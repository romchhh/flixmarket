"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useAdminToast } from "@/components/contexts/AdminToastContext";
import { ImageDropzone } from "@/components/admin/ImageDropzone";
import { isSubscriptionTariffsString } from "@/lib/text";

export default function EditProductPage() {
  const params = useParams();
  const router = useRouter();
  const toast = useAdminToast();
  const id = Number(params.id);
  const [productName, setProductName] = useState("");
  const [productDescription, setProductDescription] = useState("");
  const [productPrice, setProductPrice] = useState("");
  const [productPhoto, setProductPhoto] = useState<string | null>(null);
  const [productPhotoUrl, setProductPhotoUrl] = useState<string | null>(null);
  const [paymentType, setPaymentType] = useState<"subscription" | "one_time">("subscription");
  const [productBadge, setProductBadge] = useState<string>("");
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [fetchLoading, setFetchLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!Number.isInteger(id)) {
      setFetchLoading(false);
      return;
    }
    fetch(`/api/admin/products/${id}`)
      .then((r) => {
        if (!r.ok) throw new Error("Not found");
        return r.json();
      })
      .then((data) => {
        setProductName(data.product_name || "");
        setProductDescription(data.product_description || "");
        setProductPrice(String(data.product_price ?? ""));
        setProductPhoto(null);
        setProductPhotoUrl(data.product_photo || null);
        setPaymentType(data.payment_type === "one_time" ? "one_time" : "subscription");
        setProductBadge(data.product_badge || "");
      })
      .catch(() => setError("Товар не знайдено"))
      .finally(() => setFetchLoading(false));
  }, [id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!productName.trim()) {
      setError("Введіть назву товару");
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
      const res = await fetch(`/api/admin/products/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          product_name: productName.trim(),
          product_description: productDescription.trim() || null,
          product_price: pricePayload,
          ...(productPhoto !== null && { product_photo: productPhoto }),
          payment_type: paymentType,
          product_badge: productBadge || null,
        }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Помилка збереження");
      }
      toast.show("Зміни збережено", "success");
      router.push("/admin/products");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Помилка збереження");
      toast.show("Помилка збереження", "error");
    } finally {
      setLoading(false);
    }
  };

  if (fetchLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Link href="/admin/products" className="text-violet-600 hover:underline">Товари</Link>
          <span>/</span>
          <span>Редагування</span>
        </div>
        <p className="text-gray-500">Завантаження…</p>
      </div>
    );
  }

  if (error && !productName) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Link href="/admin/products" className="text-violet-600 hover:underline">Товари</Link>
        </div>
        <p className="text-red-600">{error}</p>
        <Link href="/admin/products" className="inline-block rounded-lg border border-gray-300 px-4 py-2 text-sm">
          Назад до товарів
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link href="/admin/products" className="text-violet-600 hover:underline">Товари</Link>
        <span>/</span>
        <span>Редагувати: {productName || id}</span>
      </div>
      <h1 className="text-2xl font-bold text-gray-900">Редагувати товар</h1>
      <form onSubmit={handleSubmit} className="max-w-xl space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Назва товару *</label>
          <input
            type="text"
            value={productName}
            onChange={(e) => setProductName(e.target.value)}
            required
            className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Опис</label>
          <textarea
            value={productDescription}
            onChange={(e) => setProductDescription(e.target.value)}
            rows={3}
            className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20"
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
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">🏷️ Позначка</label>
          <select
            value={productBadge}
            onChange={(e) => setProductBadge(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20"
          >
            <option value="">⬜ Без позначки</option>
            <option value="hot">🔥 Гаряча пропозиція</option>
            <option value="bestseller">⭐ Бестселер</option>
            <option value="new">✨ Нове</option>
          </select>
        </div>
        <ImageDropzone
          type="product"
          value={productPhoto}
          currentPreviewUrl={productPhotoUrl}
          onChange={(path) => { setProductPhoto(path); setProductPhotoUrl(null); if (path) toast.show("Зображення завантажено", "success"); }}
          onUploadingChange={setUploading}
          disabled={uploading}
          label="Фото товару (перетягніть або натисніть для заміни)"
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <div className="flex gap-2">
          <button
            type="submit"
            disabled={loading || uploading}
            className="rounded-lg bg-violet-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-violet-700 disabled:opacity-50"
          >
            {loading ? "Збереження…" : "Зберегти"}
          </button>
          <Link href="/admin/products" className="rounded-lg border border-gray-300 px-4 py-2.5 text-sm">
            Скасувати
          </Link>
        </div>
      </form>
    </div>
  );
}
