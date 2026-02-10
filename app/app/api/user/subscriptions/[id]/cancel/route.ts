import { NextRequest, NextResponse } from "next/server";
import { validateInitData, getTelegramUserIdFromInitData } from "@/lib/telegram";
import { getUserByTelegramId, cancelUserSubscription, getSubscriptionByIdAndUser } from "@/lib/db";
import { TelegramNotify } from "@/lib/telegram-notify";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const initData = request.headers.get("x-telegram-init-data") ?? "";
  if (!initData || !validateInitData(initData)) {
    return NextResponse.json(
      { error: "Unauthorized", code: "open_in_telegram" },
      { status: 401 }
    );
  }

  const telegramUserId = getTelegramUserIdFromInitData(initData);
  if (!telegramUserId) {
    return NextResponse.json(
      { error: "No user", code: "open_in_telegram" },
      { status: 401 }
    );
  }

  const user = getUserByTelegramId(telegramUserId);
  if (!user) {
    return NextResponse.json(
      { error: "User not found", code: "user_not_found" },
      { status: 404 }
    );
  }

  const { id } = await params;
  const subscriptionId = parseInt(id, 10);
  if (!Number.isInteger(subscriptionId) || subscriptionId < 1) {
    return NextResponse.json(
      { error: "Invalid subscription id" },
      { status: 400 }
    );
  }

  const sub = getSubscriptionByIdAndUser(subscriptionId, telegramUserId);
  const cancelled = cancelUserSubscription(subscriptionId, telegramUserId);
  if (!cancelled) {
    return NextResponse.json(
      { error: "Subscription not found or already cancelled", code: "not_found" },
      { status: 404 }
    );
  }

  if (sub) {
    await TelegramNotify.sendSubscriptionCancelled(
      telegramUserId,
      user.user_name ?? null,
      sub.product_name ?? "—"
    );
  }

  return NextResponse.json({ success: true });
}
