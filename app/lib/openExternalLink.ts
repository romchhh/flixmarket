import type { TelegramWebApp } from "@/types/telegram";

/** Відкриває URL у зовнішньому браузері (поза WebView міні-додатку). */
export function openExternalLink(url: string): void {
  if (typeof window === "undefined" || !url) return;

  const tg = (window as Window & { Telegram?: { WebApp?: TelegramWebApp } }).Telegram?.WebApp;
  if (tg?.openLink) {
    tg.openLink(url, { try_instant_view: false });
    return;
  }

  window.open(url, "_blank", "noopener,noreferrer");
}
