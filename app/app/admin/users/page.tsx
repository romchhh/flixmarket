"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAdminToast } from "@/components/contexts/AdminToastContext";
import { Info } from "lucide-react";

type User = {
  id: number;
  user_id: number;
  user_name: string | null;
  ref_id: number | null;
  join_date: string | null;
  discounts: number;
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

export default function AdminUsersPage() {
  const [list, setList] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const limit = 20;
  const toast = useAdminToast();

  useEffect(() => {
    setLoading(true);
    fetch(`/api/admin/users?limit=${limit}&offset=${page * limit}`)
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => setList(Array.isArray(data) ? data : []))
      .finally(() => setLoading(false));
  }, [page]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900 sm:text-2xl">Користувачі</h1>
        <p className="mt-1 text-sm text-gray-500">Список користувачів бота та маркетплейсу</p>
      </div>

      <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Завантаження…</div>
        ) : list.length === 0 ? (
          <div className="p-8 text-center text-gray-500">Немає користувачів</div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-[640px] divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">ID</th>
                    <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Telegram ID</th>
                    <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Ім'я</th>
                    <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Реферал</th>
                    <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Дата реєстрації</th>
                    <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Знижки</th>
                    <th className="px-3 py-2 text-right text-xs font-medium uppercase text-gray-500 sm:px-4 sm:py-3">Дії</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {list.map((u) => (
                    <tr key={u.id} className="hover:bg-gray-50">
                      <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-900 sm:px-4 sm:py-3">{u.id}</td>
                      <td className="whitespace-nowrap px-3 py-2 text-sm font-mono text-gray-600 sm:px-4 sm:py-3">{u.user_id}</td>
                      <td className="px-3 py-2 text-sm text-gray-900 sm:px-4 sm:py-3">{u.user_name ?? "—"}</td>
                      <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-600 sm:px-4 sm:py-3">{u.ref_id ?? "—"}</td>
                      <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-600 sm:px-4 sm:py-3">{formatDate(u.join_date)}</td>
                      <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-600 sm:px-4 sm:py-3">{u.discounts}</td>
                      <td className="whitespace-nowrap px-3 py-2 text-right sm:px-4 sm:py-3">
                        <Link
                          href={`/admin/users/${u.id}`}
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
            <div className="flex flex-wrap items-center justify-between gap-2 border-t border-gray-200 px-3 py-2 sm:px-4 sm:py-3">
              <p className="text-sm text-gray-500">
                Сторінка {page + 1}
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={page === 0}
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm disabled:opacity-50"
                >
                  Назад
                </button>
                <button
                  type="button"
                  disabled={list.length < limit}
                  onClick={() => setPage((p) => p + 1)}
                  className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm disabled:opacity-50"
                >
                  Далі
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
