import { NextRequest, NextResponse } from "next/server";
import { getProductById } from "@/lib/db";
import { productPhotoToUrl } from "@/lib/media";

/** Публічний API: один товар за id (без авторизації) */
export async function GET(
  _request: NextRequest,
  context: { params: Promise<{ id: string }> }
) {
  const { id: idParam } = await context.params;
  const id = parseInt(idParam, 10);
  if (!Number.isInteger(id) || id < 1) {
    return NextResponse.json({ error: "Invalid id" }, { status: 400 });
  }
  const product = getProductById(id);
  if (!product) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }
  return NextResponse.json({
    ...product,
    product_photo: productPhotoToUrl(product.product_photo),
  });
}
