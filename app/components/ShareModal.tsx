"use client";

import { useState, useEffect } from "react";
import { X, Copy, MessageCircle, Mail, Share2 } from "lucide-react";
import type { TelegramWebApp } from "@/types/telegram";

interface ShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  shareLink: string;
  shareText: string;
  tg: TelegramWebApp | null;
}

const TEXTS = {
  title: "Поділитися",
  linkLabel: "Посилання на бота (реферальне)",
  copy: "Копіювати",
  copied: "Скопійовано",
  share: "Поділитися",
  shareVia: "Поділитися через",
  cancel: "Скасувати",
  copyError: "Не вдалося скопіювати",
};

export function ShareModal({ isOpen, onClose, shareLink, shareText, tg }: ShareModalProps) {
  const [copied, setCopied] = useState(false);
  const [showFallback, setShowFallback] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setShowFallback(false);
      document.body.style.overflow = "hidden";
      document.documentElement.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
      document.documentElement.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
      document.documentElement.style.overflow = "";
    };
  }, [isOpen]);

  const handleCopy = async () => {
    if (!shareLink) return;
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard) {
        await navigator.clipboard.writeText(shareLink);
        setCopied(true);
        tg?.HapticFeedback?.notificationOccurred?.("success");
        setTimeout(() => {
          setCopied(false);
          setShowFallback(false);
        }, 2000);
      } else {
        tg?.showAlert?.(TEXTS.copyError);
      }
    } catch {
      tg?.showAlert?.(TEXTS.copyError);
    }
  };

  const handleShare = async () => {
    if (!shareLink) return;
    try {
      if (typeof navigator !== "undefined" && navigator.share) {
        await navigator.share({
          title: shareText,
          text: shareText,
          url: shareLink,
        });
        tg?.HapticFeedback?.notificationOccurred?.("success");
        onClose();
      } else {
        setShowFallback(true);
      }
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        // Користувач скасував
      } else {
        setShowFallback(true);
      }
    }
  };

  const shareViaTelegram = () => {
    if (!shareLink) return;
    const text = encodeURIComponent(shareText);
    const telegramUrl = `https://t.me/share/url?url=${encodeURIComponent(shareLink)}&text=${text}`;
    if (tg?.openTelegramLink) {
      tg.openTelegramLink(telegramUrl);
      tg.HapticFeedback?.impactOccurred?.("medium");
    } else {
      window.open(telegramUrl, "_blank");
    }
    setShowFallback(false);
    onClose();
  };

  const shareViaEmail = () => {
    if (!shareLink) return;
    const subject = encodeURIComponent(shareText);
    const body = encodeURIComponent(`${shareText}\n${shareLink}`);
    window.open(`mailto:?subject=${subject}&body=${body}`, "_blank");
    setShowFallback(false);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <>
      <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
        <div
          className="absolute inset-0 bg-black/30"
          aria-hidden
          onClick={onClose}
        />
        <div className="relative w-full max-w-sm rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-gray-900">{TEXTS.title}</h2>
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-full hover:bg-gray-100 text-gray-500"
              aria-label={TEXTS.cancel}
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <p className="text-xs text-gray-500 mb-1.5">{TEXTS.linkLabel}</p>
          <div className="flex gap-2 mb-3">
            <code className="flex-1 min-w-0 text-xs text-gray-700 bg-gray-50 border border-gray-100 rounded-lg px-2.5 py-2 break-all">
              {shareLink || "—"}
            </code>
          </div>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleCopy}
              disabled={!shareLink}
              className="flex-1 inline-flex items-center justify-center gap-1.5 rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              <Copy className="w-3.5 h-3.5" />
              {copied ? TEXTS.copied : TEXTS.copy}
            </button>
            <button
              type="button"
              onClick={handleShare}
              disabled={!shareLink}
              className="flex-1 inline-flex items-center justify-center gap-1.5 rounded-xl bg-violet-600 px-3 py-2 text-xs font-medium text-white hover:bg-violet-700 disabled:opacity-50"
            >
              <Share2 className="w-3.5 h-3.5" />
              {TEXTS.share}
            </button>
          </div>
        </div>
      </div>

      {showFallback && (
        <div className="fixed inset-0 z-[110] flex items-end justify-center p-4">
          <div
            className="absolute inset-0 bg-black/30"
            aria-hidden
            onClick={() => setShowFallback(false)}
          />
          <div className="relative w-full max-w-sm rounded-t-2xl border-t border-gray-100 bg-white p-4 pb-6">
            <div className="w-12 h-1 bg-gray-200 rounded-full mx-auto mb-4" />
            <h3 className="text-sm font-semibold text-gray-900 mb-3">{TEXTS.shareVia}</h3>
            <div className="space-y-2">
              <button
                type="button"
                onClick={handleCopy}
                className="w-full flex items-center gap-3 p-3 hover:bg-gray-50 rounded-xl transition-colors border border-gray-100"
              >
                <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center">
                  <Copy className="w-5 h-5 text-gray-600" />
                </div>
                <span className="text-sm font-medium text-gray-900">
                  {copied ? TEXTS.copied : TEXTS.copy}
                </span>
              </button>
              <button
                type="button"
                onClick={shareViaTelegram}
                className="w-full flex items-center gap-3 p-3 hover:bg-gray-50 rounded-xl transition-colors border border-gray-100"
              >
                <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center">
                  <MessageCircle className="w-5 h-5 text-gray-600" />
                </div>
                <span className="text-sm font-medium text-gray-900">Telegram</span>
              </button>
              <button
                type="button"
                onClick={shareViaEmail}
                className="w-full flex items-center gap-3 p-3 hover:bg-gray-50 rounded-xl transition-colors border border-gray-100"
              >
                <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center">
                  <Mail className="w-5 h-5 text-gray-600" />
                </div>
                <span className="text-sm font-medium text-gray-900">Email</span>
              </button>
            </div>
            <button
              type="button"
              onClick={() => { setShowFallback(false); onClose(); }}
              className="w-full mt-3 py-2.5 text-sm text-gray-500 font-medium rounded-xl hover:bg-gray-50"
            >
              {TEXTS.cancel}
            </button>
          </div>
        </div>
      )}
    </>
  );
}
