import { NextRequest, NextResponse } from "next/server";
import { getAdminSession } from "@/lib/admin-auth";
import { getProductsPreview, createProduct } from "@/lib/db";
import { productPhotoToUrl } from "@/lib/media";
import { isSubscriptionTariffsString } from "@/lib/text";

async function requireAdmin() {
  const ok = await getAdminSession();
  if (!ok) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  return null;
}

export async function GET() {
  const err = await requireAdmin();
  if (err) return err;
  const products = getProductsPreview(1000).map((p) => ({
    ...p,
    product_photo: productPhotoToUrl(p.product_photo),
  }));
  return NextResponse.json(products);
}

export async function POST(request: NextRequest) {
  const err = await requireAdmin();
  if (err) return err;
  try {
    const body = await request.json();
    const catalogId = Number(body.catalog_id);
    const productType = typeof body.product_type === "string" ? body.product_type.trim() : "";
    const productName = typeof body.product_name === "string" ? body.product_name.trim() : "";
    const productDescription =
      typeof body.product_description === "string" ? body.product_description.trim() : null;
    const productPhoto = typeof body.product_photo === "string" ? body.product_photo : null;
    const paymentType = typeof body.payment_type === "string" ? body.payment_type : "subscription";

    if (!Number.isInteger(catalogId) || !productType || !productName) {
      return NextResponse.json(
        { error: "catalog_id, product_type, product_name required" },
        { status: 400 }
      );
    }

    let productPrice: number | string;
    if (paymentType === "subscription" && typeof body.product_price === "string") {
      const trimmed = body.product_price.trim();
      if (!trimmed || !isSubscriptionTariffsString(trimmed)) {
        return NextResponse.json(
          { error: "Для підписки вкажіть тарифи у форматі: 1 - 150, 3 - 400, 12 - 1100" },
          { status: 400 }
        );
      }
      productPrice = trimmed;
    } else {
      const num = Number(body.product_price);
      if (Number.isNaN(num) || num < 0) {
        return NextResponse.json(
          { error: "catalog_id, product_type, product_name, product_price required" },
          { status: 400 }
        );
      }
      productPrice = num;
    }

    const success = createProduct(
      catalogId,
      productType,
      productName,
      productDescription || null,
      productPrice,
      productPhoto,
      paymentType
    );
    if (!success) {
      return NextResponse.json({ error: "Failed to create product" }, { status: 500 });
    }
    return NextResponse.json({ ok: true }, { status: 201 });
  } catch {
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}
