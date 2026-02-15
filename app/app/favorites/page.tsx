"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Heart } from "lucide-react";
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
  product_badge?: string;
};

export default function FavoritesPage() {
  const [favoriteIds, setFavoriteIds] = useState<Set<number>>(new Set());
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    document.title = "Обране — Flix Market";
  }, []);

  useEffect(() => {
    try {
      const raw = localStorage.getItem("flix-favorites");
      if (raw) setFavoriteIds(new Set(JSON.parse(raw)));
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    fetch("/api/products")
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => setProducts(Array.isArray(data) ? data : []))
      .finally(() => setLoading(false));
  }, []);

  const toggleFavorite = (productId: number) => {
    setFavoriteIds((prev) => {
      const next = new Set(prev);
      if (next.has(productId)) next.delete(productId);
      else next.add(productId);
      try {
        localStorage.setItem("flix-favorites", JSON.stringify([...next]));
      } catch {
        // ignore
      }
      return next;
    });
  };

  const favoriteProducts = products.filter((p) => favoriteIds.has(p.id));

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-10 h-10 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto min-h-screen px-4 py-6 pb-24">
      <div className="flex items-center justify-center gap-2 mb-6">
        <Heart className="w-6 h-6 shrink-0 text-violet-600" aria-hidden />
        <h1 className="text-2xl font-bold text-gray-900 text-center">
          Обране{favoriteProducts.length > 0 ? ` (${favoriteProducts.length})` : ""}
        </h1>
      </div>
      {favoriteProducts.length === 0 ? (
        <div className="text-center py-16">
          <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
            <Heart className="w-10 h-10 text-gray-400" />
          </div>
          <p className="text-gray-700 font-medium text-lg">Немає обраного</p>
          <p className="text-gray-500 text-sm mt-2 max-w-xs mx-auto">
            Додайте товари з головної або каталогу — натисніть серце на картці товару
          </p>
          <Link
            href="/catalog"
            className="inline-flex items-center justify-center mt-6 rounded-xl border-2 border-violet-600 bg-transparent px-5 py-2.5 text-sm font-medium text-violet-600 hover:bg-violet-50"
          >
            Перейти в каталог
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3 pb-8">
          {favoriteProducts.map((product) => (
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
                {product.product_badge && (
                  <span
                    className={`absolute top-2 left-2 px-2 py-0.5 rounded-lg text-[10px] font-semibold text-white shadow ${
                      product.product_badge === "hot" ? "bg-rose-500" : product.product_badge === "bestseller" ? "bg-amber-500" : "bg-emerald-500"
                    }`}
                  >
                    {product.product_badge === "hot" ? "Гаряча пропозиція" : product.product_badge === "bestseller" ? "Бестселер" : "Нове"}
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
                    fill="currentColor"
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
                {(() => {
                  const priceStr = typeof product.product_price === "string" ? product.product_price : String(product.product_price);
                  const showPeriod = (product.payment_type === "recurring" || product.payment_type === "subscription") || isSubscriptionTariffsString(priceStr);
                  const period = getSubscriptionPeriodSummary(priceStr);
                  return showPeriod ? (
                    <div className="mt-1.5 inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-violet-100 to-fuchsia-100 px-2.5 py-1 text-xs font-medium text-violet-700 shadow-sm border border-violet-200/60">
                      <span>{period ?? "Підписка"}</span>
                    </div>
                  ) : (
                    <div className="mt-1.5 inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-700 shadow-sm border border-gray-200/60">
                      <span>Разова оплата</span>
                    </div>
                  );
                })()}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
