"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAdminToast } from "@/components/contexts/AdminToastContext";
import { Info } from "lucide-react";
import { stripHtml, formatPriceDisplay } from "@/lib/text";

type Product = {
  id: number;
  catalog_id: number;
  product_type: string;
  product_name: string;
  product_price: number | string;
  product_photo: string | null;
  payment_type: string;
};

export default function AdminProductsPage() {
  const [list, setList] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const toast = useAdminToast();

  useEffect(() => {
    fetch("/api/admin/products")
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => setList(Array.isArray(data) ? data : []))
      .finally(() => setLoading(false));
  }, []);

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`Видалити товар «${name}»?`)) return;
    const res = await fetch(`/api/admin/products/${id}`, { method: "DELETE" });
    if (res.ok) {
      setList((prev) => prev.filter((p) => p.id !== id));
      toast.show("Товар видалено", "success");
    } else {
      toast.show("Помилка видалення", "error");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-xl font-bold text-gray-900 sm:text-2xl">Товари</h1>
        <Link
          href="/admin/products/add"
          className="w-fit rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-700"
        >
          Додати товар
        </Link>
      </div>
      {loading ? (
        <p className="text-gray-500">Завантаження…</p>
      ) : list.length === 0 ? (
        <p className="text-gray-500">Немає товарів.</p>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white">
          <table className="min-w-[520px] divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 sm:px-4 sm:py-3">Фото</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 sm:px-4 sm:py-3">Назва</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 sm:px-4 sm:py-3">Категорія</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 sm:px-4 sm:py-3">Ціна</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 sm:px-4 sm:py-3">Оплата</th>
                <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 sm:px-4 sm:py-3">Дії</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {list.map((p) => (
                <tr key={p.id}>
                  <td className="whitespace-nowrap px-3 py-2 sm:px-4 sm:py-3">
                    {p.product_photo ? (
                      <img
                        src={p.product_photo}
                        alt=""
                        className="h-10 w-10 rounded object-cover"
                      />
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-sm text-gray-900 sm:px-4 sm:py-3">{stripHtml(p.product_name)}</td>
                  <td className="px-3 py-2 text-sm text-gray-500 sm:px-4 sm:py-3">{stripHtml(p.product_type)}</td>
                  <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-900 sm:px-4 sm:py-3">{formatPriceDisplay(p.product_price)}</td>
                  <td className="px-3 py-2 text-sm text-gray-500 sm:px-4 sm:py-3">
                    {p.payment_type === "subscription" ? "Підписка" : "Одноразово"}
                  </td>
                  <td className="whitespace-nowrap px-3 py-2 text-right text-sm sm:px-4 sm:py-3">
                    <Link
                      href={`/admin/products/${p.id}`}
                      className="mr-2 inline-flex items-center gap-1 rounded-lg bg-violet-50 px-2 py-1 text-violet-700 hover:bg-violet-100"
                    >
                      <Info className="h-4 w-4" />
                      Детальніше
                    </Link>
                    <Link
                      href={`/admin/products/${p.id}/edit`}
                      className="text-violet-600 hover:underline"
                    >
                      Редагувати
                    </Link>
                    {" · "}
                    <button
                      type="button"
                      onClick={() => handleDelete(p.id, p.product_name)}
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
