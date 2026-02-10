import { NextRequest, NextResponse } from "next/server";
import { validateInitData, getTelegramUserIdFromInitData, getTelegramUserFromInitData } from "@/lib/telegram";
import {
  getUserByTelegramId,
  getUserSubscriptions,
  getUserRecurringSubscriptions,
  getUserPaymentsForProfile,
  getRecurringPaymentsForProfile,
  getPartnerBalance,
  getReferralCount,
  getPartnerReferralPercent,
  getReferralsOfPartner,
  getPartnerEarningsHistory,
} from "@/lib/db";
import { productPhotoToUrl } from "@/lib/media";

function daysOnService(joinDate: string | null): number | null {
  if (!joinDate) return null;
  const start = new Date(joinDate);
  const now = new Date();
  const diff = now.getTime() - start.getTime();
  return Math.floor(diff / (24 * 60 * 60 * 1000));
}

export async function GET(request: NextRequest) {
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

  const subscriptionsRaw = getUserSubscriptions(telegramUserId);
  const recurringRaw = getUserRecurringSubscriptions(telegramUserId);
  const payments = getUserPaymentsForProfile(telegramUserId);
  const subscriptionPayments = getRecurringPaymentsForProfile(telegramUserId);

  const subscriptions = subscriptionsRaw.map((s) => ({
    ...s,
    product_photo: productPhotoToUrl(s.product_photo ?? null) ?? null,
  }));
  const recurringSubscriptions = recurringRaw.map((r) => ({
    ...r,
    product_photo: productPhotoToUrl(r.product_photo ?? null) ?? null,
  }));

  const telegramUser = getTelegramUserFromInitData(initData);
  const firstName = telegramUser?.first_name ?? null;
  const lastName = telegramUser?.last_name ?? null;

  const partnerBalance = getPartnerBalance(telegramUserId);
  const referralCount = getReferralCount(telegramUserId);
  const referralPercent = getPartnerReferralPercent();
  const referrals = getReferralsOfPartner(telegramUserId);
  const earningsHistory = getPartnerEarningsHistory(telegramUserId, 20);

  return NextResponse.json({
    ...user,
    firstName,
    lastName,
    subscriptions,
    recurringSubscriptions,
    payments,
    subscriptionPayments,
    daysOnService: daysOnService(user.join_date),
    referral: {
      partnerBalance,
      referralCount,
      referralPercent,
      referrals,
      earningsHistory,
    },
  });
}
