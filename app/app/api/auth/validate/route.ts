import { NextRequest, NextResponse } from "next/server";
import { validateInitData, getTelegramUserIdFromInitData } from "@/lib/telegram";

export async function POST(request: NextRequest) {
  const initData = request.headers.get("x-telegram-init-data") ?? request.nextUrl.searchParams.get("initData") ?? "";
  if (!initData) {
    return NextResponse.json({ ok: false, error: "Missing init data" }, { status: 400 });
  }
  if (!validateInitData(initData)) {
    return NextResponse.json({ ok: false, error: "Invalid init data" }, { status: 401 });
  }
  const telegramUserId = getTelegramUserIdFromInitData(initData);
  if (!telegramUserId) {
    return NextResponse.json({ ok: false, error: "No user in init data" }, { status: 401 });
  }
  return NextResponse.json({ ok: true, telegram_user_id: telegramUserId });
}
