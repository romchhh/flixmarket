/**
 * Відправка повідомлень у Telegram-групу адміна (як у боті при створенні/скасуванні підписок).
 * Єдина система: бот і міні-додаток використовують одну групу (ADMIN_CHAT_ID).
 */

const BOT_TOKEN = process.env.BOT_TOKEN ?? "";
const ADMIN_CHAT_ID = process.env.ADMIN_CHAT_ID ?? "";

/** Посилання на канал (як у боті — get_channel_keyboard). */
const CHANNEL_URL = "https://t.me/+N99gG8vIUYVkNGJi";

/** Inline-клавіатура з кнопкою «Підписатися на канал» для повідомлень користувачу після оплати. */
function getChannelReplyMarkup(): { inline_keyboard: Array<Array<{ text: string; url: string }>> } {
  return {
    inline_keyboard: [[{ text: "Підписатися на канал", url: CHANNEL_URL }]],
  };
}

const TELEGRAM_API = "https://api.telegram.org";

function formatAdminUserLine(userId: number, username: string | null): string {
  if (username && username.trim()) {
    return `Користувач: @${username} (ID: <code>${userId}</code>)`;
  }
  return `Користувач: ID <code>${userId}</code> (прихований профіль)`;
}

function formatAdminReferralLine(
  refId: number | null,
  refUsername: string | null,
  creditAmount: number
): string {
  if (!refId || creditAmount <= 0) return "";
  const refDisplay =
    refUsername && refUsername.trim()
      ? `@${refUsername} (ID: <code>${refId}</code>)`
      : `ID <code>${refId}</code> (прихований профіль)`;
  return `\n✨ Рефералу ${refDisplay} нараховано: <b>${creditAmount.toFixed(2)} ₴</b>`;
}

function monthsWord(months: number): string {
  if (months === 1) return "місяць";
  if (months >= 2 && months <= 4) return "місяці";
  return "місяців";
}

/** Текст адміну «Нова підписка!» (як у боті). */
export function getAdminNewSubscriptionText(
  paymentId: string,
  userId: number,
  username: string | null,
  productName: string,
  amount: number,
  months: number,
  refId: number | null,
  refUsername: string | null,
  creditAmount: number
): string {
  const m = monthsWord(months);
  return (
    `💰 <b>Нова підписка!</b>\n\n` +
    `ID платежу: <code>${paymentId}</code>\n` +
    `Тип: 📅 Підписка\n` +
    `${formatAdminUserLine(userId, username)}\n` +
    `Товар: ${productName}\n` +
    `Сума: ${amount} UAH\n` +
    `Термін: ${months} ${m}` +
    formatAdminReferralLine(refId, refUsername, creditAmount)
  );
}

/** Текст адміну «Нова оплата!» (одноразова), як у боті. */
export function getAdminNewOneTimeText(
  invoiceId: string,
  userId: number,
  username: string | null,
  productName: string,
  amount: number,
  months: number,
  endDateStr: string,
  refId: number | null,
  refUsername: string | null,
  creditAmount: number
): string {
  return (
    `💰 <b>Нова оплата!</b>\n\n` +
    `ID платежу: <code>${invoiceId}</code>\n` +
    `Тип: 💳 Одноразова оплата\n` +
    `${formatAdminUserLine(userId, username)}\n` +
    `Товар: ${productName}\n` +
    `Сума: ${amount} UAH\n` +
    `Термін: ${months} міс.\n` +
    `Активна до: ${endDateStr}` +
    formatAdminReferralLine(refId, refUsername, creditAmount)
  );
}

/**
 * Відправити довільний HTML-повідомлення в групу адміна.
 */
export async function sendToAdmin(text: string): Promise<boolean> {
  if (!BOT_TOKEN || !ADMIN_CHAT_ID) return false;
  const chatId = ADMIN_CHAT_ID.trim();
  if (!chatId) return false;
  try {
    const res = await fetch(
      `${TELEGRAM_API}/bot${BOT_TOKEN}/sendMessage`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_id: chatId,
          text,
          parse_mode: "HTML",
          disable_web_page_preview: true,
        }),
      }
    );
    return res.ok;
  } catch {
    return false;
  }
}

/** Відправити повідомлення в групу адміна з inline-кнопкою «Написати користувачу». */
export async function sendToAdminWithKeyboard(
  text: string,
  userId: number
): Promise<boolean> {
  if (!BOT_TOKEN || !ADMIN_CHAT_ID) return false;
  const chatId = ADMIN_CHAT_ID.trim();
  if (!chatId) return false;
  try {
    const res = await fetch(
      `${TELEGRAM_API}/bot${BOT_TOKEN}/sendMessage`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_id: chatId,
          text,
          parse_mode: "HTML",
          disable_web_page_preview: true,
          reply_markup: {
            inline_keyboard: [[{ text: "👤 Написати користувачу", url: `tg://user?id=${userId}` }]],
          },
        }),
      }
    );
    return res.ok;
  } catch {
    return false;
  }
}

/** Текст користувачу: підписка успішно оформлена (як у боті). */
export function getUserSubscriptionSuccessText(
  productName: string,
  months: number,
  amount: number,
  cardInfo?: string
): string {
  const m = monthsWord(months);
  let text =
    `✅ <b>Підписка успішно оформлена!</b>\n\n` +
    `• Підписка: ${productName}\n` +
    `• Термін: ${months} ${m}\n` +
    `• Сума: ${amount} UAH\n\n` +
    `📅 <b>Автоматичне списання:</b> кожні ${months} ${m}\n`;
  if (cardInfo) text += `${cardInfo}\n\n`;
  text +=
    "Зачекайте поки з вами зв'яжеться менеджер для підключення підписки\n\n" +
    `🔔 <b>Для отримання всіх оновлень підпишіться на наш канал:</b>\n`;
  return text;
}

/** Текст користувачу: одноразова оплата успішна (як у боті). */
export function getUserOneTimeSuccessText(
  productName: string,
  months: number,
  amount: number
): string {
  const m = monthsWord(months);
  return (
    `✅ <b>Оплата успішна!</b>\n\n` +
    `• Підписка: ${productName}\n` +
    `• Термін: ${months} ${m}\n` +
    `• Сума: ${amount} UAH\n\n` +
    `💳 <b>Одноразова оплата</b>\n\n` +
    "Зачекайте поки з вами зв'яжеться менеджер для підключення підписки\n\n" +
    `🔔 <b>Для отримання всіх оновлень підпишіться на наш канал:</b>\n`
  );
}

/** Відправити повідомлення користувачу в Telegram (ЛС з ботом). */
export async function sendToUser(
  telegramUserId: number,
  text: string,
  parseMode: "HTML" | "Markdown" = "HTML",
  options?: { withChannelButton?: boolean }
): Promise<boolean> {
  if (!BOT_TOKEN) return false;
  try {
    const body: Record<string, unknown> = {
      chat_id: telegramUserId,
      text,
      parse_mode: parseMode,
      disable_web_page_preview: true,
    };
    if (options?.withChannelButton) {
      body.reply_markup = getChannelReplyMarkup();
    }
    const res = await fetch(
      `${TELEGRAM_API}/bot${BOT_TOKEN}/sendMessage`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }
    );
    return res.ok;
  } catch {
    return false;
  }
}

/**
 * Текст повідомлення адміну: підписка скасована (з міні-додатку або бота).
 */
export function getAdminSubscriptionCancelledText(
  userId: number,
  username: string | null,
  productName: string,
  source: "miniapp" | "bot" | "site" = "miniapp"
): string {
  const userLine = formatAdminUserLine(userId, username);
  const sourceLabel =
    source === "miniapp" ? "📱 Мінідодаток" : source === "site" ? "🌐 Сайт" : "🤖 Бот";
  return (
    `🚫 <b>Підписка скасована</b>\n\n` +
    `📍 Джерело: <b>${sourceLabel}</b>\n` +
    `${userLine}\n` +
    `Підписка: <b>${productName || "—"}</b>\n\n` +
    `💡 Користувач може поновити підписку самостійно`
  );
}

/**
 * Клас-хелпер для повідомлень у групу (створення/скасування підписок).
 */
export class TelegramNotify {
  /**
   * Надіслати в групу адміна повідомлення про скасування підписки (з кнопкою «Написати користувачу», як у боті).
   * Викликати після cancelUserSubscription або cancelRecurringSubscription у міні-додатку.
   */
  static async sendSubscriptionCancelled(
    userId: number,
    username: string | null,
    productName: string
  ): Promise<boolean> {
    const text = getAdminSubscriptionCancelledText(userId, username, productName, "miniapp");
    return sendToAdminWithKeyboard(text, userId);
  }

  /**
   * Надіслати довільне повідомлення в групу адміна.
   */
  static async send(text: string): Promise<boolean> {
    return sendToAdmin(text);
  }
}
