import { NextResponse } from "next/server";
import { getProductsPreview } from "@/lib/db";
import { productPhotoToUrl } from "@/lib/media";

export async function GET() {
  const products = getProductsPreview(24).map((p) => ({
    ...p,
    product_photo: productPhotoToUrl(p.product_photo),
  }));
  return NextResponse.json(products);
}
