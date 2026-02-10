/**
 * Converts stored file path (e.g. Content/products/xxx.jpg) to URL for marketplace.
 */
export function productPhotoToUrl(photoPath: string | null): string | null {
  if (!photoPath || !photoPath.trim()) return null;
  const base = "Content/products/";
  const name = photoPath.startsWith(base)
    ? photoPath.slice(base.length)
    : photoPath.replace(/^.*[/\\]/, "");
  return name ? `/api/media/products/${encodeURIComponent(name)}` : null;
}

/**
 * Converts stored category image path to URL for marketplace.
 */
export function categoryPhotoToUrl(photoPath: string | null): string | null {
  if (!photoPath || !photoPath.trim()) return null;
  const base = "Content/categories/";
  const name = photoPath.startsWith(base)
    ? photoPath.slice(base.length)
    : photoPath.replace(/^.*[/\\]/, "");
  return name ? `/api/media/categories/${encodeURIComponent(name)}` : null;
}
