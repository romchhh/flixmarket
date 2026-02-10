import { NextRequest, NextResponse } from "next/server";
import { getAdminSession } from "@/lib/admin-auth";
import { getAdminUserDetail } from "@/lib/db";

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const ok = await getAdminSession();
  if (!ok) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const { id } = await params;
  const idNum = parseInt(id, 10);
  if (!Number.isInteger(idNum) || idNum < 1) {
    return NextResponse.json({ error: "Bad request" }, { status: 400 });
  }

  const data = getAdminUserDetail(idNum);
  if (!data) return NextResponse.json({ error: "Not found" }, { status: 404 });

  return NextResponse.json(data);
}
