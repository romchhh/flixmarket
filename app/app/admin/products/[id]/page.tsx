"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ChevronLeft, Package, TrendingUp, ShoppingCart, CreditCard, Receipt } from "lucide-react";
import { stripHtml, formatPriceDisplay } from "@/lib/text";

type ProductDetail = {
  product: {
    id: number;
    catalog_id: number;
    product_type: string;
    product_name: string;
    product_description: string | null;
    product_price: number | string;
    product_photo: string | null;
    payment_type: string;
  };
  oneTimePurchases: number;
  oneTimeRevenue: number;
  simpleSubscriptionsCount: number;
  recurringSubscriptionsCount: number;
  recurringRevenue: number;
  totalRevenue: number;
  recentPayments: Array<{
    type: "one_time";
    amount: number;
    status: string | null;
    created_at: string | null;
  }>;
  recentSubPayments: Array<{
    type: "subscription";
    amount: number;
    status: string | null;
    payment_date: string | null;
  }>;
};

function formatDateTime(s: string | null) {
  if (!s) return "—";
  try {
    return new Date(s).toLocaleString("uk-UA", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return s;
  }
}

export default function ProductDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [data, setData] = useState<ProductDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const idNum = parseInt(id, 10);
    if (!Number.isInteger(idNum) || idNum < 1) {
      setError("Невірний ID");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    fetch(`/api/admin/products/${idNum}/detail`)
      .then((r) => {
        if (!r.ok) {
          if (r.status === 404) throw new Error("Товар не знайдено");
          throw new Error("Помилка завантаження");
        }
        return r.json();
      })
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Помилка"))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="space-y-6">
        <Link
          href="/admin/products"
          className="inline-flex items-center gap-1 text-sm text-violet-600 hover:underline"
        >
          <ChevronLeft className="h-4 w-4" />
          Товари
        </Link>
        <p className="text-gray-500">Завантаження…</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-6">
        <Link
          href="/admin/products"
          className="inline-flex items-center gap-1 text-sm text-violet-600 hover:underline"
        >
          <ChevronLeft className="h-4 w-4" />
          Товари
        </Link>
        <p className="text-red-600">{error || "Товар не знайдено"}</p>
      </div>
    );
  }

  const { product, oneTimePurchases, oneTimeRevenue, simpleSubscriptionsCount, recurringSubscriptionsCount, recurringRevenue, totalRevenue, recentPayments, recentSubPayments } = data;
  const totalPurchases = oneTimePurchases + simpleSubscriptionsCount + recurringSubscriptionsCount;

  const mergedRecent = [
    ...recentPayments.map((p) => ({ ...p, date: p.created_at, type: "one_time" as const })),
    ...recentSubPayments.map((p) => ({ ...p, date: p.payment_date, type: "subscription" as const })),
  ]
    .sort((a, b) => {
      const da = a.date ? new Date(a.date).getTime() : 0;
      const db = b.date ? new Date(b.date).getTime() : 0;
      return db - da;
    })
    .slice(0, 20);

  return (
    <div className="space-y-6">
      <Link
        href="/admin/products"
        className="inline-flex items-center gap-1 text-sm text-violet-600 hover:underline"
      >
        <ChevronLeft className="h-4 w-4" />
        Товари
      </Link>

      <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm sm:p-6">
        <h1 className="text-xl font-bold text-gray-900 sm:text-2xl">Товар: {stripHtml(product.product_name)}</h1>
        <div className="mt-4 flex flex-wrap items-start gap-4">
          {product.product_photo && (
            <img
              src={product.product_photo}
              alt=""
              className="h-24 w-24 rounded-lg object-cover"
            />
          )}
          <div className="min-w-0">
            <p className="text-sm text-gray-500">Категорія: {stripHtml(product.product_type)}</p>
            <p className="mt-1 font-medium text-gray-900">{formatPriceDisplay(product.product_price)}</p>
            <p className="text-sm text-gray-500">
              {product.payment_type === "subscription" ? "Підписка" : "Одноразово"}
            </p>
            {product.product_description && (
              <p className="mt-2 text-sm text-gray-600">{product.product_description}</p>
            )}
          </div>
          <div className="ml-auto flex gap-2">
            <Link
              href={`/admin/products/${product.id}/edit`}
              className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-700"
            >
              Редагувати
            </Link>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="flex items-start gap-3 rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
          <TrendingUp className="h-8 w-8 shrink-0 text-green-600" />
          <div>
            <p className="text-xs font-medium uppercase text-gray-500">Дохід всього</p>
            <p className="mt-1 text-2xl font-bold text-gray-900">{totalRevenue.toFixed(0)} ₴</p>
          </div>
        </div>
        <div className="flex items-start gap-3 rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
          <ShoppingCart className="h-8 w-8 shrink-0 text-violet-600" />
          <div>
            <p className="text-xs font-medium uppercase text-gray-500">Куплено разів</p>
            <p className="mt-1 text-2xl font-bold text-gray-900">{totalPurchases}</p>
            <p className="text-xs text-gray-500">
              одноразово: {oneTimePurchases}, прості підписки: {simpleSubscriptionsCount}, рекуррентні: {recurringSubscriptionsCount}
            </p>
          </div>
        </div>
        <div className="flex items-start gap-3 rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
          <Receipt className="h-8 w-8 shrink-0 text-amber-600" />
          <div>
            <p className="text-xs font-medium uppercase text-gray-500">Одноразові платежі</p>
            <p className="mt-1 text-xl font-bold text-gray-900">{oneTimeRevenue.toFixed(0)} ₴</p>
            <p className="text-xs text-gray-500">{oneTimePurchases} шт.</p>
          </div>
        </div>
        <div className="flex items-start gap-3 rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
          <CreditCard className="h-8 w-8 shrink-0 text-blue-600" />
          <div>
            <p className="text-xs font-medium uppercase text-gray-500">По підписках</p>
            <p className="mt-1 text-xl font-bold text-gray-900">{recurringRevenue.toFixed(0)} ₴</p>
            <p className="text-xs text-gray-500">
              простих: {simpleSubscriptionsCount}, рекуррентних: {recurringSubscriptionsCount}
            </p>
          </div>
        </div>
      </div>

      {mergedRecent.length > 0 && (
        <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
          <h2 className="flex items-center gap-2 border-b border-gray-200 px-4 py-3 text-lg font-semibold text-gray-900 sm:px-6">
            <Receipt className="h-5 w-5" />
            Останні платежі
          </h2>
          <div className="overflow-x-auto">
            <table className="min-w-[400px] divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Дата</th>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Тип</th>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Сума</th>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Статус</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {mergedRecent.map((p, i) => (
                  <tr key={`${p.type}-${i}`} className="hover:bg-gray-50">
                    <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-600 sm:px-4 sm:py-3">
                      {formatDateTime(p.date)}
                    </td>
                    <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-600 sm:px-4 sm:py-3">
                      {p.type === "one_time" ? "Одноразово" : "Підписка"}
                    </td>
                    <td className="whitespace-nowrap px-3 py-2 text-sm font-medium text-gray-900 sm:px-4 sm:py-3">
                      {p.amount} ₴
                    </td>
                    <td className="whitespace-nowrap px-3 py-2 sm:px-4 sm:py-3">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                          p.status === "success"
                            ? "bg-green-100 text-green-700"
                            : p.status === "failed" || p.status === "pending"
                              ? "bg-amber-100 text-amber-700"
                              : "bg-gray-100 text-gray-600"
                        }`}
                      >
                        {p.status ?? "—"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
