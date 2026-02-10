import { NextRequest, NextResponse } from "next/server";
import { getProductsByCatalog } from "@/lib/db";
import { productPhotoToUrl } from "@/lib/media";

export async function GET(
  _request: NextRequest,
  { params }: { params: { id: string } }
) {
  const id = parseInt(params.id, 10);
  if (Number.isNaN(id)) {
    return NextResponse.json({ error: "Invalid id" }, { status: 400 });
  }
  const products = getProductsByCatalog(id).map((p) => ({
    ...p,
    product_photo: productPhotoToUrl(p.product_photo),
  }));
  return NextResponse.json(products);
}
