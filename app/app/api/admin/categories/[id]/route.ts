import { NextRequest, NextResponse } from "next/server";
import { getAdminSession } from "@/lib/admin-auth";
import { getProductTypes } from "@/lib/db";
import { categoryPhotoToUrl } from "@/lib/media";

export async function GET(
  _request: NextRequest,
  { params }: { params: { id: string } }
) {
  const ok = await getAdminSession();
  if (!ok) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const catalogId = parseInt(params.id, 10);
  if (!Number.isInteger(catalogId)) {
    return NextResponse.json({ error: "Invalid id" }, { status: 400 });
  }

  const list = getProductTypes();
  const one = list.find((t) => t.catalog_id === catalogId);
  if (!one) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  return NextResponse.json({
    catalog_id: one.catalog_id,
    product_type: one.product_type,
    catalog_photo: categoryPhotoToUrl(one.catalog_photo),
    image_path: one.catalog_photo,
  });
}
