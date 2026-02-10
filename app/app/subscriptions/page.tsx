"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChevronLeft, CreditCard, Receipt, XCircle } from "lucide-react";
import type { UserProfile } from "@/types/user";
import { stripHtml } from "@/lib/text";
import { productPhotoToUrl } from "@/lib/media";
import { formatTimeLeft, formatSubscriptionDate, formatPaymentDate, getTimeLeft } from "@/lib/subscription-timer";

const TOUCH_DEBOUNCE_MS = 400;

function getInitData(): string {
  if (typeof window === "undefined") return "";
  const init = (window as unknown as { Telegram?: { WebApp?: { initData?: string } } }).Telegram?.WebApp?.initData;
  return typeof init === "string" ? init : "";
}

export default function SubscriptionsPage() {
  const router = useRouter();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [cancelLoadingId, setCancelLoadingId] = useState<number | null>(null);
  const [tick, setTick] = useState(0);
  const lastTouchTime = useRef(0);

  const botLink = typeof process.env.NEXT_PUBLIC_BOT_LINK === "string" && process.env.NEXT_PUBLIC_BOT_LINK
    ? process.env.NEXT_PUBLIC_BOT_LINK
    : null;

  const fetchProfile = useCallback((silent = false) => {
    const initData = getInitData();
    if (!initData) {
      setError("open_telegram");
      setLoading(false);
      return;
    }
    if (!silent) {
      setLoading(true);
      setError(null);
    }
    fetch("/api/user", { headers: { "x-telegram-init-data": initData } })
      .then(async (res) => {
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          setError(data?.code ?? (res.status === 401 ? "open_in_telegram" : res.status === 404 ? "user_not_found" : "load_failed"));
          return;
        }
        setProfile(data);
      })
      .catch(() => setError("load_failed"))
      .finally(() => { if (!silent) setLoading(false); });
  }, []);

  useEffect(() => {
    document.title = "Мої підписки — Flix Market";
  }, []);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  const handleCancelSubscription = useCallback(async (subscriptionId: number) => {
    if (!window.confirm("Скасувати цю підписку? Вона перестане бути активною.")) return;
    const initData = getInitData();
    if (!initData) return;
    setCancelLoadingId(subscriptionId);
    try {
      const res = await fetch(`/api/user/subscriptions/${subscriptionId}/cancel`, {
        method: "POST",
        headers: { "x-telegram-init-data": initData },
      });
      if (res.ok) {
        await fetchProfile(true);
      }
    } finally {
      setCancelLoadingId(null);
    }
  }, [fetchProfile]);

  useEffect(() => {
    const subs = profile?.subscriptions ?? [];
    const rec = profile?.recurringSubscriptions ?? [];
    if (subs.length === 0 && rec.length === 0) return;
    const hasActive = subs.some((s) => s.status === "active") || rec.some((r) => r.status === "active");
    if (!hasActive) return;
    const id = setInterval(() => setTick((n) => n + 1), 1000);
    return () => clearInterval(id);
  }, [profile?.subscriptions, profile?.recurringSubscriptions]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center p-6 bg-gray-50">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-500 text-sm">Завантаження підписок…</p>
        </div>
      </div>
    );
  }

  if (error === "open_telegram" || error === "open_in_telegram") {
    return (
      <div className="min-h-screen bg-transparent p-6 flex flex-col items-center justify-center text-center">
        <CreditCard className="w-16 h-16 text-violet-400 mb-4" />
        <h1 className="text-xl font-bold text-gray-900 mb-2">Мої підписки</h1>
        <p className="text-gray-600 mb-6 max-w-sm">
          {error === "open_telegram"
            ? "Відкрийте додаток з меню бота в Telegram, щоб переглядати підписки."
            : "Не вдалося перевірити вхід. Відкрийте додаток знову з меню бота в Telegram."}
        </p>
        {botLink ? (
          <a href={botLink} target="_blank" rel="noopener noreferrer" className="inline-flex items-center justify-center rounded-xl bg-violet-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-violet-700 mb-3">
            Відкрити в Telegram
          </a>
        ) : null}
        <button type="button" onClick={() => router.back()} className="inline-flex items-center justify-center w-10 h-10 rounded-full hover:bg-gray-100 text-violet-600" aria-label="Назад">
          <ChevronLeft className="w-5 h-5" />
        </button>
      </div>
    );
  }

  if (error === "user_not_found" || (error && !profile)) {
    return (
      <div className="min-h-screen bg-transparent p-6 flex flex-col items-center justify-center text-center">
        <CreditCard className="w-16 h-16 text-violet-400 mb-4" />
        <h1 className="text-xl font-bold text-gray-900 mb-2">Мої підписки</h1>
        <p className="text-gray-600 mb-6 max-w-sm">
          {error === "user_not_found"
            ? "Підписки з'являться після першого замовлення в Telegram-боті. Каталог доступний без входу."
            : "Не вдалося завантажити підписки."}
        </p>
        {botLink ? (
          <a href={botLink} target="_blank" rel="noopener noreferrer" className="inline-flex items-center justify-center rounded-xl bg-violet-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-violet-700 mb-3">
            Відкрити в Telegram
          </a>
        ) : null}
        <Link href="/catalog" className="inline-flex items-center gap-1 text-violet-600 font-medium hover:underline">
          До каталогу
        </Link>
      </div>
    );
  }

  if (!profile) return null;

  const subs = profile.subscriptions ?? [];
  const recurringSubs = profile.recurringSubscriptions ?? [];
  const activeSubs = subs.filter((s) => s.status === "active" && !getTimeLeft(s.end_date).ended);
  const endedSubs = subs.filter((s) => s.status !== "active" || getTimeLeft(s.end_date).ended);
  const activeRecurring = recurringSubs.filter((r) => r.status === "active");
  const endedRecurring = recurringSubs.filter((r) => r.status !== "active");
  const hasAnySubs = subs.length > 0 || recurringSubs.length > 0;
  const payments = profile.payments ?? [];
  const subPayments = profile.subscriptionPayments ?? [];

  return (
    <div className="min-h-screen bg-transparent pb-24" style={{ touchAction: "pan-y" }}>
      <div className="sticky top-0 bg-transparent z-10 px-4 py-3 flex items-center justify-between">
        <button
          type="button"
          onClick={() => router.back()}
          className="p-2 -ml-2 rounded-full hover:bg-gray-100 flex items-center justify-center text-gray-600 shrink-0 w-10 h-10"
          aria-label="Назад"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
        <div className="absolute left-1/2 -translate-x-1/2 flex items-center justify-center gap-2">
          <CreditCard className="w-5 h-5 shrink-0 text-violet-600" aria-hidden />
          <h1 className="text-lg font-bold text-gray-900">Мої підписки</h1>
        </div>
        <div className="w-10 shrink-0" aria-hidden />
      </div>

      <div className="p-4 space-y-6">
        {!hasAnySubs ? (
          <div className="text-center py-12 bg-white rounded-3xl border border-gray-100 px-6">
            <CreditCard className="w-14 h-14 mx-auto text-gray-300 mb-3" />
            <p className="text-gray-600 font-medium">У вас поки немає підписок</p>
            <p className="text-gray-500 text-sm mt-1">
              Оформте підписку в каталозі — оплата прямо в Telegram
            </p>
            <Link
              href="/catalog"
              className="inline-flex items-center justify-center mt-4 px-5 py-2.5 border-2 border-violet-600 bg-transparent text-violet-600 rounded-xl text-sm font-medium hover:bg-violet-50"
            >
              Перейти в каталог
            </Link>
            {botLink && (
              <p className="mt-4">
                <a href={botLink} target="_blank" rel="noopener noreferrer" className="text-sm text-violet-600 hover:underline">
                  Як продовжити підписку
                </a>
              </p>
            )}
          </div>
        ) : (
          <div className="space-y-6">
            {(activeSubs.length > 0 || activeRecurring.length > 0) && (
              <section>
                <h2 className="text-sm font-semibold text-gray-500 mb-3">Активні</h2>
                <div className="space-y-4">
                  {activeRecurring.map((r) => {
                    const monthsWord = r.months === 1 ? "місяць" : r.months >= 2 && r.months <= 4 ? "місяці" : "місяців";
                    const nextDate = r.next_payment_date ? (r.next_payment_date.includes(" ") ? r.next_payment_date.slice(0, 10) : r.next_payment_date) : null;
                    const recPhotoUrl = r.product_photo ?? null;
                    const nextTimeLeft = nextDate ? getTimeLeft(nextDate) : null;
                    return (
                      <div key={`rec-${r.id}`} className="rounded-2xl border-2 border-violet-200 overflow-hidden shadow-sm bg-white">
                        <div className="flex gap-4 p-4">
                          <div className="w-24 h-24 rounded-xl bg-violet-50 shrink-0 overflow-hidden flex items-center justify-center">
                            {recPhotoUrl ? (
                              <img src={recPhotoUrl} alt="" className="w-full h-full object-cover" />
                            ) : (
                              <span className="text-4xl">🔄</span>
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="font-semibold text-gray-900 leading-tight">
                              {stripHtml(r.product_name ?? "") || "Підписка"}
                            </p>
                            <p className="text-sm text-gray-500 mt-1">
                              {r.price} ₴ кожні {r.months} {monthsWord} · автосписання
                            </p>
                            {nextDate && (
                              <p className="text-sm text-violet-600 mt-1">
                                Наступний платіж: {formatSubscriptionDate(nextDate)}
                              </p>
                            )}
                            {r.payment_failures > 0 && (
                              <p className="text-xs text-amber-600 mt-1">Невдалих спроб оплати: {r.payment_failures}</p>
                            )}
                            <span className="inline-block mt-2 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700">
                              Активна
                            </span>
                          </div>
                        </div>
                        <div className="border-t border-gray-100 px-4 py-3 bg-gray-50/50 space-y-3">
                          {nextDate && nextTimeLeft && !nextTimeLeft.ended && (
                            <p key={`rec-timer-${r.id}-${tick}`} className="text-xs font-mono font-semibold text-violet-600">
                              До наступного платежу: {nextTimeLeft.days} дн. {String(nextTimeLeft.hours).padStart(2, "0")}:{String(nextTimeLeft.minutes).padStart(2, "0")}:{String(nextTimeLeft.seconds).padStart(2, "0")}
                            </p>
                          )}
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              e.preventDefault();
                              if (Date.now() - lastTouchTime.current < TOUCH_DEBOUNCE_MS) return;
                              handleCancelSubscription(r.id);
                            }}
                            onPointerDown={(e) => {
                              if (e.pointerType === "touch") {
                                e.stopPropagation();
                                e.preventDefault();
                                if (cancelLoadingId === r.id) return;
                                lastTouchTime.current = Date.now();
                                handleCancelSubscription(r.id);
                              }
                            }}
                            disabled={cancelLoadingId === r.id}
                            className="w-full flex items-center justify-center gap-2 py-3 text-sm font-medium text-rose-600 hover:bg-rose-50 active:bg-rose-100 rounded-xl transition-colors disabled:opacity-50 touch-manipulation cursor-pointer min-h-[44px] bg-white border border-rose-200"
                          >
                            {cancelLoadingId === r.id ? (
                              <span className="animate-pulse">Скасування…</span>
                            ) : (
                              <>
                                <XCircle className="w-4 h-4" />
                                Скасувати підписку
                              </>
                            )}
                          </button>
                        </div>
                      </div>
                    );
                  })}
                  {activeSubs.map((s) => {
                    const timeLeft = getTimeLeft(s.end_date);
                    const photoUrl = productPhotoToUrl(s.product_photo ?? null);
                    const isExpanded = expandedId === s.id;
                    const relatedPayments = payments.filter((p) => p.product_id === s.product_id && p.status !== "pending");
                    const relatedSubPayments = subPayments.filter((sp) => sp.subscription_id === s.id && sp.status !== "pending");
                    const hasPayments = relatedPayments.length > 0 || relatedSubPayments.length > 0;
                    const paymentCount = relatedPayments.length + relatedSubPayments.length;
                    const lessThanDay = timeLeft.days === 0 && !timeLeft.ended;

                    return (
                      <div
                        key={s.id}
                        className={`rounded-2xl border-2 overflow-hidden shadow-sm bg-white transition-all ${
                          lessThanDay ? "border-amber-400 bg-amber-50/30" : "border-violet-200"
                        }`}
                      >
                        <button
                          type="button"
                          onClick={() => {
                            if (Date.now() - lastTouchTime.current < TOUCH_DEBOUNCE_MS) return;
                            setExpandedId(isExpanded ? null : s.id);
                          }}
                          onPointerUp={(e) => {
                            if (e.pointerType === "touch") {
                              lastTouchTime.current = Date.now();
                              setExpandedId((prev) => (prev === s.id ? null : s.id));
                            }
                          }}
                          className="w-full text-left touch-manipulation cursor-pointer select-none"
                        >
                          <div className="flex gap-4 p-4 pointer-events-none">
                            <div className="w-24 h-24 rounded-xl bg-gray-100 shrink-0 overflow-hidden flex items-center justify-center">
                              {photoUrl ? (
                                <img src={photoUrl} alt="" className="w-full h-full object-cover" />
                              ) : (
                                <span className="text-4xl">📦</span>
                              )}
                            </div>
                            <div className="flex-1 min-w-0">
                              {lessThanDay && (
                                <p className="text-xs font-semibold text-amber-700 mb-1">Закінчується сьогодні · Залишилось {timeLeft.hours} год</p>
                              )}
                              <p className="font-semibold text-gray-900 leading-tight">
                                {stripHtml(s.product_name ?? "") || `Товар #${s.product_id}`}
                              </p>
                              <p className="text-sm text-gray-500 mt-1">Діє до {formatSubscriptionDate(s.end_date)}</p>
                              {!timeLeft.ended && (
                                <p key={`timer-${s.id}-${tick}`} className="text-xs font-mono font-semibold text-violet-600 mt-2">
                                  ⏱ Залишилось: {timeLeft.days} дн. {String(timeLeft.hours).padStart(2, "0")}:{String(timeLeft.minutes).padStart(2, "0")}:{String(timeLeft.seconds).padStart(2, "0")}
                                </p>
                              )}
                              <span className="inline-block mt-2 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700">
                                Активна
                              </span>
                              <p className="mt-2 text-xs text-violet-600 flex items-center gap-1">
                                {isExpanded ? "Приховати деталі" : "Деталі підписки"}
                              </p>
                            </div>
                          </div>
                        </button>

                        {isExpanded && (
                          <>
                            <div className="border-t border-gray-100 bg-gray-50/80 px-4 py-3 space-y-3">
                              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Деталі підписки</p>
                              <dl className="grid grid-cols-1 gap-2 text-sm">
                                <div className="flex justify-between">
                                  <dt className="text-gray-500">Дата початку</dt>
                                  <dd className="font-medium text-gray-900">{formatSubscriptionDate(s.start_date)}</dd>
                                </div>
                                <div className="flex justify-between">
                                  <dt className="text-gray-500">Діє до</dt>
                                  <dd className="font-medium text-gray-900">{formatSubscriptionDate(s.end_date)}</dd>
                                </div>
                                <div className="flex justify-between items-center">
                                  <dt className="text-gray-500">Статус</dt>
                                  <dd>
                                    <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700">
                                      Активна
                                    </span>
                                  </dd>
                                </div>
                                {!timeLeft.ended && (
                                  <div className="flex justify-between items-center">
                                    <dt className="text-gray-500">Залишилось</dt>
                                    <dd className="font-mono text-violet-600 text-xs">
                                      {timeLeft.days} дн. {String(timeLeft.hours).padStart(2, "0")}:{String(timeLeft.minutes).padStart(2, "0")}:{String(timeLeft.seconds).padStart(2, "0")}
                                    </dd>
                                  </div>
                                )}
                              </dl>
                            </div>
                            {hasPayments && (
                              <div className="border-t border-gray-100 bg-gray-50/80 px-4 py-3 space-y-2">
                                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Платежі</p>
                                {relatedPayments.map((p) => (
                                  <div key={p.invoice_id ?? p.payment_id ?? ""} className="flex justify-between items-center text-sm">
                                    <span>{formatPaymentDate(p.created_at)}</span>
                                    <span className="font-medium">{p.amount} ₴</span>
                                    <span className={`text-xs px-2 py-0.5 rounded ${p.status === "success" ? "bg-emerald-50 text-emerald-700" : "bg-gray-200 text-gray-600"}`}>
                                      {p.status === "success" ? "Оплачено" : p.status ?? "—"}
                                    </span>
                                  </div>
                                ))}
                                {relatedSubPayments.map((sp) => (
                                  <div key={sp.id} className="flex justify-between items-center text-sm">
                                    <span>{formatPaymentDate(sp.payment_date)}</span>
                                    <span className="font-medium">{sp.amount} ₴</span>
                                    <span className={`text-xs px-2 py-0.5 rounded ${sp.status === "success" ? "bg-emerald-50 text-emerald-700" : "bg-gray-200 text-gray-600"}`}>
                                      {sp.status === "success" ? "Оплачено" : sp.status ?? "—"}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </>
                        )}
                        <div className="border-t border-gray-100 px-4 py-3 bg-white">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              e.preventDefault();
                              if (Date.now() - lastTouchTime.current < TOUCH_DEBOUNCE_MS) return;
                              handleCancelSubscription(s.id);
                            }}
                            onPointerDown={(e) => {
                              if (e.pointerType === "touch") {
                                e.stopPropagation();
                                e.preventDefault();
                                if (cancelLoadingId === s.id) return;
                                lastTouchTime.current = Date.now();
                                handleCancelSubscription(s.id);
                              }
                            }}
                            disabled={cancelLoadingId === s.id}
                            className="w-full flex items-center justify-center gap-2 py-3 text-sm font-medium text-rose-600 hover:bg-rose-50 active:bg-rose-100 rounded-xl transition-colors disabled:opacity-50 touch-manipulation cursor-pointer min-h-[44px] bg-white border border-rose-200"
                          >
                            {cancelLoadingId === s.id ? (
                              <span className="animate-pulse">Скасування…</span>
                            ) : (
                              <>
                                <XCircle className="w-4 h-4" />
                                Скасувати підписку
                              </>
                            )}
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>
            )}
            {(endedSubs.length > 0 || endedRecurring.length > 0) && (
              <section>
                <h2 className="text-sm font-semibold text-gray-500 mb-3">Закінчені</h2>
                <div className="space-y-4">
                  {endedRecurring.map((r) => {
                    const monthsWord = r.months === 1 ? "місяць" : r.months >= 2 && r.months <= 4 ? "місяці" : "місяців";
                    const recPhotoUrl = r.product_photo ?? null;
                    return (
                      <div key={`rec-${r.id}`} className="rounded-2xl border-2 border-gray-100 overflow-hidden shadow-sm bg-white opacity-90">
                        <div className="flex gap-4 p-4">
                          <div className="w-24 h-24 rounded-xl bg-gray-100 shrink-0 overflow-hidden flex items-center justify-center">
                            {recPhotoUrl ? (
                              <img src={recPhotoUrl} alt="" className="w-full h-full object-cover" />
                            ) : (
                              <span className="text-4xl">🔄</span>
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="font-semibold text-gray-900 leading-tight">
                              {stripHtml(r.product_name ?? "") || "Підписка"}
                            </p>
                            <p className="text-sm text-gray-500 mt-1">
                              {r.price} ₴ кожні {r.months} {monthsWord}
                            </p>
                            <span className="inline-block mt-2 px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-200 text-gray-600">
                              Скасована
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                  {endedSubs.map((s) => {
                    const photoUrl = productPhotoToUrl(s.product_photo ?? null);
                    const isExpanded = expandedId === s.id;
                    const relatedPayments = payments.filter((p) => p.product_id === s.product_id && p.status !== "pending");
                    const relatedSubPayments = subPayments.filter((sp) => sp.subscription_id === s.id && sp.status !== "pending");
                    const hasPayments = relatedPayments.length > 0 || relatedSubPayments.length > 0;
                    const paymentCount = relatedPayments.length + relatedSubPayments.length;

                    return (
                      <div key={s.id} className="rounded-2xl border-2 border-gray-100 overflow-hidden shadow-sm bg-white opacity-90">
                        <button
                          type="button"
                          onClick={() => {
                            if (Date.now() - lastTouchTime.current < TOUCH_DEBOUNCE_MS) return;
                            setExpandedId(isExpanded ? null : s.id);
                          }}
                          onPointerUp={(e) => {
                            if (e.pointerType === "touch") {
                              lastTouchTime.current = Date.now();
                              setExpandedId((prev) => (prev === s.id ? null : s.id));
                            }
                          }}
                          className="w-full text-left touch-manipulation cursor-pointer select-none"
                        >
                          <div className="flex gap-4 p-4 pointer-events-none">
                            <div className="w-24 h-24 rounded-xl bg-gray-100 shrink-0 overflow-hidden flex items-center justify-center">
                              {photoUrl ? (
                                <img src={photoUrl} alt="" className="w-full h-full object-cover" />
                              ) : (
                                <span className="text-4xl">📦</span>
                              )}
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="font-semibold text-gray-900 leading-tight">
                                {stripHtml(s.product_name ?? "") || `Товар #${s.product_id}`}
                              </p>
                              <p className="text-sm text-gray-500 mt-1">Діє до {formatSubscriptionDate(s.end_date)}</p>
                              <span className="inline-block mt-2 px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-200 text-gray-600">
                                {s.status === "cancelled" ? "Скасовано" : "Закінчилась"}
                              </span>
                              <p className="mt-2 text-xs text-violet-600 flex items-center gap-1">
                                {isExpanded ? "Приховати деталі" : "Деталі підписки"}
                              </p>
                            </div>
                          </div>
                        </button>
                        {isExpanded && (
                          <>
                            <div className="border-t border-gray-100 bg-gray-50/80 px-4 py-3 space-y-3">
                              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Деталі підписки</p>
                              <dl className="grid grid-cols-1 gap-2 text-sm">
                                <div className="flex justify-between">
                                  <dt className="text-gray-500">Дата початку</dt>
                                  <dd className="font-medium text-gray-900">{formatSubscriptionDate(s.start_date)}</dd>
                                </div>
                                <div className="flex justify-between">
                                  <dt className="text-gray-500">Діє до</dt>
                                  <dd className="font-medium text-gray-900">{formatSubscriptionDate(s.end_date)}</dd>
                                </div>
                                <div className="flex justify-between items-center">
                                  <dt className="text-gray-500">Статус</dt>
                                  <dd>
                                    <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-200 text-gray-600">
                                      {s.status === "cancelled" ? "Скасовано" : "Закінчилась"}
                                    </span>
                                  </dd>
                                </div>
                              </dl>
                            </div>
                            {hasPayments && (
                              <div className="border-t border-gray-100 bg-gray-50/80 px-4 py-3 space-y-2">
                                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Платежі</p>
                                {relatedPayments.map((p) => (
                                  <div key={p.invoice_id ?? p.payment_id ?? ""} className="flex justify-between items-center text-sm">
                                    <span>{formatPaymentDate(p.created_at)}</span>
                                    <span className="font-medium">{p.amount} ₴</span>
                                    <span className={`text-xs px-2 py-0.5 rounded ${p.status === "success" ? "bg-emerald-50 text-emerald-700" : "bg-gray-200 text-gray-600"}`}>
                                      {p.status === "success" ? "Оплачено" : p.status ?? "—"}
                                    </span>
                                  </div>
                                ))}
                                {relatedSubPayments.map((sp) => (
                                  <div key={sp.id} className="flex justify-between items-center text-sm">
                                    <span>{formatPaymentDate(sp.payment_date)}</span>
                                    <span className="font-medium">{sp.amount} ₴</span>
                                    <span className={`text-xs px-2 py-0.5 rounded ${sp.status === "success" ? "bg-emerald-50 text-emerald-700" : "bg-gray-200 text-gray-600"}`}>
                                      {sp.status === "success" ? "Оплачено" : sp.status ?? "—"}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    );
                  })}
                </div>
              </section>
            )}
          </div>
        )}

        <Link href="/profile" className="block text-center py-2 text-violet-600 font-medium text-sm">
          Мій профіль
        </Link>
      </div>
    </div>
  );
}
