"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ChevronLeft, CreditCard, Package, ThumbsUp, Share2, Heart } from "lucide-react";
import { ShareModal } from "@/components/ShareModal";
import { stripHtml, formatPriceDisplay, isSubscriptionTariffsString, getSubscriptionTariffEntries, getSubscriptionPeriodSummary } from "@/lib/text";

const TELEGRAM_ICON = (
  <svg className="w-5 h-5 shrink-0" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
    <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
  </svg>
);

type Product = {
  id: number;
  catalog_id: number;
  product_type: string;
  product_name: string;
  product_description: string | null;
  product_price: number | string;
  product_photo: string | null;
  payment_type: string;
};

const DESCRIPTION_PREVIEW_LEN = 200;

function getInitData(): string {
  if (typeof window === "undefined") return "";
  const init = (window as unknown as { Telegram?: { WebApp?: { initData?: string } } }).Telegram?.WebApp?.initData;
  return typeof init === "string" ? init : "";
}

/** Відкриває сторінку оплати в тому ж вікні (в межах міні-додатку). Після оплати Monobank перенаправить на redirectUrl (додаток або бот). */
function openPaymentUrl(url: string) {
  if (typeof window === "undefined") return;
  window.location.href = url;
}

export default function ProductPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const [product, setProduct] = useState<Product | null>(null);
  const [relatedProducts, setRelatedProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [descriptionExpanded, setDescriptionExpanded] = useState(false);
  const [paymentLoading, setPaymentLoading] = useState(false);
  const [paymentError, setPaymentError] = useState<string | null>(null);
  const [shareModalOpen, setShareModalOpen] = useState(false);
  const [shareReferralLink, setShareReferralLink] = useState("");
  const [isLiked, setIsLiked] = useState(false);

  const fetchProduct = () => {
    setLoading(true);
    setError(false);
    const numId = parseInt(id, 10);
    if (!Number.isInteger(numId) || numId < 1) {
      setError(true);
      setLoading(false);
      return;
    }
    fetch(`/api/products/${numId}`)
      .then((res) => {
        if (!res.ok) throw new Error("Not found");
        return res.json();
      })
      .then(setProduct)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    document.title = "Товар — Flix Market";
  }, []);

  useEffect(() => {
    fetchProduct();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- fetchProduct depends on id from closure
  }, [id]);

  useEffect(() => {
    if (product?.product_name) {
      document.title = `${stripHtml(product.product_name)} — Flix Market`;
    }
  }, [product]);

  useEffect(() => {
    if (!product?.id) return;
    try {
      const raw = typeof window !== "undefined" ? localStorage.getItem("flix-favorites") : null;
      const ids = raw ? (JSON.parse(raw) as number[]) : [];
      setIsLiked(Array.isArray(ids) && ids.includes(product.id));
    } catch {
      setIsLiked(false);
    }
  }, [product?.id]);

  const toggleLike = () => {
    if (!product?.id || typeof window === "undefined") return;
    try {
      const raw = localStorage.getItem("flix-favorites");
      const ids: number[] = raw ? JSON.parse(raw) : [];
      const next = Array.isArray(ids) ? [...ids] : [];
      const i = next.indexOf(product.id);
      if (i >= 0) next.splice(i, 1);
      else next.push(product.id);
      localStorage.setItem("flix-favorites", JSON.stringify(next));
      setIsLiked(next.includes(product.id));
      window.dispatchEvent(new Event("flix-favorites-changed"));
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    if (!product) return;
    fetch("/api/products")
      .then((r) => (r.ok ? r.json() : []))
      .then((list: Product[]) => {
        const other = list.filter((p) => p.id !== product.id && p.catalog_id !== product.catalog_id);
        setRelatedProducts(other.slice(0, 6));
      })
      .catch(() => setRelatedProducts([]));
  }, [product]);

  const botLink = typeof process.env.NEXT_PUBLIC_BOT_LINK === "string" && process.env.NEXT_PUBLIC_BOT_LINK
    ? process.env.NEXT_PUBLIC_BOT_LINK
    : null;
  const botUsername = typeof process.env.NEXT_PUBLIC_BOT_USERNAME === "string" && process.env.NEXT_PUBLIC_BOT_USERNAME
    ? process.env.NEXT_PUBLIC_BOT_USERNAME.trim().replace(/^@/, "")
    : "";
  const botLinkFromUsername = botUsername ? `https://t.me/${botUsername}` : null;
  const resolvedBotLink = botLink || botLinkFromUsername;

  useEffect(() => {
    if (!shareModalOpen) {
      setShareReferralLink("");
      return;
    }
    const initData = getInitData();
    const applyLink = (baseLink: string) => {
      setShareReferralLink(baseLink);
      if (!initData || !baseLink) return;
      fetch("/api/user", { headers: { "x-telegram-init-data": initData } })
        .then((r) => (r.ok ? r.json() : null))
        .then((data: { user_id?: number } | null) => {
          const uid = data?.user_id;
          if (uid != null) {
            setShareReferralLink(`${baseLink}${baseLink.includes("?") ? "&" : "?"}start=${uid}`);
          }
        })
        .catch(() => {});
    };
    if (resolvedBotLink) {
      applyLink(resolvedBotLink);
    } else {
      fetch("/api/bot-link")
        .then((r) => (r.ok ? r.json() : { botLink: "" }))
        .then((data: { botLink?: string }) => applyLink(data?.botLink || ""))
        .catch(() => setShareReferralLink(""));
    }
  }, [shareModalOpen, resolvedBotLink]);

  const handlePayWithMonobank = (months: number) => {
    const initData = getInitData();
    if (!initData) {
      setPaymentError("Відкрийте додаток з Telegram");
      return;
    }
    setPaymentError(null);
    setPaymentLoading(true);
    fetch("/api/user/payment/create", {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-telegram-init-data": initData },
      body: JSON.stringify({ productId: product!.id, months }),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.pageUrl) {
          openPaymentUrl(data.pageUrl);
        } else {
          setPaymentError(data.error || "Не вдалося створити платіж");
        }
      })
      .catch(() => setPaymentError("Помилка мережі"))
      .finally(() => setPaymentLoading(false));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-transparent pb-28">
        <div className="sticky top-0 bg-transparent z-10 px-4 py-3 flex items-center justify-center gap-2">
          <span className="text-xl" aria-hidden>📦</span>
          <div className="h-5 w-28 bg-gray-200 rounded animate-pulse" />
        </div>
        <div className="px-4 pt-4">
          <div className="bg-white rounded-3xl border border-gray-100 overflow-hidden">
            <div className="aspect-square bg-gray-200 animate-pulse" />
            <div className="p-5 space-y-3">
              <div className="h-6 w-3/4 bg-gray-200 rounded animate-pulse" />
              <div className="h-4 w-full bg-gray-100 rounded animate-pulse" />
              <div className="h-4 w-full bg-gray-100 rounded animate-pulse" />
              <div className="h-12 w-full bg-gray-100 rounded-2xl animate-pulse" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="min-h-screen bg-transparent p-6 flex flex-col items-center justify-center text-center">
        <Package className="w-16 h-16 text-gray-300 mb-4" />
        <p className="text-gray-600 font-medium">Товар не знайдено</p>
        <p className="text-sm text-gray-500 mt-1">Спробуйте оновити або повернутися назад</p>
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          <button
            type="button"
            onClick={fetchProduct}
            className="inline-flex items-center gap-2 rounded-xl bg-violet-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-violet-700"
          >
            Повторити
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            className="inline-flex items-center justify-center w-10 h-10 rounded-full hover:bg-gray-100 text-violet-600"
            aria-label="Назад"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
        </div>
      </div>
    );
  }

  const priceStr = typeof product.product_price === "string" ? product.product_price : String(product.product_price);
  const hasTariffs = isSubscriptionTariffsString(priceStr);
  const isSubscription = product.payment_type === "subscription" || product.payment_type === "recurring";
  const showTariffs = hasTariffs;
  const tariffEntries = showTariffs ? getSubscriptionTariffEntries(priceStr) : [];
  const periodSummary = getSubscriptionPeriodSummary(priceStr);

  return (
    <div className="min-h-screen bg-transparent pb-28">
      <div className="sticky top-0 bg-transparent z-10 px-4 py-3 flex items-center justify-between">
        <button
          type="button"
          onClick={() => router.back()}
          className="p-2 -ml-2 rounded-full hover:bg-gray-100 flex items-center justify-center text-gray-600 shrink-0 w-10 h-10"
          aria-label="Назад"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
        <div className="absolute left-1/2 -translate-x-1/2 flex items-center justify-center gap-2 min-w-0 max-w-[60%]">
          {product.product_photo ? (
            <img src={product.product_photo} alt="" className="h-7 w-7 rounded-lg object-cover shrink-0" />
          ) : (
            <span className="text-xl shrink-0" aria-hidden>📦</span>
          )}
          <span className="text-sm font-bold text-gray-900 truncate">{stripHtml(product.product_type)}</span>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <button
            type="button"
            onClick={toggleLike}
            className={`w-10 h-10 rounded-full hover:bg-gray-100 flex items-center justify-center ${isLiked ? "text-violet-600" : "text-gray-600"}`}
            aria-label={isLiked ? "Прибрати з обраного" : "Додати в обране"}
          >
            <Heart className="w-5 h-5" fill={isLiked ? "currentColor" : "none"} strokeWidth={2} />
          </button>
          <button
            type="button"
            onClick={() => setShareModalOpen(true)}
            className="w-10 h-10 rounded-full hover:bg-gray-100 flex items-center justify-center text-gray-600"
            aria-label="Поділитися"
          >
            <Share2 className="w-5 h-5" />
          </button>
        </div>
      </div>

      <ShareModal
        isOpen={shareModalOpen}
        onClose={() => setShareModalOpen(false)}
        shareLink={shareReferralLink}
        shareText={product ? `${stripHtml(product.product_name)} — Flix Market` : "Flix Market"}
        tg={typeof window !== "undefined" ? (window as unknown as { Telegram?: { WebApp?: import("@/types/telegram").TelegramWebApp } }).Telegram?.WebApp ?? null : null}
      />

      <div className="px-4 pt-4">
        <div className="bg-white rounded-3xl border border-gray-100 overflow-hidden shadow-sm">
          <div className="relative aspect-square bg-gray-50 flex items-center justify-center overflow-hidden">
            {product.product_photo ? (
              <img
                src={product.product_photo}
                alt=""
                className="w-full h-full object-cover"
              />
            ) : (
              <span className="text-8xl">📦</span>
            )}
            {(product as { product_badge?: string }).product_badge && (
              <span
                className={`absolute top-3 left-3 px-2.5 py-1 rounded-xl text-xs font-semibold text-white shadow-lg ${
                  (product as { product_badge?: string }).product_badge === "hot"
                    ? "bg-rose-500"
                    : (product as { product_badge?: string }).product_badge === "bestseller"
                      ? "bg-amber-500"
                      : "bg-emerald-500"
                }`}
              >
                {(product as { product_badge?: string }).product_badge === "hot"
                  ? "Гаряча пропозиція"
                  : (product as { product_badge?: string }).product_badge === "bestseller"
                    ? "Бестселер"
                    : "Нове"}
              </span>
            )}
          </div>
          <div className="p-5">
            <h1 className="text-xl font-bold text-gray-900 leading-tight">
              {stripHtml(product.product_name)}
            </h1>
            {isSubscription ? (
              <div className="mt-2 inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-violet-100 to-fuchsia-100 px-3.5 py-2 text-xs font-semibold text-violet-700 shadow-sm border border-violet-200/60">
                <span>{periodSummary ?? "Підписка"}</span>
              </div>
            ) : (
              <div className="mt-2 inline-flex items-center gap-2 rounded-full bg-gray-100 px-3.5 py-2 text-xs font-semibold text-gray-700 shadow-sm border border-gray-200/60">
                <span>Разова оплата</span>
              </div>
            )}
            {product.product_description && (() => {
              const raw = stripHtml(product.product_description);
              const isLong = raw.length > DESCRIPTION_PREVIEW_LEN;
              const show = isLong && !descriptionExpanded ? raw.slice(0, DESCRIPTION_PREVIEW_LEN) : raw;
              return (
                <div className="mt-4 rounded-2xl bg-gray-100 border border-gray-200/80 p-4">
                  <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                    {show}
                    {isLong && !descriptionExpanded && "…"}
                  </p>
                  {isLong && !descriptionExpanded && (
                    <button
                      type="button"
                      onClick={() => setDescriptionExpanded(true)}
                      className="mt-2 text-sm font-medium text-violet-600 hover:underline"
                    >
                      Читати далі
                    </button>
                  )}
                </div>
              );
            })()}
            {showTariffs && tariffEntries.length > 0 ? (
              <div className="mt-4">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Оберіть термін підписки</p>
                <p className="text-sm text-gray-600 mb-2">{periodSummary ? `Доступні періоди: ${periodSummary}` : "Оплата через Monobank"}</p>
                {paymentError && (
                  <p className="mb-2 text-sm text-rose-600">{paymentError}</p>
                )}
                <div className="flex flex-col gap-2">
                  {tariffEntries.map((t, i) => {
                    const monthsNum = parseInt(t.months, 10);
                    return (
                      <div key={i} className="flex flex-col gap-1.5 sm:flex-row sm:items-center sm:gap-2">
                        <button
                          type="button"
                          onClick={() => handlePayWithMonobank(monthsNum)}
                          disabled={paymentLoading}
                          className="flex flex-1 items-center justify-center gap-2 rounded-2xl bg-violet-600 px-4 py-3.5 text-base font-semibold text-white shadow-md hover:bg-violet-700 active:scale-[0.98] transition-transform disabled:opacity-50"
                        >
                          <CreditCard className="w-5 h-5 shrink-0" />
                          {paymentLoading ? "Завантаження…" : t.label}
                        </button>
                        {botLink && (
                          <a
                            href={`${botLink}${botLink.includes("?") ? "&" : "?"}start=pay_${product.id}_${t.months}_${t.price}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center justify-center gap-1.5 rounded-2xl border-2 border-violet-600 bg-transparent px-4 py-3.5 text-sm font-medium text-violet-600 hover:bg-violet-50"
                          >
                            {TELEGRAM_ICON}
                            В Telegram
                          </a>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="mt-4">
                <div className="text-2xl font-bold text-gray-900">
                  {formatPriceDisplay(product.product_price)}
                </div>
                {paymentError && (
                  <p className="mt-2 text-sm text-rose-600">{paymentError}</p>
                )}
                <button
                  type="button"
                  onClick={() => handlePayWithMonobank(1)}
                  disabled={paymentLoading}
                  className="mt-3 flex w-full items-center justify-center gap-2 rounded-2xl bg-violet-600 px-4 py-3.5 text-base font-semibold text-white shadow-md hover:bg-violet-700 disabled:opacity-50"
                >
                  <CreditCard className="w-5 h-5 shrink-0" />
                  {paymentLoading ? "Завантаження…" : "Оплатити через Monobank"}
                </button>
              </div>
            )}
          </div>
        </div>

        {botLink && (
          <a
            href={botLink}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-2xl border-2 border-violet-600 bg-transparent px-6 py-3.5 text-base font-semibold text-violet-600 hover:bg-violet-50"
            aria-label="Оформити замовлення в Telegram"
          >
            {TELEGRAM_ICON}
            Оформити в Telegram
          </a>
        )}

        {relatedProducts.length > 0 && (
          <section className="mt-10 pb-6 pl-4">
            <h2 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
              <ThumbsUp className="w-5 h-5 text-violet-500" />
              Вам може сподобатися
            </h2>
            <div className="flex gap-3 overflow-x-auto pb-2 -mr-4 pr-4 scrollbar-hide" style={{ scrollSnapType: "x mandatory" }}>
              {relatedProducts.map((p) => {
                const priceStr = typeof p.product_price === "string" ? p.product_price : String(p.product_price);
                const isSub = p.payment_type === "subscription" || p.payment_type === "recurring" || isSubscriptionTariffsString(priceStr);
                const period = getSubscriptionPeriodSummary(priceStr);
                return (
                  <Link
                    key={p.id}
                    href={`/product/${p.id}`}
                    className="flex-shrink-0 w-[180px] rounded-2xl border border-gray-100 overflow-hidden hover:shadow-lg transition-shadow block bg-white"
                    style={{ scrollSnapAlign: "start" }}
                  >
                    <div className="aspect-square bg-gray-50 flex items-center justify-center overflow-hidden">
                      {p.product_photo ? (
                        <img src={p.product_photo} alt="" className="w-full h-full object-cover" />
                      ) : (
                        <span className="text-4xl">📦</span>
                      )}
                    </div>
                    <div className="p-2.5">
                      <h3 className="text-sm font-medium text-gray-900 line-clamp-2 leading-tight">
                        {stripHtml(p.product_name)}
                      </h3>
                      <p className="text-xs text-gray-500 mt-0.5">{stripHtml(p.product_type)}</p>
                      <div className="text-sm font-bold text-gray-900 mt-1">{formatPriceDisplay(p.product_price)}</div>
                      {isSub ? (
                        <div className="mt-1 inline-flex items-center gap-1 rounded-full bg-violet-50 px-2 py-0.5 text-[10px] font-medium text-violet-600">
                          {period ?? "Підписка"}
                        </div>
                      ) : (
                        <div className="mt-1 inline-flex items-center gap-1 rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-medium text-gray-600">
                          Разова оплата
                        </div>
                      )}
                    </div>
                  </Link>
                );
              })}
            </div>
          </section>
        )}

        <section className="mt-8 pb-8 pl-4 pr-4">
          <div className="rounded-2xl border border-violet-100 bg-gradient-to-br from-violet-50/80 to-fuchsia-50/80 p-4">
            <h3 className="text-sm font-bold text-gray-900 mb-1">Виникли питання? Пиши в підтримку</h3>
            <p className="text-xs text-gray-700 mb-2">💬 Зв'яжіться з нашим менеджером</p>
            <p className="text-xs text-gray-600 mb-3">
              Якщо у вас виникли питання або потрібна додаткова інформація, наш менеджер завжди готовий допомогти. 📞
            </p>
            <a
              href="https://t.me/kinomanage"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-xl bg-violet-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-violet-700"
            >
              {TELEGRAM_ICON}
              @kinomanage
            </a>
          </div>
        </section>
      </div>
    </div>
  );
}
