import { NextRequest, NextResponse } from "next/server";
import { getAdminSession } from "@/lib/admin-auth";
import { getAdminFinance } from "@/lib/db";

export async function GET(request: NextRequest) {
  const ok = await getAdminSession();
  if (!ok) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const { searchParams } = new URL(request.url);
  let fromDate = searchParams.get("from") ?? "";
  let toDate = searchParams.get("to") ?? "";

  if (!fromDate || !toDate) {
    const today = new Date().toISOString().slice(0, 10);
    fromDate = fromDate || today;
    toDate = toDate || today;
  }

  if (fromDate > toDate) [fromDate, toDate] = [toDate, fromDate];

  try {
    const data = getAdminFinance(fromDate, toDate);
    return NextResponse.json(data);
  } catch (e) {
    console.error("Finance API error:", e);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}
