import { NextRequest, NextResponse } from "next/server";
import path from "node:path";
import fs from "node:fs";

const PROJECT_ROOT = path.join(process.cwd(), "..");
const PRODUCTS_DIR = path.join(PROJECT_ROOT, "bot", "Content", "products");

export async function GET(
  _request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  const pathSegments = params.path ?? [];
  const filename = pathSegments[pathSegments.length - 1];
  if (!filename || filename.includes("..")) {
    return NextResponse.json({ error: "Bad request" }, { status: 400 });
  }

  const filePath = path.join(PRODUCTS_DIR, ...pathSegments);
  if (!filePath.startsWith(PRODUCTS_DIR)) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  try {
    const stat = fs.statSync(filePath);
    if (!stat.isFile()) {
      return NextResponse.json({ error: "Not found" }, { status: 404 });
    }
    const etag = `"${stat.mtimeMs}-${stat.size}"`;
    const ifNoneMatch = _request.headers.get("if-none-match");
    if (ifNoneMatch === etag || ifNoneMatch === `W/${etag}`) {
      return new NextResponse(null, { status: 304, headers: { "Cache-Control": "public, max-age=31536000, immutable", ETag: etag } });
    }
    const ext = path.extname(filename).toLowerCase();
    const contentType =
      ext === ".png"
        ? "image/png"
        : ext === ".gif"
          ? "image/gif"
          : ext === ".webp"
            ? "image/webp"
            : "image/jpeg";
    const buffer = fs.readFileSync(filePath);
    return new NextResponse(buffer, {
      headers: {
        "Content-Type": contentType,
        "Cache-Control": "public, max-age=31536000, immutable",
        ETag: etag,
        "Last-Modified": stat.mtime.toUTCString(),
      },
    });
  } catch {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }
}
