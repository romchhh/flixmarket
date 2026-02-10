"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAdminToast } from "@/components/contexts/AdminToastContext";
import { ImageDropzone } from "@/components/admin/ImageDropzone";

export default function AddCategoryPage() {
  const router = useRouter();
  const toast = useAdminToast();
  const [productType, setProductType] = useState("");
  const [imagePath, setImagePath] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const name = productType.trim();
    if (!name) {
      setError("Введіть назву категорії");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/admin/categories", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_type: name, image_path: imagePath }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Помилка створення");
      toast.show("Категорію створено", "success");
      router.push("/admin/categories");
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
        <Link href="/admin/categories" className="text-violet-600 hover:underline">
          Категорії
        </Link>
        <span>/</span>
        <span>Додати</span>
      </div>
      <h1 className="text-2xl font-bold text-gray-900">Додати категорію</h1>
      <form onSubmit={handleSubmit} className="max-w-xl space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Назва категорії *</label>
          <input
            type="text"
            value={productType}
            onChange={(e) => setProductType(e.target.value)}
            required
            className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20"
            placeholder="Наприклад: Підписки"
          />
        </div>
        <ImageDropzone
          type="category"
          value={imagePath}
          onChange={(path) => { setImagePath(path); if (path) toast.show("Зображення завантажено", "success"); }}
          onUploadingChange={setUploading}
          disabled={uploading}
          label="Зображення категорії (перетягніть або натисніть)"
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
          <Link
            href="/admin/categories"
            className="rounded-lg border border-gray-300 px-4 py-2.5 text-sm"
          >
            Скасувати
          </Link>
        </div>
      </form>
    </div>
  );
}
