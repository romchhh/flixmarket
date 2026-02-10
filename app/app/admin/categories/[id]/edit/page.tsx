"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useAdminToast } from "@/components/contexts/AdminToastContext";
import { ImageDropzone } from "@/components/admin/ImageDropzone";

export default function EditCategoryPage() {
  const params = useParams();
  const router = useRouter();
  const toast = useAdminToast();
  const id = Number(params.id);
  const [productType, setProductType] = useState("");
  const [imagePath, setImagePath] = useState<string | null>(null);
  const [catalogPhotoUrl, setCatalogPhotoUrl] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [fetchLoading, setFetchLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!Number.isInteger(id)) {
      setFetchLoading(false);
      return;
    }
    fetch(`/api/admin/categories/${id}`)
      .then((r) => {
        if (!r.ok) throw new Error("Not found");
        return r.json();
      })
      .then((data) => {
        setProductType(data.product_type || "");
        setImagePath(data.image_path || null);
        setCatalogPhotoUrl(data.catalog_photo || null);
      })
      .catch(() => setError("Категорію не знайдено"))
      .finally(() => setFetchLoading(false));
  }, [id]);

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
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          catalog_id: id,
          product_type: name,
          image_path: imagePath,
        }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Помилка збереження");
      }
      toast.show("Зміни збережено", "success");
      router.push("/admin/categories");
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
          <Link href="/admin/categories" className="text-violet-600 hover:underline">Категорії</Link>
          <span>/</span>
          <span>Редагування</span>
        </div>
        <p className="text-gray-500">Завантаження…</p>
      </div>
    );
  }

  if (error && !productType) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Link href="/admin/categories" className="text-violet-600 hover:underline">Категорії</Link>
        </div>
        <p className="text-red-600">{error}</p>
        <Link href="/admin/categories" className="inline-block rounded-lg border border-gray-300 px-4 py-2 text-sm">
          Назад до категорій
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link href="/admin/categories" className="text-violet-600 hover:underline">Категорії</Link>
        <span>/</span>
        <span>Редагувати: {productType || id}</span>
      </div>
      <h1 className="text-2xl font-bold text-gray-900">Редагувати категорію</h1>
      <form onSubmit={handleSubmit} className="max-w-xl space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Назва категорії *</label>
          <input
            type="text"
            value={productType}
            onChange={(e) => setProductType(e.target.value)}
            required
            className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20"
          />
        </div>
        <ImageDropzone
          type="category"
          value={imagePath}
          currentPreviewUrl={catalogPhotoUrl}
          onChange={(path) => { setImagePath(path); setCatalogPhotoUrl(null); if (path) toast.show("Зображення завантажено", "success"); }}
          onUploadingChange={setUploading}
          disabled={uploading}
          label="Зображення категорії (перетягніть або натисніть для заміни)"
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
          <Link href="/admin/categories" className="rounded-lg border border-gray-300 px-4 py-2.5 text-sm">
            Скасувати
          </Link>
        </div>
      </form>
    </div>
  );
}
