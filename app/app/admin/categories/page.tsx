"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAdminToast } from "@/components/contexts/AdminToastContext";

type Category = { catalog_id: number; product_type: string; catalog_photo: string | null };

export default function AdminCategoriesPage() {
  const [list, setList] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const toast = useAdminToast();

  useEffect(() => {
    fetch("/api/admin/categories")
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => setList(Array.isArray(data) ? data : []))
      .finally(() => setLoading(false));
  }, []);

  const handleDelete = async (catalogId: number, productType: string) => {
    if (!confirm(`Видалити категорію «${productType}» і всі товари в ній?`)) return;
    const res = await fetch(`/api/admin/categories?catalog_id=${catalogId}`, { method: "DELETE" });
    if (res.ok) {
      setList((prev) => prev.filter((c) => c.catalog_id !== catalogId));
      toast.show("Категорію видалено", "success");
    } else {
      toast.show("Помилка видалення", "error");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-xl font-bold text-gray-900 sm:text-2xl">Категорії</h1>
        <Link
          href="/admin/categories/add"
          className="w-fit rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-700"
        >
          Додати категорію
        </Link>
      </div>
      {loading ? (
        <p className="text-gray-500">Завантаження…</p>
      ) : list.length === 0 ? (
        <p className="text-gray-500">Немає категорій.</p>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white">
          <table className="min-w-[400px] divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 sm:px-4 sm:py-3">ID</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 sm:px-4 sm:py-3">Назва</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 sm:px-4 sm:py-3">Зображення</th>
                <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 sm:px-4 sm:py-3">Дії</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {list.map((c) => (
                <tr key={c.catalog_id}>
                  <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-900 sm:px-4 sm:py-3">{c.catalog_id}</td>
                  <td className="px-3 py-2 text-sm text-gray-900 sm:px-4 sm:py-3">{c.product_type}</td>
                  <td className="px-3 py-2 sm:px-4 sm:py-3">
                    {c.catalog_photo ? (
                      <img
                        src={c.catalog_photo}
                        alt=""
                        className="h-10 w-10 rounded object-cover"
                      />
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                  </td>
                  <td className="whitespace-nowrap px-3 py-2 text-right text-sm sm:px-4 sm:py-3">
                    <Link
                      href={`/admin/categories/${c.catalog_id}/edit`}
                      className="text-violet-600 hover:underline"
                    >
                      Редагувати
                    </Link>
                    {" · "}
                    <button
                      type="button"
                      onClick={() => handleDelete(c.catalog_id, c.product_type)}
                      className="text-red-600 hover:underline"
                    >
                      Видалити
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
