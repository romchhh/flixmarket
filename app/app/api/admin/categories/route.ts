import { NextRequest, NextResponse } from "next/server";
import { getAdminSession } from "@/lib/admin-auth";
import {
  getProductTypes,
  getMaxCatalogId,
  addCategory,
  updateCategory,
  deleteCategory,
} from "@/lib/db";
import { categoryPhotoToUrl } from "@/lib/media";

async function requireAdmin() {
  const ok = await getAdminSession();
  if (!ok) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  return null;
}

export async function GET() {
  const err = await requireAdmin();
  if (err) return err;
  const list = getProductTypes().map((t) => ({
    catalog_id: t.catalog_id,
    product_type: t.product_type,
    catalog_photo: categoryPhotoToUrl(t.catalog_photo),
  }));
  return NextResponse.json(list);
}

export async function POST(request: NextRequest) {
  const err = await requireAdmin();
  if (err) return err;
  try {
    const body = await request.json();
    const productType = typeof body.product_type === "string" ? body.product_type.trim() : "";
    const imagePath = typeof body.image_path === "string" ? body.image_path.trim() : null;

    if (!productType) {
      return NextResponse.json({ error: "product_type required" }, { status: 400 });
    }

    const maxId = getMaxCatalogId();
    const catalogId = maxId + 1;
    const success = addCategory(catalogId, productType, imagePath);
    if (!success) {
      return NextResponse.json({ error: "Failed to create category" }, { status: 500 });
    }
    return NextResponse.json({ catalog_id: catalogId, product_type: productType }, { status: 201 });
  } catch {
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}

export async function PUT(request: NextRequest) {
  const err = await requireAdmin();
  if (err) return err;
  try {
    const body = await request.json();
    const catalogId = typeof body.catalog_id === "number" ? body.catalog_id : Number(body.catalog_id);
    const productType = typeof body.product_type === "string" ? body.product_type.trim() : "";
    const imagePath = typeof body.image_path === "string" ? body.image_path.trim() : null;

    if (!Number.isInteger(catalogId) || catalogId < 1 || !productType) {
      return NextResponse.json({ error: "catalog_id and product_type required" }, { status: 400 });
    }

    const success = updateCategory(catalogId, productType, imagePath === "" ? null : imagePath);
    if (!success) {
      return NextResponse.json({ error: "Failed to update category" }, { status: 500 });
    }
    return NextResponse.json({ ok: true });
  } catch {
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}

export async function DELETE(request: NextRequest) {
  const err = await requireAdmin();
  if (err) return err;
  try {
    const { searchParams } = new URL(request.url);
    const catalogId = parseInt(searchParams.get("catalog_id") ?? "", 10);
    if (!Number.isInteger(catalogId) || catalogId < 1) {
      return NextResponse.json({ error: "catalog_id required" }, { status: 400 });
    }
    const success = deleteCategory(catalogId);
    if (!success) {
      return NextResponse.json({ error: "Failed to delete category" }, { status: 500 });
    }
    return NextResponse.json({ ok: true });
  } catch {
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}
