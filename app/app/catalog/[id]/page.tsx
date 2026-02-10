"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ChevronLeft, LayoutGrid } from "lucide-react";
import type { Product } from "@/types/catalog";
import { stripHtml, formatPriceDisplay, isSubscriptionTariffsString, getSubscriptionPeriodSummary } from "@/lib/text";

export default function CatalogCategoryPage() {
  const params = useParams();
  const router = useRouter();
  const id = Number(params.id);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    document.title = "Товари — Flix Market";
  }, []);

  useEffect(() => {
    if (!id) return;
    fetch(`/api/catalog/${id}`)
      .then((res) => res.json())
      .then((data) => setProducts(Array.isArray(data) ? data : []))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    if (products[0]?.product_type) {
      document.title = `${stripHtml(products[0].product_type)} — Flix Market`;
    }
  }, [products]);

  const categoryName = products[0]?.product_type ? stripHtml(products[0].product_type) : "Товари";

  if (loading) {
    return (
      <div className="max-w-md mx-auto min-h-screen bg-transparent pb-24">
        <div className="sticky top-0 bg-transparent z-10 px-4 py-3 flex items-center gap-3">
          <div className="h-10 w-20 bg-gray-200 rounded-xl animate-pulse" />
          <div className="h-6 w-32 bg-gray-200 rounded animate-pulse" />
        </div>
        <div className="px-4 py-4">
          <div className="grid grid-cols-2 gap-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="rounded-2xl overflow-hidden">
                <div className="aspect-square bg-gray-200 animate-pulse" />
                <div className="p-3 space-y-2">
                  <div className="h-4 bg-gray-200 rounded animate-pulse" />
                  <div className="h-5 w-1/2 bg-gray-200 rounded animate-pulse" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto min-h-screen bg-transparent pb-24">
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
          {products[0]?.product_photo ? (
            <img src={products[0].product_photo} alt="" className="h-7 w-7 rounded-lg object-cover shrink-0" />
          ) : (
            <LayoutGrid className="w-5 h-5 shrink-0 text-violet-600" aria-hidden />
          )}
          <h1 className="text-lg font-bold text-gray-900 truncate">{categoryName}</h1>
        </div>
        <div className="w-10 shrink-0" aria-hidden />
      </div>
      <div className="px-4 py-4">
        {products.length === 0 ? (
          <div className="text-center py-12">
            <LayoutGrid className="w-14 h-14 mx-auto text-gray-300 mb-3" />
            <p className="text-gray-600 font-medium mb-1">Товарів у цій категорії немає</p>
            <p className="text-sm text-gray-500 mb-4">Перегляньте інші категорії</p>
            <Link href="/catalog" className="inline-flex items-center gap-1.5 rounded-xl bg-violet-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-violet-700">
              До каталогу
            </Link>
          </div>
        ) : (
        <div className="grid grid-cols-2 gap-3">
          {products.map((p) => (
            <Link
              key={p.id}
              href={`/product/${p.id}`}
              className="bg-white rounded-2xl border border-gray-100 overflow-hidden hover:shadow-lg transition-shadow block"
            >
              <div className="relative bg-gray-50 aspect-square flex items-center justify-center text-6xl overflow-hidden">
                {p.product_photo ? (
                  <img src={p.product_photo} alt="" className="w-full h-full object-cover" />
                ) : (
                  "📦"
                )}
                {p.product_badge && (
                  <span
                    className={`absolute top-2 left-2 px-2 py-0.5 rounded-lg text-[10px] font-semibold text-white shadow ${
                      p.product_badge === "hot" ? "bg-rose-500" : p.product_badge === "bestseller" ? "bg-amber-500" : "bg-emerald-500"
                    }`}
                  >
                    {p.product_badge === "hot" ? "🔥 Гаряча пропозиція" : p.product_badge === "bestseller" ? "⭐ Бестселер" : "✨ Нове"}
                  </span>
                )}
              </div>
              <div className="p-3">
                <h4 className="text-sm font-medium text-gray-900 mb-2 line-clamp-2 leading-tight">
                  {stripHtml(p.product_name)}
                </h4>
                {p.product_description && (
                  <p className="text-xs text-gray-500 line-clamp-2 mb-1">{stripHtml(p.product_description)}</p>
                )}
                <div className="text-lg font-bold text-gray-900">
                  {formatPriceDisplay(p.product_price)}
                </div>
                {(p.payment_type === "recurring" || p.payment_type === "subscription") ? (() => {
                  const priceStr = typeof p.product_price === "string" ? p.product_price : String(p.product_price);
                  const period = getSubscriptionPeriodSummary(priceStr);
                  return (
                    <div className="mt-1.5 inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-violet-100 to-fuchsia-100 px-2.5 py-1 text-xs font-medium text-violet-700 shadow-sm border border-violet-200/60">
                      <span>{period ? `Оплата щомісячно · ${period}` : "Оплата щомісячно"}</span>
                    </div>
                  );
                })() : (
                  <div className="mt-1.5 inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-700 shadow-sm border border-gray-200/60">
                    <span>Одноразова оплата</span>
                  </div>
                )}
              </div>
            </Link>
          ))}
        </div>
        )}
      </div>
    </div>
  );
}
