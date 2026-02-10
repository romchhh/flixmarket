import { NextRequest, NextResponse } from "next/server";
import {
  getPaymentByInvoiceId,
  updatePaymentStatusByInvoiceId,
  getPaymentsTempDataByLocalPaymentId,
  deletePaymentsTempDataByLocalPaymentId,
  saveUserToken,
  createRecurringSubscription,
  addSubscription,
  getRefIdByUser,
  addPartnerCredit,
  getPartnerReferralPercent,
  getProductById,
  getUsernameByUserId,
} from "@/lib/db";
import { getInvoiceStatus } from "@/lib/monopay";
import {
  sendToAdminWithKeyboard,
  sendToUser,
  getAdminNewSubscriptionText,
  getAdminNewOneTimeText,
  getUserSubscriptionSuccessText,
  getUserOneTimeSuccessText,
} from "@/lib/telegram-notify";

/** Тіло webhook Monobank (як відповідь "Статус рахунку"). */
type WebhookBody = {
  invoiceId?: string;
  status?: string;
  reference?: string;
  walletData?: { cardToken?: string };
  paymentInfo?: { maskedPan?: string; paymentSystem?: string };
};

/**
 * Webhook Monobank: викликається при зміні статусу рахунку.
 * При status=success робимо те саме, що й бот: оновлюємо платіж, реферал, для підписки — зберігаємо токен і створюємо recurring, для one-time — додаємо підписку, відправляємо в групу адміна та користувачу.
 */
export async function POST(request: NextRequest) {
  try {
    const body = (await request.json()) as WebhookBody;
    const invoiceId = body.invoiceId ?? (body as Record<string, unknown>).invoiceId as string | undefined;
    const status = String(body.status ?? (body as Record<string, unknown>).status ?? "").toLowerCase();

    if (!invoiceId) {
      return NextResponse.json({ ok: false, error: "missing invoiceId" }, { status: 400 });
    }

    if (status !== "success") {
      if (status === "failure" || status === "cancelled" || status === "expired") {
        updatePaymentStatusByInvoiceId(invoiceId, status);
      }
      return NextResponse.json({ ok: true });
    }

    const payment = getPaymentByInvoiceId(invoiceId);
    if (!payment) {
      return NextResponse.json({ ok: true });
    }
    if (payment.status === "success") {
      return NextResponse.json({ ok: true });
    }

    const { payment_id, user_id, product_id, months, amount, payment_type } = payment;
    const product = getProductById(product_id);
    const productName = product?.product_name ?? "—";
    const productType = product?.product_type ?? "subscription";
    const username = getUsernameByUserId(user_id);
    const refId = getRefIdByUser(user_id);

    updatePaymentStatusByInvoiceId(invoiceId, "success");

    if (refId) {
      addPartnerCredit(refId, user_id, amount, productName, payment_type ?? "one_time");
    }
    const creditAmount =
      refId && amount > 0
        ? Math.round(amount * (getPartnerReferralPercent() / 100) * 10) / 10
        : 0;
    const refUsername = refId ? getUsernameByUserId(refId) : null;

    if (payment_type === "subscription") {
      const localPaymentId = payment_id ?? invoiceId;
      const tempData = getPaymentsTempDataByLocalPaymentId(localPaymentId);
      const walletId = tempData?.wallet_id;
      let cardToken = body.walletData?.cardToken;
      let paymentInfo = body.paymentInfo;
      if ((!cardToken || !paymentInfo) && walletId) {
        const apiStatus = await getInvoiceStatus(invoiceId);
        if (apiStatus?.status === "success") {
          if (!cardToken) cardToken = apiStatus.walletData?.cardToken;
          if (!paymentInfo) paymentInfo = apiStatus.paymentInfo;
        }
      }
      const maskedCard = paymentInfo?.maskedPan ?? "**** **** **** 1234";
      const cardType = paymentInfo?.paymentSystem ?? "unknown";

      if (walletId && cardToken) {
        saveUserToken(user_id, walletId, cardToken, maskedCard, cardType);
        createRecurringSubscription(user_id, product_id, productName, months, amount, walletId);
        deletePaymentsTempDataByLocalPaymentId(localPaymentId);

        const cardInfo = `💳 <b>Картка:</b> ${maskedCard}${cardType !== "unknown" ? ` (${cardType.toUpperCase()})` : ""}`;
        const userText = getUserSubscriptionSuccessText(productName, months, amount, cardInfo);
        await sendToUser(user_id, userText, "HTML", { withChannelButton: true });

        const adminText = getAdminNewSubscriptionText(
          localPaymentId,
          user_id,
          username,
          productName,
          amount,
          months,
          refId ?? null,
          refUsername,
          creditAmount
        );
        await sendToAdminWithKeyboard(adminText, user_id);
      } else {
        const userFallback =
          `✅ <b>Оплата пройшла успішно</b>\n\n` +
          `• Підписка: ${productName}\n` +
          `• Термін: ${months} міс.\n` +
          `• Сума: ${amount} UAH\n\n` +
          `⚠️ Не вдалося зберегти дані картки для автоматичного продовження (тестова оплата або обмеження платформи).\n\n` +
          `Для продовження підписки зверніться до менеджера.`;
        await sendToUser(user_id, userFallback, "HTML", { withChannelButton: true });

        const adminText =
          `💰 <b>Оплата підписки (без токена)</b>\n\n` +
          `ID: <code>${localPaymentId}</code>\n` +
          `Користувач: ${username ? `@${username}` : ""} (ID: <code>${user_id}</code>)\n` +
          `Товар: ${productName}\n` +
          `Сума: ${amount} UAH, ${months} міс.\n\n` +
          `⚠️ Токен картки не отримано — повторювану підписку в БД не створено.`;
        await sendToAdminWithKeyboard(adminText, user_id);
      }
    } else {
      const startDate = new Date();
      const endDate = new Date();
      endDate.setDate(endDate.getDate() + 30 * months);
      const startStr = startDate.toISOString().slice(0, 10);
      const endStr = endDate.toISOString().slice(0, 10);
      addSubscription(user_id, productType, product_id, productName, amount, startStr, endStr, "active");

      const userText = getUserOneTimeSuccessText(productName, months, amount);
      await sendToUser(user_id, userText, "HTML", { withChannelButton: true });

      const endDateFormatted = endDate.getDate().toString().padStart(2, "0") + "." + (endDate.getMonth() + 1).toString().padStart(2, "0") + "." + endDate.getFullYear();
      const adminText = getAdminNewOneTimeText(
        invoiceId,
        user_id,
        username,
        productName,
        amount,
        months,
        endDateFormatted,
        refId ?? null,
        refUsername,
        creditAmount
      );
      await sendToAdminWithKeyboard(adminText, user_id);
    }

    return NextResponse.json({ ok: true });
  } catch (e) {
    console.error("[mono/webhook]", e);
    return NextResponse.json({ ok: false }, { status: 500 });
  }
}
