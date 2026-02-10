import { NextResponse } from "next/server";
import { getProductTypes } from "@/lib/db";
import { categoryPhotoToUrl } from "@/lib/media";

export async function GET() {
  const types = getProductTypes().map((t) => ({
    catalog_id: t.catalog_id,
    product_type: t.product_type,
    catalog_photo: categoryPhotoToUrl(t.catalog_photo),
  }));
  return NextResponse.json(types);
}
