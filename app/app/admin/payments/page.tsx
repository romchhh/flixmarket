"use client";

import { useEffect, useState } from "react";
import { useAdminToast } from "@/components/contexts/AdminToastContext";

type Payment = {
  payment_id: string | null;
  invoice_id: string | null;
  user_id: number;
  product_id: number;
  amount: number;
  status: string | null;
  payment_type: string | null;
  created_at: string | null;
  user_name: string | null;
};

type SubPayment = {
  id: number;
  subscription_id: number;
  user_id: number;
  amount: number;
  payment_date: string | null;
  status: string | null;
  user_name: string | null;
};

function formatDate(s: string | null) {
  if (!s) return "—";
  try {
    return new Date(s).toLocaleString("uk-UA", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
  } catch {
    return s;
  }
}

export default function AdminPaymentsPage() {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [subPayments, setSubPayments] = useState<SubPayment[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"one" | "recurring">("one");
  const toast = useAdminToast();

  useEffect(() => {
    setLoading(true);
    fetch("/api/admin/payments?limit=100")
      .then((r) => (r.ok ? r.json() : { payments: [], subPayments: [] }))
      .then((data) => {
        setPayments(Array.isArray(data.payments) ? data.payments : []);
        setSubPayments(Array.isArray(data.subPayments) ? data.subPayments : []);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900 sm:text-2xl">Платежі</h1>
        <p className="mt-1 text-sm text-gray-500">Одноразові та по підписках</p>
      </div>

      <div className="flex gap-2 border-b border-gray-200">
        <button
          type="button"
          onClick={() => setTab("one")}
          className={`border-b-2 px-4 py-2 text-sm font-medium ${
            tab === "one" ? "border-violet-600 text-violet-600" : "border-transparent text-gray-500"
          }`}
        >
          Одноразові
        </button>
        <button
          type="button"
          onClick={() => setTab("recurring")}
          className={`border-b-2 px-4 py-2 text-sm font-medium ${
            tab === "recurring" ? "border-violet-600 text-violet-600" : "border-transparent text-gray-500"
          }`}
        >
          По підписках
        </button>
      </div>

      <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Завантаження…</div>
        ) : tab === "one" ? (
          payments.length === 0 ? (
            <div className="p-8 text-center text-gray-500">Немає платежів</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-[480px] divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Користувач</th>
                    <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Сума</th>
                    <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Тип</th>
                    <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Дата</th>
                    <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Статус</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {payments.map((p, i) => (
                    <tr key={`p-${p.invoice_id ?? i}`} className="hover:bg-gray-50">
                      <td className="px-3 py-2 text-sm text-gray-600 sm:px-4 sm:py-3">{p.user_name ?? p.user_id}</td>
                      <td className="whitespace-nowrap px-3 py-2 text-sm font-medium text-gray-900 sm:px-4 sm:py-3">{p.amount} ₴</td>
                      <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-600 sm:px-4 sm:py-3">{p.payment_type ?? "—"}</td>
                      <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-600 sm:px-4 sm:py-3">{formatDate(p.created_at)}</td>
                      <td className="whitespace-nowrap px-3 py-2 sm:px-4 sm:py-3">
                        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                          p.status === "success" ? "bg-green-100 text-green-700" : p.status === "pending" ? "bg-amber-100 text-amber-700" : "bg-gray-100 text-gray-600"
                        }`}>
                          {p.status ?? "—"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        ) : subPayments.length === 0 ? (
          <div className="p-8 text-center text-gray-500">Немає платежів по підписках</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-[400px] divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Користувач</th>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Сума</th>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Дата</th>
                  <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Статус</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {subPayments.map((sp) => (
                  <tr key={`sp-${sp.id}`} className="hover:bg-gray-50">
                    <td className="px-3 py-2 text-sm text-gray-600 sm:px-4 sm:py-3">{sp.user_name ?? sp.user_id}</td>
                    <td className="whitespace-nowrap px-3 py-2 text-sm font-medium text-gray-900 sm:px-4 sm:py-3">{sp.amount} ₴</td>
                    <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-600 sm:px-4 sm:py-3">{formatDate(sp.payment_date)}</td>
                    <td className="whitespace-nowrap px-3 py-2 sm:px-4 sm:py-3">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        sp.status === "success" ? "bg-green-100 text-green-700" : sp.status === "failed" ? "bg-red-100 text-red-700" : "bg-gray-100 text-gray-600"
                      }`}>
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
