import crypto from "node:crypto";
import type { InitDataParsed, TelegramWebAppUser } from "@/types/telegram";

const BOT_TOKEN = process.env.BOT_TOKEN ?? "";

/**
 * Парсинг initData з Telegram Web App (рядок query string).
 * Повертає об'єкт з user (telegram user id, name, username тощо) та hash для перевірки.
 */
export function parseInitData(initData: string): InitDataParsed | null {
  if (!initData || typeof initData !== "string") return null;
  const params = new URLSearchParams(initData);
  const hash = params.get("hash");
  const userStr = params.get("user");
  const auth_date = params.get("auth_date");
  if (!hash || !auth_date) return null;

  const user: TelegramWebAppUser | undefined = userStr
    ? (JSON.parse(decodeURIComponent(userStr)) as TelegramWebAppUser)
    : undefined;

  return {
    user,
    auth_date: parseInt(auth_date, 10),
    hash,
  };
}

/**
 * Перевірка підпису initData (серверна).
 * https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
 */
export function validateInitData(initData: string): boolean {
  if (!BOT_TOKEN || !initData) return false;
  const params = new URLSearchParams(initData);
  const hash = params.get("hash");
  if (!hash) return false;

  params.delete("hash");
  const dataCheckString = [...params.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([k, v]) => `${k}=${v}`)
    .join("\n");

  const secretKey = crypto
    .createHmac("sha256", "WebAppData")
    .update(BOT_TOKEN)
    .digest();
  const calculatedHash = crypto
    .createHmac("sha256", secretKey)
    .update(dataCheckString)
    .digest("hex");

  return calculatedHash === hash;
}

/**
 * Отримати Telegram user id з валідного initData (після validateInitData).
 */
export function getTelegramUserIdFromInitData(initData: string): number | null {
  const parsed = parseInitData(initData);
  return parsed?.user?.id ?? null;
}

/**
 * Отримати дані користувача Telegram з initData (ім'я, прізвище, username).
 */
export function getTelegramUserFromInitData(initData: string): Pick<TelegramWebAppUser, "id" | "first_name" | "last_name" | "username"> | null {
  const parsed = parseInitData(initData);
  if (!parsed?.user) return null;
  const { id, first_name, last_name, username } = parsed.user;
  return { id, first_name, last_name, username };
}
