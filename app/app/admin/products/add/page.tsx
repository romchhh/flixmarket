"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAdminToast } from "@/components/contexts/AdminToastContext";
import { ImageDropzone } from "@/components/admin/ImageDropzone";
import { isSubscriptionTariffsString } from "@/lib/text";

type Category = { catalog_id: number; product_type: string };

export default function AddProductPage() {
  const router = useRouter();
  const toast = useAdminToast();
  const [categories, setCategories] = useState<Category[]>([]);
  const [catalogId, setCatalogId] = useState<number | "">("");
  const [productType, setProductType] = useState("");
  const [productName, setProductName] = useState("");
  const [productDescription, setProductDescription] = useState("");
  const [productPrice, setProductPrice] = useState("");
  const [productPhoto, setProductPhoto] = useState<string | null>(null);
  const [paymentType, setPaymentType] = useState<"subscription" | "one_time">("subscription");
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("/api/admin/categories")
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => {
        const arr = Array.isArray(data) ? data : [];
        setCategories(arr);
        if (arr.length > 0 && catalogId === "") {
          setCatalogId(arr[0].catalog_id);
          setProductType(arr[0].product_type);
        }
      });
  }, []);

  useEffect(() => {
    if (catalogId !== "" && categories.length) {
      const c = categories.find((x) => x.catalog_id === catalogId);
      if (c) setProductType(c.product_type);
    }
  }, [catalogId, categories]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!productName.trim()) {
      setError("Введіть назву товару");
      return;
    }
    const catId = Number(catalogId);
    if (!Number.isInteger(catId) || !productType) {
      setError("Оберіть категорію");
      return;
    }
    const trimmedPrice = productPrice.trim();
    if (paymentType === "subscription") {
      if (!trimmedPrice) {
        setError("Введіть тарифи підписки");
        return;
      }
      if (!isSubscriptionTariffsString(trimmedPrice)) {
        setError('Формат тарифів: "1 - 150, 3 - 400, 12 - 1100" (місяці - ціна, через кому)');
        return;
      }
    } else {
      const price = parseFloat(trimmedPrice.replace(",", "."));
      if (Number.isNaN(price) || price < 0) {
        setError("Введіть коректну ціну (число)");
        return;
      }
    }
    setLoading(true);
    setError("");
    const pricePayload = paymentType === "subscription"
      ? trimmedPrice
      : parseFloat(productPrice.replace(",", "."));
    try {
      const res = await fetch("/api/admin/products", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          catalog_id: catId,
          product_type: productType,
          product_name: productName.trim(),
          product_description: productDescription.trim() || null,
          product_price: pricePayload,
          product_photo: productPhoto,
          payment_type: paymentType,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Помилка створення");
      toast.show("Товар створено", "success");
      router.push("/admin/products");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Помилка створення");
      toast.show("Помилка створення", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link href="/admin/products" className="text-violet-600 hover:underline">Товари</Link>
        <span>/</span>
        <span>Додати</span>
      </div>
      <h1 className="text-2xl font-bold text-gray-900">Додати товар</h1>
      <form onSubmit={handleSubmit} className="max-w-xl space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Категорія *</label>
          <select
            value={catalogId}
            onChange={(e) => setCatalogId(e.target.value === "" ? "" : Number(e.target.value))}
            className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20"
          >
            <option value="">Оберіть категорію</option>
            {categories.map((c) => (
              <option key={c.catalog_id} value={c.catalog_id}>
                {c.product_type}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Назва товару *</label>
          <input
            type="text"
            value={productName}
            onChange={(e) => setProductName(e.target.value)}
            required
            className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20"
            placeholder="Назва"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Опис</label>
          <textarea
            value={productDescription}
            onChange={(e) => setProductDescription(e.target.value)}
            rows={3}
            className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20"
            placeholder="Опис товару"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Тип оплати</label>
          <select
            value={paymentType}
            onChange={(e) => setPaymentType(e.target.value as "subscription" | "one_time")}
            className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20"
          >
            <option value="subscription">Підписка</option>
            <option value="one_time">Одноразова оплата</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            {paymentType === "subscription" ? "Тарифи (місяці - ціна, як у боті) *" : "Ціна (₴) *"}
          </label>
          <input
            type="text"
            value={productPrice}
            onChange={(e) => setProductPrice(e.target.value)}
            required
            className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20"
            placeholder={paymentType === "subscription" ? "1 - 150, 3 - 400, 12 - 1100" : "0"}
          />
          {paymentType === "subscription" && (
            <p className="mt-1 text-xs text-gray-500">
              Перше число — кількість місяців, друге — ціна в гривнях. Кілька тарифів через кому.
            </p>
          )}
        </div>
        <ImageDropzone
          type="product"
          value={productPhoto}
          onChange={(path) => { setProductPhoto(path); if (path) toast.show("Зображення завантажено", "success"); }}
          onUploadingChange={setUploading}
          disabled={uploading}
          label="Фото товару (перетягніть або натисніть)"
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <div className="flex gap-2">
          <button
            type="submit"
            disabled={loading || uploading}
            className="rounded-lg bg-violet-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-violet-700 disabled:opacity-50"
          >
            {loading ? "Збереження…" : "Створити"}
          </button>
          <Link href="/admin/products" className="rounded-lg border border-gray-300 px-4 py-2.5 text-sm">
            Скасувати
          </Link>
        </div>
      </form>
    </div>
  );
}
