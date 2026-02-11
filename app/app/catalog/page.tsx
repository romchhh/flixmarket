"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ChevronLeft, LayoutGrid } from "lucide-react";
import type { ProductType, Product } from "@/types/catalog";
import { stripHtml, formatPriceDisplay, isSubscriptionTariffsString, getSubscriptionPeriodSummary } from "@/lib/text";

const CATEGORY_COLORS = ["#E8D5FF", "#D5F0FF", "#FFE8D5", "#FFD5E8", "#D5FFE8", "#F5E8FF", "#FFE8E8", "#E8F5FF", "#FFF5E8"];
const CATEGORY_ICONS = ["👗", "👔", "💻", "🔌", "🖥️", "📱", "📺", "📱", "🎧"];

export default function CatalogPage() {
  const [categories, setCategories] = useState<ProductType[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    document.title = "Каталог — Flix Market";
  }, []);

  useEffect(() => {
    Promise.all([
      fetch("/api/catalog").then((r) => r.json()),
      fetch("/api/products").then((r) => (r.ok ? r.json() : [])),
    ])
      .then(([cats, prods]) => {
        setCategories(Array.isArray(cats) ? cats : []);
        setProducts(Array.isArray(prods) ? prods : []);
      })
      .finally(() => setLoading(false));
  }, []);

  const productsByCatalogId = products.reduce<Record<number, Product[]>>((acc, p) => {
    const id = p.catalog_id;
    if (!acc[id]) acc[id] = [];
    acc[id].push(p);
    return acc;
  }, {});

  if (loading) {
    return (
      <div className="max-w-md mx-auto min-h-screen bg-transparent pb-24">
        <div className="sticky top-0 bg-transparent z-10 px-4 py-3 flex items-center justify-center">
          <div className="flex items-center gap-2">
            <LayoutGrid className="w-5 h-5 shrink-0 text-violet-600" aria-hidden />
            <div className="h-6 w-24 bg-gray-200 rounded animate-pulse" />
          </div>
        </div>
        <div className="px-4 py-4">
          <div className="grid grid-cols-4 gap-2">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="rounded-xl bg-gray-200 animate-pulse aspect-[3/4] max-h-24" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto min-h-screen bg-transparent pb-24">
      <div className="sticky top-0 bg-transparent z-10 px-4 py-3 flex items-center justify-between">
        <Link href="/" className="p-2 -ml-2 rounded-full hover:bg-gray-100 flex items-center justify-center text-gray-600 shrink-0 w-10 h-10" aria-label="Назад">
          <ChevronLeft className="w-5 h-5" />
        </Link>
        <div className="absolute left-1/2 -translate-x-1/2 flex items-center justify-center gap-2">
          {typeof process.env.NEXT_PUBLIC_APP_LOGO === "string" && process.env.NEXT_PUBLIC_APP_LOGO ? (
            <img src={process.env.NEXT_PUBLIC_APP_LOGO} alt="" className="h-7 w-7 rounded-lg object-cover shrink-0" />
          ) : (
            <LayoutGrid className="w-5 h-5 shrink-0 text-violet-600" aria-hidden />
          )}
          <h1 className="text-lg font-bold text-gray-900">Каталог</h1>
        </div>
        <div className="w-10 shrink-0" aria-hidden />
      </div>
      <div className="px-4 py-4">
        {categories.length === 0 ? (
          <div className="text-center py-12">
            <LayoutGrid className="w-14 h-14 mx-auto text-gray-300 mb-3" />
            <p className="text-gray-600 font-medium mb-1">Категорій поки немає</p>
            <p className="text-sm text-gray-500 mb-4">Вони з'являться після додавання товарів в адмін-панелі</p>
            <Link href="/" className="inline-flex items-center gap-1.5 rounded-xl bg-violet-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-violet-700">
              На головну
            </Link>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-4 gap-2">
              {categories.map((c, i) => (
                <Link
                  key={c.catalog_id}
                  href={`/catalog/${c.catalog_id}`}
                  className="flex flex-col items-center gap-1.5"
                >
                  <div className="w-[72%] mx-auto rounded-xl overflow-hidden border border-gray-100 bg-white shadow-sm hover:shadow-md transition-shadow active:scale-[0.98] aspect-square flex items-center justify-center">
                    {c.catalog_photo ? (
                      <img src={c.catalog_photo} alt="" className="w-full h-full object-cover" />
                    ) : (
                      <span className="text-2xl" style={{ color: CATEGORY_COLORS[i % CATEGORY_COLORS.length] }}>{CATEGORY_ICONS[i % CATEGORY_ICONS.length]}</span>
                    )}
                  </div>
                  <span className="text-[10px] font-bold text-gray-800 text-center leading-tight line-clamp-2 w-full">
                    {stripHtml(c.product_type)}
                  </span>
                </Link>
              ))}
            </div>

            {categories.map((c) => {
              const categoryProducts = productsByCatalogId[c.catalog_id] ?? [];
              if (categoryProducts.length === 0) return null;
              return (
                <section key={c.catalog_id} className="mt-8">
                  <div className="flex items-center justify-between mb-3">
                    <h2 className="text-lg font-bold text-gray-900">{stripHtml(c.product_type)}</h2>
                    <Link
                      href={`/catalog/${c.catalog_id}`}
                      className="text-sm font-medium text-violet-600 hover:underline"
                    >
                      Всі
                    </Link>
                  </div>
                  <div
                    className="flex gap-3 overflow-x-auto pb-2 -mx-4 px-4 scrollbar-hide"
                    style={{ scrollSnapType: "x mandatory" }}
                  >
                    {categoryProducts.map((p) => {
                      const priceStr = typeof p.product_price === "string" ? p.product_price : String(p.product_price);
                      const isSub =
                        p.payment_type === "subscription" ||
                        p.payment_type === "recurring";
                      const period = getSubscriptionPeriodSummary(priceStr);
                      return (
                        <Link
                          key={p.id}
                          href={`/product/${p.id}`}
                          className="flex-shrink-0 w-[180px] rounded-2xl border border-gray-100 overflow-hidden hover:shadow-lg transition-shadow block bg-white"
                          style={{ scrollSnapAlign: "start" }}
                        >
                          <div className="relative aspect-square bg-gray-50 flex items-center justify-center overflow-hidden">
                            {p.product_photo ? (
                              <img src={p.product_photo} alt="" className="w-full h-full object-cover" />
                            ) : (
                              <span className="text-4xl">📦</span>
                            )}
                            {p.product_badge && (
                              <span
                                className={`absolute top-2 left-2 px-2 py-0.5 rounded-lg text-[10px] font-semibold text-white shadow ${
                                  p.product_badge === "hot"
                                    ? "bg-rose-500"
                                    : p.product_badge === "bestseller"
                                      ? "bg-amber-500"
                                      : "bg-emerald-500"
                                }`}
                              >
                                {p.product_badge === "hot"
                                  ? "🔥 Гаряча пропозиція"
                                  : p.product_badge === "bestseller"
                                    ? "⭐ Бестселер"
                                    : "✨ Нове"}
                              </span>
                            )}
                          </div>
                          <div className="p-2.5">
                            <h3 className="text-sm font-medium text-gray-900 line-clamp-2 leading-tight">
                              {stripHtml(p.product_name)}
                            </h3>
                            <div className="text-sm font-bold text-gray-900 mt-1">
                              {formatPriceDisplay(p.product_price)}
                            </div>
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
              );
            })}
          </>
        )}
      </div>
    </div>
  );
}
