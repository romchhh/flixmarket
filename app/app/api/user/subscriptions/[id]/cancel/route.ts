import { NextRequest, NextResponse } from "next/server";
import { validateInitData, getTelegramUserIdFromInitData } from "@/lib/telegram";
import {
  getUserByTelegramId,
  cancelUserSubscription,
  getSubscriptionByIdAndUser,
  getRecurringSubscriptionByIdAndUser,
  cancelRecurringSubscription,
} from "@/lib/db";
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

  let productName: string | null = null;

  const sub = getSubscriptionByIdAndUser(subscriptionId, telegramUserId);
  const cancelledSimple = cancelUserSubscription(subscriptionId, telegramUserId);
  if (cancelledSimple && sub) {
    productName = sub.product_name;
  }

  if (!cancelledSimple) {
    const recSub = getRecurringSubscriptionByIdAndUser(subscriptionId, telegramUserId);
    const cancelledRecurring = cancelRecurringSubscription(subscriptionId, telegramUserId);
    if (cancelledRecurring && recSub) {
      productName = recSub.product_name;
    }
    if (!cancelledRecurring) {
      return NextResponse.json(
        { error: "Subscription not found or already cancelled", code: "not_found" },
        { status: 404 }
      );
    }
  }

  await TelegramNotify.sendSubscriptionCancelled(
    telegramUserId,
    user.user_name ?? null,
    productName ?? "—"
  );

  return NextResponse.json({ success: true });
}
