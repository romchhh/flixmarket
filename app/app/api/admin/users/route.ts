import { NextRequest, NextResponse } from "next/server";
import { getAdminSession } from "@/lib/admin-auth";
import { getAdminUsers } from "@/lib/db";

export async function GET(request: NextRequest) {
  const ok = await getAdminSession();
  if (!ok) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const { searchParams } = new URL(request.url);
  const limit = Math.min(100, Math.max(1, parseInt(searchParams.get("limit") ?? "20", 10)));
  const offset = Math.max(0, parseInt(searchParams.get("offset") ?? "0", 10));
  const users = getAdminUsers(limit, offset);
  return NextResponse.json(users);
}
