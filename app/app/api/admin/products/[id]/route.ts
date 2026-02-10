import { NextRequest, NextResponse } from "next/server";
import { getAdminSession } from "@/lib/admin-auth";
import { getProductById, updateProduct, deleteProduct, getProductTypes } from "@/lib/db";
import { productPhotoToUrl } from "@/lib/media";
import { isSubscriptionTariffsString } from "@/lib/text";

async function requireAdmin() {
  const ok = await getAdminSession();
  if (!ok) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  return null;
}

export async function GET(
  _request: NextRequest,
  context: { params: Promise<{ id: string }> }
) {
  const err = await requireAdmin();
  if (err) return err;
  const { id: idParam } = await context.params;
  const id = parseInt(idParam, 10);
  if (!Number.isInteger(id)) {
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

export async function PUT(
  request: NextRequest,
  context: { params: Promise<{ id: string }> }
) {
  const err = await requireAdmin();
  if (err) return err;
  const { id: idParam } = await context.params;
  const id = parseInt(idParam, 10);
  if (!Number.isInteger(id)) {
    return NextResponse.json({ error: "Invalid id" }, { status: 400 });
  }
  try {
    const body = await request.json();
    const data: {
      product_name?: string;
      product_description?: string | null;
      product_price?: number | string;
      product_photo?: string | null;
      payment_type?: string;
      product_badge?: string | null;
      catalog_id?: number;
      product_type?: string;
    } = {};
    if (typeof body.product_name === "string") data.product_name = body.product_name.trim();
    if (body.product_description !== undefined) data.product_description = body.product_description === "" ? null : body.product_description;
    if (body.product_price !== undefined) {
      if (typeof body.product_price === "string" && body.product_price.trim()) {
        const trimmed = body.product_price.trim();
        if (isSubscriptionTariffsString(trimmed)) {
          data.product_price = trimmed;
        } else {
          const num = Number(trimmed.replace(",", "."));
          if (!Number.isNaN(num) && num >= 0) data.product_price = num;
        }
      } else if (typeof body.product_price === "number" && !Number.isNaN(body.product_price) && body.product_price >= 0) {
        data.product_price = body.product_price;
      }
    }
    if (body.product_photo !== undefined) data.product_photo = body.product_photo;
    if (typeof body.payment_type === "string") data.payment_type = body.payment_type;
    if (body.product_badge !== undefined) data.product_badge = body.product_badge === "" ? null : body.product_badge;

    const catalogId = body.catalog_id !== undefined ? Number(body.catalog_id) : undefined;
    if (catalogId !== undefined && Number.isInteger(catalogId) && catalogId >= 1) {
      const types = getProductTypes();
      const cat = types.find((t) => t.catalog_id === catalogId);
      if (cat) {
        data.catalog_id = catalogId;
        data.product_type = cat.product_type;
      }
    }

    const success = updateProduct(id, data);
    if (!success) {
      return NextResponse.json({ error: "Failed to update product" }, { status: 500 });
    }
    return NextResponse.json({ ok: true });
  } catch {
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}

export async function DELETE(
  _request: NextRequest,
  context: { params: Promise<{ id: string }> }
) {
  const err = await requireAdmin();
  if (err) return err;
  const { id: idParam } = await context.params;
  const id = parseInt(idParam, 10);
  if (!Number.isInteger(id)) {
    return NextResponse.json({ error: "Invalid id" }, { status: 400 });
  }
  const success = deleteProduct(id);
  if (!success) {
    return NextResponse.json({ error: "Failed to delete product" }, { status: 500 });
  }
  return NextResponse.json({ ok: true });
}
