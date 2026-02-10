import { NextRequest, NextResponse } from "next/server";

/**
 * Webhook Monobank не використовується для обробки оплат.
 * Усі оплати обробляє лише Telegram-бот (check_pending_payments).
 * Ендпоінт залишено для сумісності: приймає POST, повертає 200, нічого не робить.
 */
export async function POST(request: NextRequest) {
  try {
    await request.json();
    return NextResponse.json({ ok: true });
  } catch {
    return NextResponse.json({ ok: true });
  }
}
