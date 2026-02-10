/**
 * Monobank API: створення інвойсів для оплати (як у Telegram-боті).
 * Після оплати статус перевіряє бот (check_pending_payments), створює підписку та надсилає в групу.
 */

const MONO_HOST = "https://api.monobank.ua/";
const XTOKEN = process.env.XTOKEN ?? "";

function getRedirectUrl(): string {
  const webApp = process.env.WEB_APP_URL?.trim();
  const bot = process.env.BOT_LINK_FOR_REDIRECT?.trim();
  if (webApp) return webApp;
  if (bot) return bot;
  return "https://t.me/FlixMarketBot";
}

export type CreatePaymentResult = { localPaymentId: string; invoiceId: string; pageUrl: string };
export type CreatePaymentWithTokenizationResult = {
  localPaymentId: string;
  invoiceId: string;
  pageUrl: string;
  walletId: string;
};

/**
 * Створює одноразовий платіж (або перший платіж підписки без токенізації).
 * Як у боті: create_payment().
 */
export async function createPayment(
  userId: number,
  productName: string,
  months: number,
  price: number
): Promise<CreatePaymentResult> {
  if (!XTOKEN) throw new Error("XTOKEN is not configured");
  const localPaymentId = `order_${userId}_${Math.floor(Date.now() / 1000)}`;
  const payload: Record<string, unknown> = {
    amount: Math.round(price * 100),
    ccy: 980,
    description: `Оплата ${productName} на ${months} міс.`,
    orderReference: localPaymentId,
    destination: "Оплата через Flix Market",
    redirectUrl: getRedirectUrl(),
    merchantPaymInfo: {
      basketOrder: [
        {
          name: productName,
          qty: 1,
          sum: Math.round(price * 100),
          code: `prod_${productName.slice(0, 50)}`,
          unit: "шт.",
        },
      ],
    },
  };
  // Webhook не реєструємо — обробка оплат тільки в боті (check_pending_payments)
  const res = await fetch(`${MONO_HOST}api/merchant/invoice/create`, {
    method: "POST",
    headers: { "X-Token": XTOKEN, "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Monobank error: ${res.status} ${text}`);
  }
  const r = (await res.json()) as { invoiceId: string; pageUrl: string };
  return {
    localPaymentId,
    invoiceId: r.invoiceId,
    pageUrl: r.pageUrl,
  };
}

/**
 * Створює платіж з токенізацією картки для повторюваної підписки.
 * Як у боті: create_payment_with_tokenization().
 */
export async function createPaymentWithTokenization(
  userId: number,
  productName: string,
  months: number,
  price: number
): Promise<CreatePaymentWithTokenizationResult> {
  if (!XTOKEN) throw new Error("XTOKEN is not configured");
  const localPaymentId = `subscription_${userId}_${Math.floor(Date.now() / 1000)}`;
  const walletId = `wallet_${userId}_${Math.random().toString(36).slice(2, 10)}`;
  const payload = {
    amount: Math.round(price * 100),
    ccy: 980,
    merchantPaymInfo: {
      reference: localPaymentId,
      destination: `Підписка на ${productName}`,
      comment: `Підписка на ${productName} на ${months} міс.`,
      customerEmails: [],
      discounts: [],
      basketOrder: [
        {
          name: productName,
          qty: 1,
          sum: Math.round(price * 100),
          total: Math.round(price * 100),
          icon: null,
          unit: "шт.",
          code: `sub_${productName.slice(0, 30)}`,
          barcode: null,
          header: null,
          footer: null,
          tax: [],
          uktzed: null,
          discounts: [],
        },
      ],
    },
    redirectUrl: getRedirectUrl(),
    // webHookUrl не вказуємо — обробка тільки в боті
    validity: 3600,
    paymentType: "debit",
    saveCardData: {
      saveCard: true,
      walletId,
    },
  };
  const res = await fetch(`${MONO_HOST}api/merchant/invoice/create`, {
    method: "POST",
    headers: { "X-Token": XTOKEN, "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Monobank error: ${res.status} ${text}`);
  }
  const r = (await res.json()) as { invoiceId: string; pageUrl: string };
  return {
    localPaymentId,
    invoiceId: r.invoiceId,
    pageUrl: r.pageUrl,
    walletId,
  };
}

/** Відповідь Monobank "Статус рахунку" (для webhook: якщо в тілі немає walletData — дістаємо звідси). */
export type InvoiceStatusResponse = {
  invoiceId?: string;
  status?: string;
  walletData?: { cardToken?: string };
  paymentInfo?: { maskedPan?: string; paymentSystem?: string };
};

/**
 * Отримати повний статус інвойсу з Monobank (walletData.cardToken, paymentInfo).
 * Потрібно для підписки, коли webhook не присилає walletData в тілі.
 */
export async function getInvoiceStatus(invoiceId: string): Promise<InvoiceStatusResponse | null> {
  if (!XTOKEN) return null;
  try {
    const res = await fetch(
      `${MONO_HOST}api/merchant/invoice/status?invoiceId=${encodeURIComponent(invoiceId)}`,
      { method: "GET", headers: { "X-Token": XTOKEN } }
    );
    if (!res.ok) return null;
    return (await res.json()) as InvoiceStatusResponse;
  } catch {
    return null;
  }
}
