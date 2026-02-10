import { NextResponse } from "next/server";
import { getAdminSession } from "@/lib/admin-auth";

export async function GET() {
  const ok = await getAdminSession();
  return NextResponse.json({ authenticated: ok });
}
