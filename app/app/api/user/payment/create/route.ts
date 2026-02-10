import { NextRequest, NextResponse } from "next/server";
import { validateInitData, getTelegramUserIdFromInitData } from "@/lib/telegram";
import {
  getUserByTelegramId,
  getProductById,
  savePaymentInfo,
  insertPaymentsTempData,
} from "@/lib/db";
import { createPayment, createPaymentWithTokenization } from "@/lib/monopay";
import { stripHtml } from "@/lib/text";
import { getSubscriptionTariffEntries, isSubscriptionTariffsString } from "@/lib/text";

type Body = { productId: number; months: number };

function getPriceForMonths(
  productPrice: number | string,
  paymentType: string,
  months: number
): number {
  const priceStr = typeof productPrice === "string" ? productPrice : String(productPrice);
  if (isSubscriptionTariffsString(priceStr)) {
    const entries = getSubscriptionTariffEntries(priceStr);
    const entry = entries.find((e) => parseInt(e.months, 10) === months);
    if (entry) return parseFloat(entry.price) || 0;
    if (entries.length > 0) return parseFloat(entries[0].price) || 0;
  }
  const num = typeof productPrice === "number" ? productPrice : parseFloat(priceStr);
  return Number.isNaN(num) ? 0 : num;
}

export async function POST(request: NextRequest) {
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

  let body: Body;
  try {
    body = (await request.json()) as Body;
  } catch {
    return NextResponse.json(
      { error: "Invalid JSON", code: "invalid_body" },
      { status: 400 }
    );
  }

  const productId = Number(body.productId);
  const months = Number(body.months) || 1;
  if (!Number.isInteger(productId) || productId < 1 || !Number.isInteger(months) || months < 1) {
    return NextResponse.json(
      { error: "Invalid productId or months", code: "invalid_params" },
      { status: 400 }
    );
  }

  const product = getProductById(productId);
  if (!product) {
    return NextResponse.json(
      { error: "Product not found", code: "not_found" },
      { status: 404 }
    );
  }

  const productName = stripHtml(product.product_name ?? "Товар");
  const price = getPriceForMonths(
    product.product_price as number | string,
    product.payment_type as string,
    months
  );
  if (price <= 0) {
    return NextResponse.json(
      { error: "Invalid price for selected period", code: "invalid_price" },
      { status: 400 }
    );
  }

  const isSubscription =
    product.payment_type === "subscription" || product.payment_type === "recurring";

  try {
    if (isSubscription) {
      const result = await createPaymentWithTokenization(
        telegramUserId,
        productName,
        months,
        price
      );
      insertPaymentsTempData(
        result.invoiceId,
        result.walletId,
        "subscription",
        result.localPaymentId
      );
      savePaymentInfo(
        result.localPaymentId,
        result.invoiceId,
        telegramUserId,
        productId,
        months,
        price,
        "pending",
        "subscription"
      );
      return NextResponse.json({
        pageUrl: result.pageUrl,
        invoiceId: result.invoiceId,
      });
    } else {
      const result = await createPayment(telegramUserId, productName, months, price);
      savePaymentInfo(
        result.localPaymentId,
        result.invoiceId,
        telegramUserId,
        productId,
        months,
        price,
        "pending",
        "one_time"
      );
      return NextResponse.json({
        pageUrl: result.pageUrl,
        invoiceId: result.invoiceId,
      });
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : "Payment creation failed";
    return NextResponse.json(
      { error: message, code: "payment_create_failed" },
      { status: 500 }
    );
  }
}
