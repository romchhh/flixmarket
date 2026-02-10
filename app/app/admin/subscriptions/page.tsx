"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAdminToast } from "@/components/contexts/AdminToastContext";
import { Info } from "lucide-react";
import { stripHtml } from "@/lib/text";

type SimpleSub = {
  id: number;
  user_id: number;
  product_name: string | null;
  price: number;
  start_date: string | null;
  end_date: string | null;
  status: string | null;
  user_name: string | null;
};

type RecurringSub = {
  id: number;
  user_id: number;
  product_name: string | null;
  months: number;
  price: number;
  next_payment_date: string | null;
  status: string | null;
  payment_failures: number;
  user_name: string | null;
};

function formatDate(s: string | null) {
  if (!s) return "—";
  try {
    return new Date(s).toLocaleDateString("uk-UA", { day: "2-digit", month: "2-digit", year: "numeric" });
  } catch {
    return s;
  }
}

export default function AdminSubscriptionsPage() {
  const [simple, setSimple] = useState<SimpleSub[]>([]);
  const [recurring, setRecurring] = useState<RecurringSub[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"simple" | "recurring">("simple");
  const toast = useAdminToast();

  useEffect(() => {
    setLoading(true);
    fetch("/api/admin/subscriptions?limit=100")
      .then((r) => (r.ok ? r.json() : { simple: [], recurring: [] }))
      .then((data) => {
        setSimple(Array.isArray(data.simple) ? data.simple : []);
        setRecurring(Array.isArray(data.recurring) ? data.recurring : []);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900 sm:text-2xl">Підписки</h1>
        <p className="mt-1 text-sm text-gray-500">Прості та рекуррентні підписки</p>
      </div>

      <div className="flex gap-2 border-b border-gray-200">
        <button
          type="button"
          onClick={() => setTab("simple")}
          className={`border-b-2 px-4 py-2 text-sm font-medium ${
            tab === "simple" ? "border-violet-600 text-violet-600" : "border-transparent text-gray-500"
          }`}
        >
          Прості
        </button>
        <button
          type="button"
          onClick={() => setTab("recurring")}
          className={`border-b-2 px-4 py-2 text-sm font-medium ${
            tab === "recurring" ? "border-violet-600 text-violet-600" : "border-transparent text-gray-500"
          }`}
        >
          Рекуррентні
        </button>
      </div>

      <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Завантаження…</div>
        ) : tab === "simple" ? (
          simple.length === 0 ? (
            <div className="p-8 text-center text-gray-500">Немає простих підписок</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-[600px] divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">ID</th>
                    <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Користувач</th>
                    <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Товар</th>
                    <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Ціна</th>
                    <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Початок / Кінець</th>
                    <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Статус</th>
                    <th className="px-3 py-2 text-right text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Дії</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {simple.map((s) => (
                    <tr key={`s-${s.id}`} className="hover:bg-gray-50">
                      <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-900 sm:px-4 sm:py-3">{s.id}</td>
                      <td className="px-3 py-2 text-sm text-gray-600 sm:px-4 sm:py-3">{s.user_name ?? s.user_id}</td>
                      <td className="px-3 py-2 text-sm text-gray-900 sm:px-4 sm:py-3">{stripHtml(s.product_name ?? "") || "—"}</td>
                      <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-900 sm:px-4 sm:py-3">{s.price} ₴</td>
                      <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-600 sm:px-4 sm:py-3">
                        {formatDate(s.start_date)} — {formatDate(s.end_date)}
                      </td>
                      <td className="whitespace-nowrap px-3 py-2 sm:px-4 sm:py-3">
                        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                          s.status === "active" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"
                        }`}>
                          {s.status ?? "—"}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-3 py-2 text-right sm:px-4 sm:py-3">
                        <Link
                          href={`/admin/subscriptions/simple/${s.id}`}
                          className="inline-flex items-center gap-1 rounded-lg bg-violet-50 px-2.5 py-1.5 text-sm font-medium text-violet-700 hover:bg-violet-100"
                        >
                          <Info className="h-4 w-4" />
                          Детальніше
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        ) : recurring.length === 0 ? (
          <div className="p-8 text-center text-gray-500">Немає рекуррентних підписок</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-[600px] divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">ID</th>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Користувач</th>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Товар</th>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Ціна / міс.</th>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Наступний платіж</th>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Статус</th>
                  <th className="px-3 py-2 text-right text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Дії</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {recurring.map((r) => (
                  <tr key={`r-${r.id}`} className="hover:bg-gray-50">
                    <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-900 sm:px-4 sm:py-3">{r.id}</td>
                    <td className="px-3 py-2 text-sm text-gray-600 sm:px-4 sm:py-3">{r.user_name ?? r.user_id}</td>
                    <td className="px-3 py-2 text-sm text-gray-900 sm:px-4 sm:py-3">{stripHtml(r.product_name ?? "") || "—"}</td>
                    <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-900 sm:px-4 sm:py-3">{r.price} ₴</td>
                    <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-600 sm:px-4 sm:py-3">{formatDate(r.next_payment_date)}</td>
                    <td className="whitespace-nowrap px-3 py-2 sm:px-4 sm:py-3">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        r.status === "active" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"
                      }`}>
                        {r.status ?? "—"}
                      </span>
                      {r.payment_failures > 0 && (
                        <span className="ml-1 text-xs text-red-600">({r.payment_failures} помилок)</span>
                      )}
                    </td>
                    <td className="whitespace-nowrap px-3 py-2 text-right sm:px-4 sm:py-3">
                      <Link
                        href={`/admin/subscriptions/recurring/${r.id}`}
                        className="inline-flex items-center gap-1 rounded-lg bg-violet-50 px-2.5 py-1.5 text-sm font-medium text-violet-700 hover:bg-violet-100"
                      >
                        <Info className="h-4 w-4" />
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
    </div>
  );
}
