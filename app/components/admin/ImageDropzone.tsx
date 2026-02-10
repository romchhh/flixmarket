"use client";

import React, { useRef, useState } from "react";

type ImageDropzoneProps = {
  type: "product" | "category";
  value: string | null;
  currentPreviewUrl?: string | null;
  onChange: (path: string | null) => void;
  onUploadingChange?: (uploading: boolean) => void;
  disabled?: boolean;
  label?: string;
  className?: string;
};

export function ImageDropzone({
  type,
  value,
  currentPreviewUrl,
  onChange,
  onUploadingChange,
  disabled,
  label = "Зображення",
  className = "",
}: ImageDropzoneProps) {
  const [drag, setDrag] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const uploadFile = async (file: File) => {
    if (!file.type.startsWith("image/")) {
      setError("Дозволені лише зображення (JPEG, PNG, GIF, WebP)");
      return;
    }
    setError("");
    onUploadingChange?.(true);
    try {
      const form = new FormData();
      form.set("type", type);
      form.set("file", file);
      const res = await fetch("/api/admin/upload", { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Помилка завантаження");
      onChange(data.path);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Помилка завантаження");
      onChange(null);
    } finally {
      onUploadingChange?.(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDrag(false);
    if (disabled) return;
    const file = e.dataTransfer.files[0];
    if (file) uploadFile(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDrag(true);
  };

  const handleDragLeave = () => setDrag(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadFile(file);
    e.target.value = "";
  };

  const filename = value ? value.replace(/^.*[/\\]/, "") : "";
  const previewUrl = currentPreviewUrl || (filename ? `/api/media/${type === "product" ? "products" : "categories"}/${encodeURIComponent(filename)}` : null);

  return (
    <div className={className}>
      {label && (
        <label className="mb-1 block text-sm font-medium text-gray-700">{label}</label>
      )}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => inputRef.current?.click()}
        className={`relative flex min-h-[160px] cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed transition-colors ${
          drag ? "border-violet-500 bg-violet-50" : "border-gray-300 bg-gray-50 hover:border-gray-400 hover:bg-gray-100"
        } ${disabled ? "pointer-events-none opacity-60" : ""}`}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/gif,image/webp"
          onChange={handleFileChange}
          disabled={disabled}
          className="hidden"
        />
        {previewUrl ? (
          <div className="relative h-full min-h-[160px] w-full overflow-hidden rounded-lg p-2">
            <img
              src={previewUrl}
              alt=""
              className="mx-auto max-h-40 w-auto max-w-full object-contain"
            />
            {!disabled && (
              <p className="mt-2 text-center text-xs text-gray-500">
                Натисніть або перетягніть нове зображення для заміни
              </p>
            )}
          </div>
        ) : (
          <>
            <svg className="h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <p className="mt-2 text-sm text-gray-500">
              Перетягніть сюди або натисніть для вибору
            </p>
            <p className="mt-0.5 text-xs text-gray-400">PNG, JPG, GIF, WebP</p>
          </>
        )}
      </div>
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
      {value && !previewUrl && <p className="mt-1 text-xs text-gray-500">Шлях: {value}</p>}
    </div>
  );
}
