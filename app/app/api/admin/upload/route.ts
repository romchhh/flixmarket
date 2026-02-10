import { NextRequest, NextResponse } from "next/server";
import path from "node:path";
import fs from "node:fs";
import { getAdminSession } from "@/lib/admin-auth";

const PROJECT_ROOT = path.join(process.cwd(), "..");
const PRODUCTS_DIR = path.join(PROJECT_ROOT, "bot", "Content", "products");
const CATEGORIES_DIR = path.join(PROJECT_ROOT, "bot", "Content", "categories");

const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"];

function getExt(mime: string): string {
  if (mime === "image/png") return ".png";
  if (mime === "image/gif") return ".gif";
  if (mime === "image/webp") return ".webp";
  return ".jpg";
}

export async function POST(request: NextRequest) {
  const ok = await getAdminSession();
  if (!ok) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const formData = await request.formData();
    const type = formData.get("type") as string | null; // "product" | "category"
    const file = formData.get("file") as File | null;

    if (!file || !type || !["product", "category"].includes(type)) {
      return NextResponse.json(
        { error: "type (product|category) and file required" },
        { status: 400 }
      );
    }

    const mime = file.type;
    if (!ALLOWED_TYPES.includes(mime)) {
      return NextResponse.json(
        { error: "Allowed: JPEG, PNG, GIF, WebP" },
        { status: 400 }
      );
    }

    const dir = type === "product" ? PRODUCTS_DIR : CATEGORIES_DIR;
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    const ext = getExt(mime);
    const baseName = type === "product" ? "product" : "category";
    const filename = `${baseName}_${Date.now()}${ext}`;
    const filePath = path.join(dir, filename);
    const buffer = Buffer.from(await file.arrayBuffer());
    fs.writeFileSync(filePath, buffer);

    const relativePath = type === "product" ? `Content/products/${filename}` : `Content/categories/${filename}`;
    return NextResponse.json({ path: relativePath, filename });
  } catch (e) {
    console.error("Upload error:", e);
    return NextResponse.json({ error: "Upload failed" }, { status: 500 });
  }
}
