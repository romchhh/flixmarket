"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChevronLeft, ChevronDown, ChevronUp, User, CreditCard, Receipt, XCircle, Users, Copy, ExternalLink, Share2 } from "lucide-react";
import type { UserProfile as UserProfileType } from "@/types/user";
import { stripHtml } from "@/lib/text";
import { ShareModal } from "@/components/ShareModal";
import { productPhotoToUrl } from "@/lib/media";
import { formatTimeLeft, formatSubscriptionDate, formatPaymentDate, getTimeLeft } from "@/lib/subscription-timer";

function getInitData(): string {
  if (typeof window === "undefined") return "";
  const init = (window as unknown as { Telegram?: { WebApp?: { initData?: string } } }).Telegram?.WebApp?.initData;
  return typeof init === "string" ? init : "";
}

type ErrorCode = "open_telegram" | "open_in_telegram" | "user_not_found" | null;

const PAYMENTS_INITIAL = 10;
const TOUCH_DEBOUNCE_MS = 400;
const MONTH_NAMES: Record<number, string> = {
  1: "Січень", 2: "Лютий", 3: "Березень", 4: "Квітень", 5: "Травень", 6: "Червень",
  7: "Липень", 8: "Серпень", 9: "Вересень", 10: "Жовтень", 11: "Листопад", 12: "Грудень",
};

function getMonthKey(dateStr: string): string {
  const d = new Date(dateStr);
  const y = d.getFullYear();
  const m = d.getMonth() + 1;
  return `${y}-${String(m).padStart(2, "0")}`;
}

function getMonthLabel(dateStr: string): string {
  const d = new Date(dateStr);
  const m = d.getMonth() + 1;
  const y = d.getFullYear();
  return `${MONTH_NAMES[m] ?? ""} ${y}`;
}

export default function ProfilePage() {
  const router = useRouter();
  const [profile, setProfile] = useState<UserProfileType | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorCode, setErrorCode] = useState<ErrorCode>(null);
  const [showPayments, setShowPayments] = useState(false);
  const [showAllPayments, setShowAllPayments] = useState(false);
  const [cancelLoadingId, setCancelLoadingId] = useState<number | null>(null);
  const [expandedSubId, setExpandedSubId] = useState<number | null>(null);
  const [referralExpanded, setReferralExpanded] = useState(false);
  const [shareModalOpen, setShareModalOpen] = useState(false);
  const [tick, setTick] = useState(0);
  const lastTouchTime = useRef(0);

  const botLink = typeof process.env.NEXT_PUBLIC_BOT_LINK === "string" && process.env.NEXT_PUBLIC_BOT_LINK
    ? process.env.NEXT_PUBLIC_BOT_LINK
    : null;
  const botUsername = typeof process.env.NEXT_PUBLIC_BOT_USERNAME === "string" && process.env.NEXT_PUBLIC_BOT_USERNAME
    ? process.env.NEXT_PUBLIC_BOT_USERNAME.trim().replace(/^@/, "")
    : "";
  const botLinkFromUsername = botUsername ? `https://t.me/${botUsername}` : null;
  const resolvedBotLink = botLink || botLinkFromUsername;

  const fetchProfile = useCallback((silent = false) => {
    const initData = getInitData();
    if (!initData) {
      setErrorCode("open_telegram");
      setLoading(false);
      return;
    }
    if (!silent) {
      setLoading(true);
      setErrorCode(null);
    }
    fetch("/api/user", { headers: { "x-telegram-init-data": initData } })
      .then(async (res) => {
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          const code = (data?.code as ErrorCode) ?? (res.status === 401 ? "open_in_telegram" : res.status === 404 ? "user_not_found" : null);
          setErrorCode(code);
          return;
        }
        setProfile(data);
      })
      .catch(() => setErrorCode("open_in_telegram"))
      .finally(() => { if (!silent) setLoading(false); });
  }, []);

  useEffect(() => {
    document.title = "Мій профіль — Flix Market";
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
    const hasActiveSimple = subs.some((s) => s.status === "active");
    const hasActiveRecurring = rec.some((r) => r.status === "active");
    if (!hasActiveSimple && !hasActiveRecurring) return;
    const id = setInterval(() => setTick((n) => n + 1), 1000);
    return () => clearInterval(id);
  }, [profile?.subscriptions, profile?.recurringSubscriptions]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center p-6 bg-gray-50">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-500 text-sm">Завантаження профілю…</p>
        </div>
      </div>
    );
  }

  if (errorCode === "open_telegram" || errorCode === "open_in_telegram") {
    return (
      <div className="min-h-screen bg-transparent p-6 flex flex-col items-center justify-center text-center">
        <User className="w-16 h-16 text-violet-400 mb-4" />
        <h1 className="text-xl font-bold text-gray-900 mb-2">Мій профіль</h1>
        <p className="text-gray-600 mb-6 max-w-sm">
          {errorCode === "open_telegram"
            ? "Відкрийте додаток з меню бота в Telegram, щоб переглядати профіль та підписки."
            : "Не вдалося перевірити вхід. Відкрийте додаток знову з меню бота в Telegram."}
        </p>
        {resolvedBotLink ? (
          <a
            href={resolvedBotLink}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center rounded-xl bg-violet-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-violet-700 mb-3"
          >
            Відкрити в Telegram
          </a>
        ) : null}
        <button type="button" onClick={() => router.back()} className="inline-flex items-center justify-center w-10 h-10 rounded-full hover:bg-gray-100 text-violet-600" aria-label="Назад">
          <ChevronLeft className="w-5 h-5" />
        </button>
      </div>
    );
  }

  if (errorCode === "user_not_found" || !profile) {
    return (
      <div className="min-h-screen bg-transparent p-6 flex flex-col items-center justify-center text-center">
        <User className="w-16 h-16 text-violet-400 mb-4" />
        <h1 className="text-xl font-bold text-gray-900 mb-2">Мій профіль</h1>
        <p className="text-gray-600 mb-6 max-w-sm">
          Профіль з'явиться після першого замовлення в Telegram-боті. Каталог доступний без входу.
        </p>
        {resolvedBotLink ? (
          <a
            href={resolvedBotLink}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center rounded-xl bg-violet-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-violet-700 mb-3"
          >
            Відкрити в Telegram
          </a>
        ) : null}
        <Link href="/catalog" className="inline-flex items-center gap-1 text-violet-600 font-medium hover:underline">
          До каталогу
        </Link>
      </div>
    );
  }

  const subs = profile.subscriptions ?? [];
  const recurringSubs = profile.recurringSubscriptions ?? [];
  const activeSubs = subs.filter((s) => s.status === "active" && !getTimeLeft(s.end_date).ended);
  const endedSubs = subs.filter((s) => s.status !== "active" || getTimeLeft(s.end_date).ended);
  const activeRecurring = recurringSubs.filter((r) => r.status === "active");
  const endedRecurring = recurringSubs.filter((r) => r.status !== "active");
  const hasAnySubs = subs.length > 0 || recurringSubs.length > 0;
  const payments = profile.payments ?? [];
  const subPayments = profile.subscriptionPayments ?? [];
  const allPayments = [
    ...payments.map((p) => ({ type: "one_time" as const, ...p, date: p.created_at })),
    ...subPayments.map((p) => ({ type: "recurring" as const, ...p, date: p.payment_date })),
  ]
    .filter((p) => (p as { status?: string }).status !== "pending")
    .sort((a, b) => (b.date || "").localeCompare(a.date || ""));

  const displayedPayments = showAllPayments ? allPayments : allPayments.slice(0, PAYMENTS_INITIAL);
  const paymentsByMonthDisplayed = (() => {
    const map = new Map<string, typeof allPayments>();
    for (const p of displayedPayments) {
      const key = getMonthKey(p.date ?? "");
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(p);
    }
    return Array.from(map.entries()).sort((a, b) => b[0].localeCompare(a[0]));
  })();
  const hasMorePayments = allPayments.length > PAYMENTS_INITIAL && !showAllPayments;

  return (
    <div className="min-h-screen bg-transparent pb-28" style={{ touchAction: "pan-y" }}>
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
          <User className="w-5 h-5 shrink-0 text-violet-600" aria-hidden />
          <h1 className="text-lg font-bold text-gray-900">Мій профіль</h1>
        </div>
        <div className="w-10 shrink-0" aria-hidden />
      </div>

      <div className="p-4 space-y-6">
        {/* Картка профілю */}
        <div className="bg-gradient-to-br from-violet-500 to-indigo-600 rounded-3xl p-6 text-white shadow-lg">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-white/20 flex items-center justify-center text-3xl">
              <User className="w-8 h-8" />
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-xl font-bold truncate">
                {[
                  profile.firstName,
                  profile.lastName,
                ]
                  .filter(Boolean)
                  .join(" ")
                  .trim() || stripHtml(profile.user_name ?? "Користувач")}
              </h2>
              <p className="text-white/80 text-sm">ID: {profile.user_id}</p>
              {profile.daysOnService != null && profile.daysOnService >= 0 && (
                <p className="text-white/70 text-xs mt-1">
                  На сервісі {profile.daysOnService} {profile.daysOnService === 1 ? "день" : profile.daysOnService < 5 ? "дні" : "днів"}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Партнерська (реферальна) програма — згортання, кнопка «Взяти участь» */}
        {profile.referral && (
          <section className="rounded-3xl border-2 border-violet-100 bg-gradient-to-br from-violet-50 to-fuchsia-50 p-5 shadow-sm">
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <button
                type="button"
                onClick={() => setReferralExpanded((e) => !e)}
                className="flex items-center gap-2 text-left min-w-0 flex-1"
              >
                <Users className="w-5 h-5 text-violet-500 shrink-0" />
                <h3 className="text-base font-bold text-gray-900">Партнерська програма</h3>
                {referralExpanded ? <ChevronUp className="w-5 h-5 text-gray-500 shrink-0" /> : <ChevronDown className="w-5 h-5 text-gray-500 shrink-0" />}
              </button>
              <button
                type="button"
                onClick={() => setShareModalOpen(true)}
                className="inline-flex items-center gap-1.5 rounded-xl bg-violet-600 px-3 py-2 text-sm font-medium text-white hover:bg-violet-700 shrink-0"
              >
                <Share2 className="w-4 h-4" />
                Взяти участь
              </button>
            </div>

            {referralExpanded && (
              <>
                <div className="grid grid-cols-2 gap-3 mt-4 mb-4">
                  <div className="rounded-xl bg-white/80 p-3 border border-violet-100">
                    <p className="text-xs font-medium text-gray-500">Баланс</p>
                    <p className="text-lg font-bold text-violet-700">{profile.referral.partnerBalance.toFixed(2)} ₴</p>
                  </div>
                  <div className="rounded-xl bg-white/80 p-3 border border-violet-100">
                    <p className="text-xs font-medium text-gray-500">Запрошено</p>
                    <p className="text-lg font-bold text-gray-900">{profile.referral.referralCount}</p>
                  </div>
                </div>
                <p className="text-xs text-gray-600 mb-3">
                  Відсоток з покупок рефералів: <strong>{Math.round(profile.referral.referralPercent)}%</strong>. Діліться посиланням — отримуйте % на баланс. Вивід та оплата підписок з балансу — в боті.
                </p>
                <div className="rounded-xl bg-white border border-violet-100 p-3 mb-3">
                  <p className="text-xs font-medium text-gray-500 mb-2">Ваше партнерське посилання</p>
                  {resolvedBotLink ? (
                    <>
                      <code className="block w-full text-xs bg-gray-100 px-2 py-2 rounded break-all mb-3">
                        {`${resolvedBotLink}${resolvedBotLink.includes("?") ? "&" : "?"}start=${profile.user_id}`}
                      </code>
                      <div className="flex items-center gap-2 flex-wrap">
                        <button
                          type="button"
                          onClick={() => {
                            const link = `${resolvedBotLink}${resolvedBotLink.includes("?") ? "&" : "?"}start=${profile.user_id}`;
                            if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
                              navigator.clipboard.writeText(link);
                            }
                          }}
                          className="inline-flex items-center gap-1.5 rounded-lg bg-violet-600 px-3 py-2 text-xs font-medium text-white hover:bg-violet-700"
                        >
                          <Copy className="w-3.5 h-3.5" />
                          Копіювати
                        </button>
                        <a
                          href={`${resolvedBotLink}${resolvedBotLink.includes("?") ? "&" : "?"}start=${profile.user_id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 rounded-lg border-2 border-violet-600 bg-transparent px-3 py-2 text-xs font-medium text-violet-600 hover:bg-violet-50"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                          Відкрити в боті
                        </a>
                      </div>
                    </>
                  ) : (
                    <p className="text-xs text-gray-500">Посилання на бота налаштовується в додатку.</p>
                  )}
                </div>
                {profile.referral.referrals.length > 0 && (
                  <div className="mb-4">
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Ваші реферали</p>
                    <ul className="space-y-1.5 rounded-xl bg-white/80 border border-violet-100 p-3 max-h-40 overflow-y-auto">
                      {profile.referral.referrals.map((r) => (
                        <li key={r.user_id} className="flex justify-between items-center text-sm">
                          <span className="font-medium text-gray-900 truncate">{r.user_name ? `@${r.user_name}` : `ID ${r.user_id}`}</span>
                          <span className="text-xs text-gray-500 shrink-0 ml-2">
                            {r.join_date ? new Date(r.join_date).toLocaleDateString("uk-UA", { day: "2-digit", month: "short", year: "numeric" }) : "—"}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {profile.referral.earningsHistory.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Історія нарахувань</p>
                    <ul className="space-y-1.5 rounded-xl bg-white/80 border border-violet-100 p-3 max-h-44 overflow-y-auto">
                      {profile.referral.earningsHistory.map((e, i) => (
                        <li key={i} className="flex justify-between items-center text-sm">
                          <span className="text-gray-700 truncate">
                            +{e.credit_amount.toFixed(1)} ₴ {e.product_name ? `(${stripHtml(e.product_name).slice(0, 20)}…)` : ""}
                          </span>
                          <span className="text-xs text-gray-500 shrink-0 ml-2">
                            {e.created_at ? new Date(e.created_at).toLocaleDateString("uk-UA", { day: "2-digit", month: "short", year: "numeric" }) : "—"}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            )}
          </section>
        )}

        <ShareModal
          isOpen={shareModalOpen}
          onClose={() => setShareModalOpen(false)}
          shareLink={resolvedBotLink && profile ? `${resolvedBotLink}${resolvedBotLink.includes("?") ? "&" : "?"}start=${profile.user_id}` : resolvedBotLink ?? ""}
          shareText="Flix Market — діліться посиланням і отримуйте % з покупок рефералів"
          tg={typeof window !== "undefined" ? (window as unknown as { Telegram?: { WebApp?: import("@/types/telegram").TelegramWebApp } }).Telegram?.WebApp ?? null : null}
        />

        {/* Підписки: одноразові + повторювані (як у боті) */}
        {hasAnySubs && (
          <section>
            <h3 className="text-base font-bold text-gray-900 mb-3 flex items-center gap-2">
              <CreditCard className="w-5 h-5 text-violet-500" />
              Мої підписки
            </h3>
            {activeSubs.length > 0 && (
              <div className="space-y-3 mb-4">
                {activeSubs.map((s) => {
                  const isActive = s.status === "active";
                  const timeLeft = getTimeLeft(s.end_date);
                  const photoUrl = productPhotoToUrl(s.product_photo ?? null);
                  const isExpanded = expandedSubId === s.id;
                  const relatedPayments = payments.filter((p) => p.product_id === s.product_id && p.status !== "pending");
                  const relatedSubPayments = subPayments.filter((sp) => sp.subscription_id === s.id && sp.status !== "pending");
                  const hasPayments = relatedPayments.length > 0 || relatedSubPayments.length > 0;
                  return (
                    <div
                      key={s.id}
                      className={`rounded-2xl border-2 overflow-hidden shadow-sm transition-all border-violet-200 bg-white ring-2 ring-violet-100 ring-offset-2`}
                    >
                      <button
                        type="button"
                        onClick={() => {
                          if (Date.now() - lastTouchTime.current < TOUCH_DEBOUNCE_MS) return;
                          setExpandedSubId(isExpanded ? null : s.id);
                        }}
                        onPointerUp={(e) => {
                          if (e.pointerType === "touch") {
                            lastTouchTime.current = Date.now();
                            setExpandedSubId((prev) => (prev === s.id ? null : s.id));
                          }
                        }}
                        className="w-full text-left touch-manipulation cursor-pointer select-none"
                      >
                        <div className="flex gap-4 p-4 pointer-events-none">
                          <div className="w-20 h-20 rounded-xl bg-gray-100 shrink-0 overflow-hidden flex items-center justify-center">
                            {photoUrl ? (
                              <img src={photoUrl} alt="" className="w-full h-full object-cover" />
                            ) : (
                              <span className="text-3xl">📦</span>
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="font-semibold text-gray-900 truncate">
                              {stripHtml(s.product_name ?? "") || `Товар #${s.product_id}`}
                            </p>
                            <p className="text-sm text-gray-500 mt-0.5">Діє до {formatSubscriptionDate(s.end_date)}</p>
                            <div className="mt-2">
                              {isActive && !timeLeft.ended ? (
                                <p className="text-xs font-mono font-semibold text-violet-600 bg-violet-50 px-2 py-1 rounded-lg inline-block">
                                  ⏱ {timeLeft.days} дн. {String(timeLeft.hours).padStart(2, "0")}:{String(timeLeft.minutes).padStart(2, "0")}:{String(timeLeft.seconds).padStart(2, "0")}
                                </p>
                              ) : (
                                <p className="text-xs text-gray-500">{formatTimeLeft(s.end_date)}</p>
                              )}
                            </div>
                            <span className="inline-block mt-2 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700">
                              Активна
                            </span>
                            <p className="mt-2 text-xs text-violet-600">
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
            )}
            {activeRecurring.length > 0 && (
              <div className="space-y-3 mb-4">
                {activeRecurring.map((r) => {
                  const monthsWord = r.months === 1 ? "місяць" : r.months >= 2 && r.months <= 4 ? "місяці" : "місяців";
                  const nextDate = r.next_payment_date ? (r.next_payment_date.includes(" ") ? r.next_payment_date.slice(0, 10) : r.next_payment_date) : null;
                  const recPhotoUrl = r.product_photo ?? null;
                  return (
                    <div key={r.id} className="rounded-2xl border-2 border-violet-200 bg-white overflow-hidden shadow-sm">
                      <div className="flex gap-4 p-4">
                        <div className="w-20 h-20 rounded-xl bg-violet-50 shrink-0 overflow-hidden flex items-center justify-center">
                          {recPhotoUrl ? (
                            <img src={recPhotoUrl} alt="" className="w-full h-full object-cover" />
                          ) : (
                            <span className="text-3xl">🔄</span>
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold text-gray-900 truncate">
                            {stripHtml(r.product_name ?? "") || "Підписка"}
                          </p>
                          <p className="text-sm text-gray-500 mt-0.5">
                            {r.price} ₴ кожні {r.months} {monthsWord}
                          </p>
                          {nextDate && (
                            <p className="text-xs text-violet-600 mt-1">
                              Наступний платіж: {formatSubscriptionDate(nextDate)}
                            </p>
                          )}
                          {r.payment_failures > 0 && (
                            <p className="text-xs text-amber-600 mt-1">Невдалих спроб: {r.payment_failures}</p>
                          )}
                          <span className="inline-block mt-2 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700">
                            Активна
                          </span>
                        </div>
                      </div>
                      <div className="border-t border-gray-100 px-4 py-3 bg-white">
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
              </div>
            )}
            {endedRecurring.length > 0 && (
              <div className="space-y-3 mb-4">
                {endedRecurring.map((r) => {
                  const monthsWord = r.months === 1 ? "місяць" : r.months >= 2 && r.months <= 4 ? "місяці" : "місяців";
                  const recPhotoUrl = r.product_photo ?? null;
                  return (
                    <div key={r.id} className="rounded-2xl border-2 border-gray-100 bg-gray-50 overflow-hidden shadow-sm opacity-90">
                      <div className="flex gap-4 p-4">
                        <div className="w-20 h-20 rounded-xl bg-gray-100 shrink-0 overflow-hidden flex items-center justify-center">
                          {recPhotoUrl ? (
                            <img src={recPhotoUrl} alt="" className="w-full h-full object-cover" />
                          ) : (
                            <span className="text-3xl">🔄</span>
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold text-gray-900 truncate">
                            {stripHtml(r.product_name ?? "") || "Підписка"}
                          </p>
                          <p className="text-sm text-gray-500 mt-0.5">
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
              </div>
            )}
            {endedSubs.length > 0 && (
              <div className="space-y-3">
                <p className="text-sm font-semibold text-gray-500 mb-1">Закінчені (одноразові)</p>
                {endedSubs.map((s) => {
                  const photoUrl = productPhotoToUrl(s.product_photo ?? null);
                  const isExpanded = expandedSubId === s.id;
                  const relatedPayments = payments.filter((p) => p.product_id === s.product_id && p.status !== "pending");
                  const relatedSubPayments = subPayments.filter((sp) => sp.subscription_id === s.id && sp.status !== "pending");
                  const hasPayments = relatedPayments.length > 0 || relatedSubPayments.length > 0;
                  return (
                    <div
                      key={s.id}
                      className="rounded-2xl border-2 border-gray-100 bg-gray-50 overflow-hidden shadow-sm opacity-90"
                    >
                      <button
                        type="button"
                        onClick={() => {
                          if (Date.now() - lastTouchTime.current < TOUCH_DEBOUNCE_MS) return;
                          setExpandedSubId(isExpanded ? null : s.id);
                        }}
                        onPointerUp={(e) => {
                          if (e.pointerType === "touch") {
                            lastTouchTime.current = Date.now();
                            setExpandedSubId((prev) => (prev === s.id ? null : s.id));
                          }
                        }}
                        className="w-full text-left touch-manipulation cursor-pointer select-none"
                      >
                        <div className="flex gap-4 p-4 pointer-events-none">
                          <div className="w-20 h-20 rounded-xl bg-gray-100 shrink-0 overflow-hidden flex items-center justify-center">
                            {photoUrl ? (
                              <img src={photoUrl} alt="" className="w-full h-full object-cover" />
                            ) : (
                              <span className="text-3xl">📦</span>
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="font-semibold text-gray-900 truncate">
                              {stripHtml(s.product_name ?? "") || `Товар #${s.product_id}`}
                            </p>
                            <p className="text-sm text-gray-500 mt-0.5">Діє до {formatSubscriptionDate(s.end_date)}</p>
                            <p className="text-xs text-gray-500 mt-1">{formatTimeLeft(s.end_date)}</p>
                            <span className="inline-block mt-2 px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-200 text-gray-600">
                              {s.status === "cancelled" ? "Скасовано" : "Закінчилась"}
                            </span>
                            <p className="mt-2 text-xs text-violet-600">
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
            )}
          </section>
        )}

        {/* Історія платежів */}
        <section>
          <button
            type="button"
            onClick={() => setShowPayments((v) => !v)}
            className="w-full flex items-center justify-between text-left mb-3"
          >
            <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
              <Receipt className="w-5 h-5 text-violet-500" />
              Історія платежів
            </h3>
            <span className="text-sm text-violet-600">
              {showPayments ? "Згорнути" : `${allPayments.length} записів`}
            </span>
          </button>
          {showPayments && (
            <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
              {allPayments.length === 0 ? (
                <p className="p-4 text-center text-gray-500 text-sm">Платежів поки немає</p>
              ) : (
                <>
                  {paymentsByMonthDisplayed.map(([monthKey, monthPayments]) => {
                    const firstDate = monthPayments[0]?.date ?? "";
                    return (
                      <div key={monthKey} className="border-b border-gray-100 last:border-b-0">
                        <p className="px-4 py-2 text-xs font-semibold text-gray-500 bg-gray-50">
                          {getMonthLabel(firstDate)}
                        </p>
                        {monthPayments.map((p, i) => (
                          <div
                            key={p.type === "one_time" ? (p as { invoice_id?: string }).invoice_id ?? i : `sub-${(p as { id: number }).id}`}
                            className="p-4 flex items-center gap-3 border-t border-gray-50"
                          >
                            <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center text-lg">
                              {(p as { product_photo?: string }).product_photo ? "🖼" : "💳"}
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="font-medium text-gray-900 truncate">
                                {p.type === "one_time"
                                  ? stripHtml((p as { product_name?: string }).product_name ?? "") || "Оплата"
                                  : stripHtml((p as { product_name?: string }).product_name ?? "") || "Помісячний платіж"}
                              </p>
                              <p className="text-sm text-gray-500">
                                {(p as { amount: number }).amount} ₴ · {formatPaymentDate((p as { date?: string }).date)}
                              </p>
                            </div>
                            <span
                              className={`text-xs font-medium px-2 py-1 rounded-full ${
                                (p as { status?: string }).status === "success"
                                  ? "bg-emerald-50 text-emerald-700"
                                  : "bg-gray-100 text-gray-600"
                              }`}
                            >
                              {(p as { status?: string }).status === "success" ? "Оплачено" : (p as { status?: string }).status ?? "—"}
                            </span>
                          </div>
                        ))}
                      </div>
                    );
                  })}
                  {hasMorePayments && (
                    <div className="p-3 border-t border-gray-100">
                      <button
                        type="button"
                        onClick={() => setShowAllPayments(true)}
                        className="w-full text-center text-sm font-medium text-violet-600 hover:underline"
                      >
                        Показати всі
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </section>

        <div className="flex flex-col sm:flex-row gap-3 justify-center items-center pt-2">
          <Link href="/subscriptions" className="text-violet-600 font-medium text-sm hover:underline">
            Мої підписки
          </Link>
          <Link href="/catalog" className="text-violet-600 font-medium text-sm hover:underline">
            Перейти до каталогу
          </Link>
        </div>
      </div>
    </div>
  );
}
