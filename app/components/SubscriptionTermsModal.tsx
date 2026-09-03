"use client";

import Link from "next/link";
import { CreditCard, X } from "lucide-react";

function monthsWord(months: number): string {
  if (months === 1) return "місяць";
  if (months >= 2 && months <= 4) return "місяці";
  return "місяців";
}

type SubscriptionTermsModalProps = {
  open: boolean;
  productName: string;
  months: number;
  priceLabel: string;
  loading?: boolean;
  onClose: () => void;
  onConfirm: () => void;
};

export default function SubscriptionTermsModal({
  open,
  productName,
  months,
  priceLabel,
  loading = false,
  onClose,
  onConfirm,
}: SubscriptionTermsModalProps) {
  if (!open) return null;

  const period = `${months} ${monthsWord(months)}`;

  return (
    <div className="fixed inset-0 z-[200] flex items-end sm:items-center justify-center">
      <button
        type="button"
        className="absolute inset-0 bg-black/40"
        aria-label="Закрити"
        onClick={onClose}
      />
      <div className="relative w-full max-w-md mx-auto rounded-t-3xl sm:rounded-3xl bg-white shadow-xl max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 flex items-center justify-between gap-3 bg-white px-5 pt-5 pb-3 border-b border-gray-100">
          <h2 className="text-lg font-bold text-gray-900">Умови автоматичної підписки</h2>
          <button
            type="button"
            onClick={onClose}
            className="w-9 h-9 rounded-full hover:bg-gray-100 flex items-center justify-center text-gray-500"
            aria-label="Закрити"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-5 py-4 space-y-4">
          <div className="rounded-2xl bg-gray-50 border border-gray-100 p-4 text-sm text-gray-700 space-y-1">
            <p>
              Товар: <span className="font-semibold text-gray-900">{productName}</span>
            </p>
            <p>
              Тариф: <span className="font-semibold text-gray-900">{period}</span>
            </p>
            <p>
              Сума: <span className="font-semibold text-gray-900">{priceLabel}</span>
            </p>
          </div>

          <div className="rounded-2xl bg-amber-50 border border-amber-200/80 p-4">
            <p className="text-sm font-semibold text-amber-900 mb-2">Важливо перед оплатою</p>
            <ul className="text-sm text-amber-950/90 space-y-2 list-disc pl-4">
              <li>Після успішної оплати активується автоматична підписка.</li>
              <li>
                Кошти списуватимуться автоматично кожні <strong>{period}</strong>.
              </li>
              <li>Картка зберігається для подальших платежів.</li>
              <li>Скасувати автопродовження можна будь-коли в профілі / «Мої підписки».</li>
              <li>Після скасування доступ діє до кінця вже оплаченого періоду.</li>
              <li>
                Якщо списання не вдасться, зробимо кілька спроб протягом кількох днів. Якщо оплата
                так і не пройде — підписку буде автоматично скасовано.
              </li>
            </ul>
          </div>

          <p className="text-xs text-gray-500 leading-relaxed">
            Продовжуючи, ви погоджуєтесь з умовами автоматичної підписки та{" "}
            <Link href="/oferta" className="text-violet-600 hover:underline">
              публічною офертою
            </Link>
            . Також ознайомтесь з{" "}
            <Link href="/policy" className="text-violet-600 hover:underline">
              політикою конфіденційності
            </Link>
            .
          </p>

          <div className="flex flex-col gap-2 pb-2">
            <button
              type="button"
              onClick={onConfirm}
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-2xl bg-violet-600 px-4 py-3.5 text-base font-semibold text-white shadow-md hover:bg-violet-700 disabled:opacity-50"
            >
              <CreditCard className="w-5 h-5 shrink-0" />
              {loading ? "Завантаження…" : "Погоджуюсь і оплатити"}
            </button>
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-50"
            >
              Скасувати
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
