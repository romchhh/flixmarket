"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ChevronLeft, User, CreditCard, Receipt, Calendar } from "lucide-react";

type UserDetail = {
  user: {
    id: number;
    user_id: number;
    user_name: string | null;
    ref_id: number | null;
    join_date: string | null;
    discounts: number;
  };
  simpleSubscriptions: Array<{
    id: number;
    product_name: string | null;
    price: number;
    start_date: string | null;
    end_date: string | null;
    status: string | null;
  }>;
  recurringSubscriptions: Array<{
    id: number;
    product_name: string | null;
    months: number;
    price: number;
    next_payment_date: string | null;
    status: string | null;
    payment_failures: number;
  }>;
  payments: Array<{
    payment_id: string | null;
    amount: number;
    status: string | null;
    payment_type: string | null;
    created_at: string | null;
  }>;
  subPayments: Array<{
    id: number;
    subscription_id: number;
    amount: number;
    payment_date: string | null;
    status: string | null;
  }>;
};

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

export default function UserDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [data, setData] = useState<UserDetail | null>(null);
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
    fetch(`/api/admin/users/${idNum}`)
      .then((r) => {
        if (!r.ok) {
          if (r.status === 404) throw new Error("Користувача не знайдено");
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
          href="/admin/users"
          className="inline-flex items-center gap-1 text-sm text-violet-600 hover:underline"
        >
          <ChevronLeft className="h-4 w-4" />
          Користувачі
        </Link>
        <p className="text-gray-500">Завантаження…</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-6">
        <Link
          href="/admin/users"
          className="inline-flex items-center gap-1 text-sm text-violet-600 hover:underline"
        >
          <ChevronLeft className="h-4 w-4" />
          Користувачі
        </Link>
        <p className="text-red-600">{error || "Користувача не знайдено"}</p>
      </div>
    );
  }

  const { user, simpleSubscriptions, recurringSubscriptions, payments, subPayments } = data;

  return (
    <div className="space-y-6">
      <Link
        href="/admin/users"
        className="inline-flex items-center gap-1 text-sm text-violet-600 hover:underline"
      >
        <ChevronLeft className="h-4 w-4" />
        Користувачі
      </Link>

      <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm sm:p-6">
        <h1 className="text-xl font-bold text-gray-900 sm:text-2xl">Користувач #{user.id}</h1>
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <div className="flex items-start gap-3 rounded-xl border border-gray-100 bg-gray-50/50 p-4">
            <User className="h-5 w-5 shrink-0 text-gray-500" />
            <div>
              <p className="text-xs font-medium uppercase text-gray-500">Ім'я</p>
              <p className="mt-0.5 font-medium text-gray-900">{user.user_name ?? "—"}</p>
              <p className="text-sm text-gray-500">Telegram ID: {user.user_id}</p>
            </div>
          </div>
          <div className="flex items-start gap-3 rounded-xl border border-gray-100 bg-gray-50/50 p-4">
            <Calendar className="h-5 w-5 shrink-0 text-gray-500" />
            <div>
              <p className="text-xs font-medium uppercase text-gray-500">Реєстрація / Реферал</p>
              <p className="mt-0.5 font-medium text-gray-900">{formatDate(user.join_date)}</p>
              <p className="text-sm text-gray-500">Реферал: {user.ref_id ?? "—"}</p>
              <p className="text-sm text-gray-500">Знижки: {user.discounts}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Прості підписки */}
      <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
        <h2 className="flex items-center gap-2 border-b border-gray-200 px-4 py-3 text-lg font-semibold text-gray-900 sm:px-6">
          <CreditCard className="h-5 w-5" />
          Прості підписки ({simpleSubscriptions.length})
        </h2>
        {simpleSubscriptions.length === 0 ? (
          <div className="p-6 text-center text-gray-500">Немає простих підписок</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-[400px] divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">ID</th>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Товар</th>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Ціна</th>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Початок — Кінець</th>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Статус</th>
                  <th className="px-3 py-2 text-right text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Дії</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {simpleSubscriptions.map((s) => (
                  <tr key={`s-${s.id}`} className="hover:bg-gray-50">
                    <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-900 sm:px-4 sm:py-3">{s.id}</td>
                    <td className="px-3 py-2 text-sm text-gray-900 sm:px-4 sm:py-3">{s.product_name ?? "—"}</td>
                    <td className="whitespace-nowrap px-3 py-2 text-sm sm:px-4 sm:py-3">{s.price} ₴</td>
                    <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-600 sm:px-4 sm:py-3">
                      {formatDate(s.start_date)} — {formatDate(s.end_date)}
                    </td>
                    <td className="whitespace-nowrap px-3 py-2 sm:px-4 sm:py-3">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${s.status === "active" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"}`}>
                        {s.status ?? "—"}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-3 py-2 text-right sm:px-4 sm:py-3">
                      <Link href={`/admin/subscriptions/simple/${s.id}`} className="text-sm text-violet-600 hover:underline">
                        Детальніше
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Рекуррентні підписки */}
      <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
        <h2 className="flex items-center gap-2 border-b border-gray-200 px-4 py-3 text-lg font-semibold text-gray-900 sm:px-6">
          <CreditCard className="h-5 w-5" />
          Рекуррентні підписки ({recurringSubscriptions.length})
        </h2>
        {recurringSubscriptions.length === 0 ? (
          <div className="p-6 text-center text-gray-500">Немає рекуррентних підписок</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-[400px] divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">ID</th>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Товар</th>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Ціна / міс.</th>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Наступний платіж</th>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Статус</th>
                  <th className="px-3 py-2 text-right text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Дії</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {recurringSubscriptions.map((r) => (
                  <tr key={`r-${r.id}`} className="hover:bg-gray-50">
                    <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-900 sm:px-4 sm:py-3">{r.id}</td>
                    <td className="px-3 py-2 text-sm text-gray-900 sm:px-4 sm:py-3">{r.product_name ?? "—"}</td>
                    <td className="whitespace-nowrap px-3 py-2 text-sm sm:px-4 sm:py-3">{r.price} ₴</td>
                    <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-600 sm:px-4 sm:py-3">{formatDate(r.next_payment_date)}</td>
                    <td className="whitespace-nowrap px-3 py-2 sm:px-4 sm:py-3">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${r.status === "active" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"}`}>
                        {r.status ?? "—"}
                      </span>
                      {r.payment_failures > 0 && <span className="ml-1 text-xs text-red-600">({r.payment_failures})</span>}
                    </td>
                    <td className="whitespace-nowrap px-3 py-2 text-right sm:px-4 sm:py-3">
                      <Link href={`/admin/subscriptions/recurring/${r.id}`} className="text-sm text-violet-600 hover:underline">
                        Детальніше
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Одноразові платежі */}
      <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
        <h2 className="flex items-center gap-2 border-b border-gray-200 px-4 py-3 text-lg font-semibold text-gray-900 sm:px-6">
          <Receipt className="h-5 w-5" />
          Одноразові платежі ({payments.length})
        </h2>
        {payments.length === 0 ? (
          <div className="p-6 text-center text-gray-500">Немає одноразових платежів</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-[400px] divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Дата</th>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Сума</th>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Тип</th>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Статус</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {payments.map((p, i) => (
                  <tr key={`p-${p.payment_id ?? i}`} className="hover:bg-gray-50">
                    <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-600 sm:px-4 sm:py-3">{formatDateTime(p.created_at)}</td>
                    <td className="whitespace-nowrap px-3 py-2 text-sm font-medium text-gray-900 sm:px-4 sm:py-3">{p.amount} ₴</td>
                    <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-600 sm:px-4 sm:py-3">{p.payment_type ?? "—"}</td>
                    <td className="whitespace-nowrap px-3 py-2 sm:px-4 sm:py-3">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${p.status === "success" ? "bg-green-100 text-green-700" : p.status === "pending" ? "bg-amber-100 text-amber-700" : "bg-gray-100 text-gray-600"}`}>
                        {p.status ?? "—"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Платежі по підписках */}
      <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
        <h2 className="flex items-center gap-2 border-b border-gray-200 px-4 py-3 text-lg font-semibold text-gray-900 sm:px-6">
          <Receipt className="h-5 w-5" />
          Платежі по підписках ({subPayments.length})
        </h2>
        {subPayments.length === 0 ? (
          <div className="p-6 text-center text-gray-500">Немає платежів по підписках</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-[360px] divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Дата</th>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Сума</th>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Підписка ID</th>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Статус</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {subPayments.map((sp) => (
                  <tr key={`sp-${sp.id}`} className="hover:bg-gray-50">
                    <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-600 sm:px-4 sm:py-3">{formatDateTime(sp.payment_date)}</td>
                    <td className="whitespace-nowrap px-3 py-2 text-sm font-medium text-gray-900 sm:px-4 sm:py-3">{sp.amount} ₴</td>
                    <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-600 sm:px-4 sm:py-3">
                      <Link href={`/admin/subscriptions/recurring/${sp.subscription_id}`} className="text-violet-600 hover:underline">
                        #{sp.subscription_id}
                      </Link>
                    </td>
                    <td className="whitespace-nowrap px-3 py-2 sm:px-4 sm:py-3">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${sp.status === "success" ? "bg-green-100 text-green-700" : sp.status === "failed" ? "bg-red-100 text-red-700" : "bg-gray-100 text-gray-600"}`}>
                        {sp.status ?? "—"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
