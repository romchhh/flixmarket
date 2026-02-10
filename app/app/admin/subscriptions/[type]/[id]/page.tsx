"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ChevronLeft, User, Package, Calendar, CreditCard } from "lucide-react";
import { stripHtml } from "@/lib/text";

type SimpleDetail = {
  type: "simple";
  subscription: {
    id: number;
    user_id: number;
    user_name: string | null;
    product_name: string | null;
    price: number;
    start_date: string | null;
    end_date: string | null;
    status: string | null;
  };
  payments: never[];
};

type RecurringDetail = {
  type: "recurring";
  subscription: {
    id: number;
    user_id: number;
    user_name: string | null;
    product_name: string | null;
    months: number;
    price: number;
    next_payment_date: string | null;
    status: string | null;
    payment_failures: number;
  };
  payments: Array<{
    id: number;
    amount: number;
    payment_date: string | null;
    status: string | null;
    invoice_id: string | null;
  }>;
};

type Detail = SimpleDetail | RecurringDetail;

function formatDate(s: string | null) {
  if (!s) return "—";
  try {
    return new Date(s).toLocaleDateString("uk-UA", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  } catch {
    return s;
  }
}

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

export default function SubscriptionDetailPage() {
  const params = useParams();
  const type = params.type as string;
  const id = params.id as string;
  const [data, setData] = useState<Detail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (type !== "simple" && type !== "recurring") {
      setError("Невірний тип підписки");
      setLoading(false);
      return;
    }
    const idNum = parseInt(id, 10);
    if (!Number.isInteger(idNum) || idNum < 1) {
      setError("Невірний ID");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    fetch(`/api/admin/subscriptions/${type}/${idNum}`)
      .then((r) => {
        if (!r.ok) {
          if (r.status === 404) throw new Error("Підписку не знайдено");
          throw new Error("Помилка завантаження");
        }
        return r.json();
      })
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Помилка"))
      .finally(() => setLoading(false));
  }, [type, id]);

  if (loading) {
    return (
      <div className="space-y-6">
        <Link
          href="/admin/subscriptions"
          className="inline-flex items-center gap-1 text-sm text-violet-600 hover:underline"
        >
          <ChevronLeft className="h-4 w-4" />
          Підписки
        </Link>
        <p className="text-gray-500">Завантаження…</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-6">
        <Link
          href="/admin/subscriptions"
          className="inline-flex items-center gap-1 text-sm text-violet-600 hover:underline"
        >
          <ChevronLeft className="h-4 w-4" />
          Підписки
        </Link>
        <p className="text-red-600">{error || "Підписку не знайдено"}</p>
      </div>
    );
  }

  const sub = data.subscription;
  const isRecurring = data.type === "recurring";

  return (
    <div className="space-y-6">
      <Link
        href="/admin/subscriptions"
        className="inline-flex items-center gap-1 text-sm text-violet-600 hover:underline"
      >
        <ChevronLeft className="h-4 w-4" />
        Підписки
      </Link>

      <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm sm:p-6">
        <h1 className="text-xl font-bold text-gray-900 sm:text-2xl">
          Підписка #{sub.id} {isRecurring ? "(рекуррентна)" : "(проста)"}
        </h1>

        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <div className="flex items-start gap-3 rounded-xl border border-gray-100 bg-gray-50/50 p-4">
            <User className="h-5 w-5 shrink-0 text-gray-500" />
            <div>
              <p className="text-xs font-medium uppercase text-gray-500">Користувач</p>
              <p className="mt-0.5 font-medium text-gray-900">{sub.user_name ?? "—"}</p>
              <p className="text-sm text-gray-500">Telegram ID: {sub.user_id}</p>
            </div>
          </div>
          <div className="flex items-start gap-3 rounded-xl border border-gray-100 bg-gray-50/50 p-4">
            <Package className="h-5 w-5 shrink-0 text-gray-500" />
            <div>
              <p className="text-xs font-medium uppercase text-gray-500">Товар</p>
              <p className="mt-0.5 font-medium text-gray-900">{stripHtml(sub.product_name ?? "") || "—"}</p>
            </div>
          </div>
          <div className="flex items-start gap-3 rounded-xl border border-gray-100 bg-gray-50/50 p-4">
            <CreditCard className="h-5 w-5 shrink-0 text-gray-500" />
            <div>
              <p className="text-xs font-medium uppercase text-gray-500">Ціна / Статус</p>
              <p className="mt-0.5 font-medium text-gray-900">{sub.price} ₴</p>
              <span
                className={`mt-1 inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                  sub.status === "active" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"
                }`}
              >
                {sub.status ?? "—"}
              </span>
              {isRecurring && data.subscription.payment_failures > 0 && (
                <p className="mt-1 text-xs text-red-600">
                  Помилок оплати: {data.subscription.payment_failures}
                </p>
              )}
            </div>
          </div>
          <div className="flex items-start gap-3 rounded-xl border border-gray-100 bg-gray-50/50 p-4">
            <Calendar className="h-5 w-5 shrink-0 text-gray-500" />
            <div>
              <p className="text-xs font-medium uppercase text-gray-500">
                {isRecurring ? "Наступний платіж" : "Період"}
              </p>
              {isRecurring ? (
                <p className="mt-0.5 font-medium text-gray-900">
                  {formatDate((sub as RecurringDetail["subscription"]).next_payment_date)}
                </p>
              ) : (
                <p className="mt-0.5 font-medium text-gray-900">
                  {formatDate((sub as SimpleDetail["subscription"]).start_date)} —{" "}
                  {formatDate((sub as SimpleDetail["subscription"]).end_date)}
                </p>
              )}
              {isRecurring && (
                <p className="text-sm text-gray-500">
                  {(sub as RecurringDetail["subscription"]).months} міс.
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      {isRecurring && data.payments.length > 0 && (
        <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
          <h2 className="border-b border-gray-200 px-4 py-3 text-lg font-semibold text-gray-900 sm:px-6">
            Історія платежів
          </h2>
          <div className="overflow-x-auto">
            <table className="min-w-[400px] divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">
                    Дата
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">
                    Сума
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">
                    Статус
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">
                    Invoice
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {data.payments.map((p) => (
                  <tr key={p.id} className="hover:bg-gray-50">
                    <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-600 sm:px-4 sm:py-3">
                      {formatDateTime(p.payment_date)}
                    </td>
                    <td className="whitespace-nowrap px-3 py-2 text-sm font-medium text-gray-900 sm:px-4 sm:py-3">
                      {p.amount} ₴
                    </td>
                    <td className="whitespace-nowrap px-3 py-2 sm:px-4 sm:py-3">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                          p.status === "success"
                            ? "bg-green-100 text-green-700"
                            : p.status === "failed"
                              ? "bg-red-100 text-red-700"
                              : "bg-gray-100 text-gray-600"
                        }`}
                      >
                        {p.status ?? "—"}
                      </span>
                    </td>
                    <td className="max-w-[120px] truncate px-3 py-2 text-xs text-gray-500 sm:px-4 sm:py-3">
                      {p.invoice_id ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {isRecurring && data.payments.length === 0 && (
        <div className="rounded-2xl border border-gray-200 bg-white p-6 text-center text-gray-500">
          Історія платежів по цій підписці поки порожня.
        </div>
      )}
    </div>
  );
}
