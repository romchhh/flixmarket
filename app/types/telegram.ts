/** Користувач з Telegram Web App init data */
export interface TelegramWebAppUser {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  language_code?: string;
  is_premium?: boolean;
  photo_url?: string;
}

export interface InitDataParsed {
  user?: TelegramWebAppUser;
  auth_date: number;
  hash: string;
}

/** Telegram Web App instance (window.Telegram.WebApp) */
export interface TelegramWebApp {
  openLink?: (url: string) => void;
  openTelegramLink?: (url: string) => void;
  showAlert?: (message: string) => void;
  HapticFeedback?: {
    impactOccurred?: (style: "light" | "medium" | "heavy") => void;
    notificationOccurred?: (type: "error" | "success" | "warning") => void;
  };
}
