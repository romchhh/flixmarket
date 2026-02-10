/**
 * Розрахунок часу до кінця підписки (до кінця дня end_date).
 * end_date: "YYYY-MM-DD"
 */
export function getSubscriptionEndTime(endDate: string): Date {
  return new Date(`${endDate.trim()}T23:59:59`);
}

export function getTimeLeft(endDate: string): {
  ended: boolean;
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
} {
  const end = getSubscriptionEndTime(endDate);
  const now = new Date();
  const diff = end.getTime() - now.getTime();
  if (diff <= 0) {
    return { ended: true, days: 0, hours: 0, minutes: 0, seconds: 0 };
  }
  const seconds = Math.floor((diff / 1000) % 60);
  const minutes = Math.floor((diff / (1000 * 60)) % 60);
  const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  return { ended: false, days, hours, minutes, seconds };
}

/** Формат "X дн. Y год Z хв" або "Закінчилась" */
export function formatTimeLeft(endDate: string): string {
  const t = getTimeLeft(endDate);
  if (t.ended) return "Закінчилась";
  const parts: string[] = [];
  if (t.days > 0) parts.push(`${t.days} дн.`);
  parts.push(`${String(t.hours).padStart(2, "0")} год`);
  parts.push(`${String(t.minutes).padStart(2, "0")} хв`);
  return parts.join(" ");
}

const MONTH_NAMES: Record<number, string> = {
  1: "січня", 2: "лютого", 3: "березня", 4: "квітня", 5: "травня", 6: "червня",
  7: "липня", 8: "серпня", 9: "вересня", 10: "жовтня", 11: "листопада", 12: "грудня",
};

/** Нормалізована дата для відображення: "27 березня 2025" */
export function formatSubscriptionDate(dateStr: string): string {
  const d = new Date(dateStr.trim() + "T12:00:00");
  if (Number.isNaN(d.getTime())) return dateStr;
  const day = d.getDate();
  const month = MONTH_NAMES[d.getMonth() + 1] ?? "";
  const year = d.getFullYear();
  return `${day} ${month} ${year}`;
}

/** Нормалізована дата/час для платежів: "25 лютого 2025, 14:18" */
export function formatPaymentDate(dateStr: string | null | undefined): string {
  if (!dateStr || !dateStr.trim()) return "—";
  const d = new Date(dateStr.trim().replace(" ", "T"));
  if (Number.isNaN(d.getTime())) return dateStr;
  const day = d.getDate();
  const month = MONTH_NAMES[d.getMonth() + 1] ?? "";
  const year = d.getFullYear();
  const hours = d.getHours();
  const minutes = d.getMinutes();
  const time = `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
  return `${day} ${month} ${year}, ${time}`;
}
