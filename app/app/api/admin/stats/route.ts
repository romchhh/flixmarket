import { NextResponse } from "next/server";
import { getAdminSession } from "@/lib/admin-auth";
import { getAdminStats } from "@/lib/db";

export async function GET() {
  const ok = await getAdminSession();
  if (!ok) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const stats = getAdminStats();
  return NextResponse.json(stats);
}
