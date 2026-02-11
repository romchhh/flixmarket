"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Heart, Search, LayoutGrid, Smartphone, X, Zap } from "lucide-react";
import { stripHtml, formatPriceDisplay, isSubscriptionTariffsString, getSubscriptionPeriodSummary } from "@/lib/text";

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

type Category = {
  catalog_id: number;
  product_type: string;
  catalog_photo?: string | null;
};

const CATEGORY_COLORS = [
  "#E8D5FF",
  "#D5F0FF",
  "#FFE8D5",
  "#FFD5E8",
  "#D5FFE8",
  "#F5E8FF",
  "#FFE8E8",
  "#E8F5FF",
  "#FFF5E8",
];

const CATEGORY_ICONS = ["👗", "👔", "💻", "🔌", "🖥️", "📱", "📺", "📱", "🎧"];

function getInitialFavorites(): Set<number> {
  if (typeof window === "undefined") return new Set();
  try {
    const raw = localStorage.getItem("flix-favorites");
    if (raw) {
      const arr = JSON.parse(raw);
      return new Set(Array.isArray(arr) ? arr : []);
    }
  } catch {
    // ignore
  }
  return new Set();
}

export default function CatalogShell() {
  const [favorites, setFavorites] = useState<Set<number>>(getInitialFavorites);
  const [categories, setCategories] = useState<Category[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    Promise.all([
      fetch("/api/catalog").then((r) => r.json()),
      fetch("/api/products").then((r) => r.json()),
    ])
      .then(([cats, prods]) => {
        setCategories(Array.isArray(cats) ? cats : []);
        setProducts(Array.isArray(prods) ? prods : []);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem("flix-favorites", JSON.stringify([...favorites]));
    } catch {
      // ignore
    }
  }, [favorites]);

  useEffect(() => {
    const handler = () => {
      try {
        const raw = localStorage.getItem("flix-favorites");
        if (raw) setFavorites(new Set(JSON.parse(raw)));
      } catch {
        // ignore
      }
    };
    window.addEventListener("flix-favorites-changed", handler);
    return () => window.removeEventListener("flix-favorites-changed", handler);
  }, []);

  const toggleFavorite = (productId: number) => {
    setFavorites((prev) => {
      const next = new Set(prev);
      if (next.has(productId)) next.delete(productId);
      else next.add(productId);
      return next;
    });
  };

  const renderHome = () => (
    <>
      <div className="sticky top-0 bg-gradient-to-b from-violet-50/95 to-white/90 backdrop-blur-xl border-b border-gray-100/80 z-10">
        <div className="px-4 pt-4 pb-3">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Пошук"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-10 py-3 bg-white rounded-full border border-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-violet-200 transition-all shadow-sm"
              />
              {searchQuery.length > 0 && (
                <button
                  type="button"
                  onClick={() => setSearchQuery("")}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-full hover:bg-gray-100 text-gray-400 hover:text-gray-600"
                  aria-label="Очистити пошук"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>
            <Link
              href="/catalog"
              className="px-5 py-3 bg-white text-violet-600 rounded-full text-sm font-medium flex items-center gap-2 hover:bg-violet-50 border border-gray-100 shadow-sm transition-colors shrink-0"
            >
              <LayoutGrid className="w-4 h-4" />
              Каталог
            </Link>
          </div>
          <div className="bg-gradient-to-r from-violet-50 to-fuchsia-50 rounded-2xl p-4 flex items-center gap-3 border border-violet-100">
            <div className="w-10 h-10 bg-violet-500 rounded-xl flex items-center justify-center text-white shrink-0">
              <Zap className="w-5 h-5" strokeWidth={2} />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-800">Оплата в один клік</p>
              <p className="text-xs text-gray-600">Не виходьте з Telegram — оплачуйте прямо в боті</p>
            </div>
          </div>
        </div>
        <Link
          href="/catalog"
          className="mx-4 mb-4 block bg-gradient-to-r from-violet-600 to-indigo-500 rounded-3xl p-5 text-white relative overflow-hidden hover:opacity-95 active:scale-[0.99] transition-all shadow-lg"
        >
          <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-20">
            <Smartphone className="w-24 h-24" strokeWidth={1.5} />
          </div>
          <div className="relative z-10">
            <p className="text-sm opacity-90 mb-1">Підписки на сервіси в Telegram</p>
            <h2 className="text-2xl font-bold leading-tight mb-3">
              Підписки від 1 місяця. Оплачуйте щомісяця прямо в месенджері.
            </h2>
            <span className="inline-flex items-center gap-1.5 text-sm font-semibold text-white/95">
              Перейти в каталог
              <LayoutGrid className="w-4 h-4" />
            </span>
          </div>
        </Link>
      </div>

      <div className="px-4 py-4">
        <div className="grid grid-cols-4 gap-2 mb-6">
          {categories.slice(0, 12).map((cat, i) => (
            <Link
              key={cat.catalog_id}
              href={`/catalog/${cat.catalog_id}`}
              className="flex flex-col items-center gap-1.5"
            >
              <div className="w-[72%] mx-auto rounded-xl overflow-hidden border border-gray-100 bg-white shadow-sm hover:shadow-md transition-shadow active:scale-[0.98] aspect-square flex items-center justify-center">
                {cat.catalog_photo ? (
                  <img src={cat.catalog_photo} alt="" className="w-full h-full object-cover" />
                ) : (
                  <span className="text-2xl" style={{ color: CATEGORY_COLORS[i % CATEGORY_COLORS.length] }}>{CATEGORY_ICONS[i % CATEGORY_ICONS.length]}</span>
                )}
              </div>
              <span className="text-[10px] font-bold text-gray-800 text-center leading-tight line-clamp-2 w-full">
                {stripHtml(cat.product_type)}
              </span>
            </Link>
          ))}
        </div>

        <h3 className="text-xl font-bold mb-1">
          {searchQuery ? "Результати пошуку" : "Каталог"}
        </h3>
        {(() => {
          const q = searchQuery.trim().toLowerCase();
          const filtered = q
            ? products.filter(
                (p) =>
                  stripHtml(p.product_name).toLowerCase().includes(q) ||
                  (p.product_description && stripHtml(p.product_description).toLowerCase().includes(q)) ||
                  stripHtml(p.product_type).toLowerCase().includes(q)
              )
            : products;
          return (
            <>
              {searchQuery && (
                <p className="text-sm text-gray-500 mb-3">
                  Знайдено {filtered.length} {filtered.length === 1 ? "товар" : filtered.length < 5 ? "товари" : "товарів"}
                </p>
              )}
        <div className="grid grid-cols-2 gap-3 pb-28">
          {filtered.length === 0 ? (
            <div className="col-span-2 text-center py-10 px-4">
              <p className="text-gray-600 font-medium mb-1">
                {searchQuery ? "Нічого не знайдено" : "Немає товарів"}
              </p>
              <p className="text-sm text-gray-500 mb-4">
                {searchQuery ? "Спробуйте інший запит або перегляньте каталог" : "Товари з'являться після додавання в адмінці"}
              </p>
              <Link
                href="/catalog"
                className="inline-flex items-center gap-1.5 rounded-xl border-2 border-violet-600 bg-transparent px-4 py-2.5 text-sm font-medium text-violet-600 hover:bg-violet-50"
              >
                <LayoutGrid className="w-4 h-4" />
                Перейти в каталог
              </Link>
            </div>
          ) : (
          filtered.map((product) => (
            <Link
              key={product.id}
              href={`/product/${product.id}`}
              className="bg-white rounded-2xl border border-gray-100 overflow-hidden hover:shadow-lg transition-shadow block"
            >
              <div className="relative bg-gray-50 aspect-square flex items-center justify-center text-6xl">
                {product.product_photo ? (
                  <img
                    src={product.product_photo}
                    alt=""
                    className="w-full h-full object-cover"
                  />
                ) : (
                  "📦"
                )}
                {(product as { product_badge?: string }).product_badge && (
                  <span
                    className={`absolute top-2 left-2 px-2 py-0.5 rounded-lg text-[10px] font-semibold text-white shadow ${
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
                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    toggleFavorite(product.id);
                  }}
                  className="absolute bottom-2 right-2 w-9 h-9 flex items-center justify-center hover:scale-110 transition-transform active:scale-95 text-violet-500"
                >
                  <Heart
                    className="w-6 h-6"
                    fill={favorites.has(product.id) ? "currentColor" : "none"}
                    stroke="currentColor"
                    strokeWidth={2}
                  />
                </button>
              </div>
              <div className="p-3">
                <h4 className="text-sm font-medium text-gray-900 mb-1 line-clamp-2 leading-tight">
                  {stripHtml(product.product_name)}
                </h4>
                {product.product_description && (
                  <p className="text-xs text-gray-500 line-clamp-2 mb-2 leading-tight">
                    {stripHtml(product.product_description)}
                  </p>
                )}
                <div className="text-lg font-bold text-gray-900">
                  {formatPriceDisplay(product.product_price)}
                </div>
                {(product.payment_type === "recurring" || product.payment_type === "subscription") ? (() => {
                  const priceStr = typeof product.product_price === "string" ? product.product_price : String(product.product_price);
                  const period = getSubscriptionPeriodSummary(priceStr);
                  return (
                    <div className="mt-1.5 inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-violet-100 to-fuchsia-100 px-2.5 py-1 text-xs font-medium text-violet-700 shadow-sm border border-violet-200/60">
                      <span>{period ?? "Підписка"}</span>
                    </div>
                  );
                })() : (
                  <div className="mt-1.5 inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-700 shadow-sm border border-gray-200/60">
                    <span>Разова оплата</span>
                  </div>
                )}
              </div>
            </Link>
          ))
          )}
        </div>
            </>
          );
        })()}
      </div>
    </>
  );

  return (
    <div className="max-w-md mx-auto min-h-screen bg-transparent relative flex flex-col">
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-4">
            <div className="h-8 w-48 bg-gray-200 rounded-xl animate-pulse mb-6" />
            <div className="grid grid-cols-4 gap-2 mb-6">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="rounded-xl overflow-hidden">
                  <div className="aspect-square bg-gray-200 animate-pulse" />
                  <div className="h-6 bg-gray-100 animate-pulse mt-1 rounded" />
                </div>
              ))}
            </div>
            <div className="h-6 w-32 bg-gray-200 rounded animate-pulse mb-4" />
            <div className="grid grid-cols-2 gap-3">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="rounded-2xl overflow-hidden">
                  <div className="aspect-square bg-gray-200 animate-pulse" />
                  <div className="p-3 space-y-2">
                    <div className="h-4 bg-gray-200 rounded animate-pulse" />
                    <div className="h-4 w-2/3 bg-gray-200 rounded animate-pulse" />
                    <div className="h-5 w-1/2 bg-gray-200 rounded animate-pulse" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          renderHome()
        )}
      </div>
    </div>
  );
}
