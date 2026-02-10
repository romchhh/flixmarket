import { NextRequest, NextResponse } from "next/server";
import { getAdminSession } from "@/lib/admin-auth";
import { getAdminSubscriptionDetail } from "@/lib/db";

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ type: string; id: string }> }
) {
  const ok = await getAdminSession();
  if (!ok) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const { type, id } = await params;
  const typeNorm = type === "simple" || type === "recurring" ? type : null;
  const idNum = typeNorm ? parseInt(id, 10) : NaN;

  if (!typeNorm || !Number.isInteger(idNum) || idNum < 1) {
    return NextResponse.json({ error: "Bad request" }, { status: 400 });
  }

  const data = getAdminSubscriptionDetail(typeNorm, idNum);
  if (!data) return NextResponse.json({ error: "Not found" }, { status: 404 });

  return NextResponse.json(data);
}
