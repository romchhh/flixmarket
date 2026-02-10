/**
 * Видаляє HTML-теги з рядка (наприклад <tg-emoji>, <b> тощо).
 * Текст всередині тегів залишається.
 */
export function stripHtml(str: string | null | undefined): string {
  if (str == null || typeof str !== "string") return "";
  return str.replace(/<[^>]*>/g, "").trim();
}

/**
 * Форматує ціну для відображення.
 * Число → "150 ₴". Рядок тарифів "1 - 150, 3 - 400" → "від 150 ₴". Інший рядок → як є + ₴.
 */
export function formatPriceDisplay(
  value: number | string | null | undefined
): string {
  if (value == null) return "— ₴";
  if (typeof value === "number") {
    if (Number.isNaN(value)) return "— ₴";
    return new Intl.NumberFormat("uk-UA", { style: "decimal" }).format(value) + " ₴";
  }
  const s = String(value).trim();
  if (!s) return "— ₴";
  if (isSubscriptionTariffsString(s)) {
    const card = getSubscriptionCardPriceLabel(s);
    return card ?? (s.includes("₴") ? s : s + " ₴");
  }
  return s.includes("₴") ? s : s + " ₴";
}

/**
 * Короткий опис періодів підписки для бейджа: "1, 3 або 12 міс." або "1 місяць".
 */
export function getSubscriptionPeriodSummary(priceStr: string | null | undefined): string | null {
  const entries = getSubscriptionTariffEntries(priceStr);
  if (entries.length === 0) return null;
  const months = entries.map((e) => e.months);
  if (months.length === 1) return `${months[0]} ${monthWord(months[0])}`;
  if (months.length === 2) return `${months[0]} або ${months[1]} міс.`;
  const last = months.pop();
  return `${months.join(", ")} або ${last} міс.`;
}

function monthWord(months: string): string {
  const m = months.trim();
  if (m === "1") return "місяць";
  if (["2", "3", "4"].includes(m)) return "місяці";
  return "місяців";
}

/**
 * Чи виглядає рядок як тарифи підписки з бота: "1 - 150, 3 - 400, 12 - 1100"
 */
export function isSubscriptionTariffsString(value: string | null | undefined): boolean {
  if (value == null || typeof value !== "string") return false;
  const s = value.trim().replace(/\s*₴\s*$/, "").trim();
  return /^\d+\s*-\s*[\d.]+\s*(,\s*\d+\s*-\s*[\d.]+\s*)*$/.test(s);
}

/**
 * Парсить тарифи підписки "1 - 150, 3 - 400, 12 - 1100" і повертає масив рядків для відображення:
 * ["1 місяць - 150 ₴", "3 місяці - 400 ₴", "12 місяців - 1100 ₴"]
 */
export function formatSubscriptionTariffs(priceStr: string | null | undefined): string[] {
  return getSubscriptionTariffEntries(priceStr).map((e) => e.label);
}

/** Елемент тарифу: months, price (число для посилання), label для кнопки */
export type SubscriptionTariffEntry = { months: string; price: string; label: string };

/**
 * Парсить тарифи підписки і повертає масив { months, price, label } для кнопок і посилань оплати.
 */
export function getSubscriptionTariffEntries(priceStr: string | null | undefined): SubscriptionTariffEntry[] {
  if (priceStr == null || typeof priceStr !== "string") return [];
  const parts = priceStr.split(",").map((p) => p.trim()).filter(Boolean);
  const result: SubscriptionTariffEntry[] = [];
  for (const part of parts) {
    const dash = part.indexOf(" - ");
    let months: string;
    let price: string;
    if (dash === -1) {
      const alt = part.match(/^(\d+)\s*-\s*(.+)$/);
      if (!alt) continue;
      months = alt[1];
      price = alt[2].trim().replace(/\s*₴\s*$/, "");
    } else {
      months = part.slice(0, dash).trim();
      price = part.slice(dash + 3).trim().replace(/\s*₴\s*$/, "");
    }
    result.push({
      months,
      price,
      label: `${months} ${monthWord(months)} - ${price} ₴`,
    });
  }
  return result;
}

/**
 * Для картки товару: якщо це тарифи підписки — повертає "від X ₴" (мінімальна ціна), інакше null.
 */
export function getSubscriptionCardPriceLabel(priceStr: string | null | undefined): string | null {
  const entries = getSubscriptionTariffEntries(priceStr);
  if (entries.length === 0) return null;
  const minPrice = Math.min(...entries.map((e) => parseFloat(e.price) || 0));
  if (Number.isNaN(minPrice)) return null;
  return `від ${new Intl.NumberFormat("uk-UA", { style: "decimal" }).format(minPrice)} ₴`;
}
