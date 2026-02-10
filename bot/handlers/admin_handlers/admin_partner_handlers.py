from aiogram import Router, types, F
from ulits.filters import IsAdmin
from main import bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from Content.texts import get_person_emoji_html, get_premium_emoji, format_date, format_datetime
from database.client_db import (
    complete_withdrawal_request,
    reject_withdrawal_request,
    get_withdrawal_request_by_id,
    get_partner_stats_for_admin,
    get_partner_referral_percent,
    set_partner_referral_percent,
    get_withdrawal_requests,
    get_all_partner_participants,
    get_partner_participants_count,
    get_referrals_of_partner,
    get_user_subscriptions,
    get_user_recurring_subscriptions,
    get_user_name,
    get_partner_balance,
    get_partner_total_earned,
)

router = Router()
PARTNER_LIST_PAGE_SIZE = 8


@router.message(IsAdmin(), F.text == "👥 Партнерська програма")
async def admin_partner_program(message: types.Message):
    percent = get_partner_referral_percent()
    total = get_partner_participants_count()
    text = (
        f"{get_premium_emoji('people')} <b>Партнерська програма</b>\n\n"
        f"{get_premium_emoji('chart')} <b>Відсоток нарахування:</b> {percent:.0f}%\n\n"
        f"{get_person_emoji_html()} <b>Учасників:</b> {total}\n\n"
        f"<i>Натисніть «Список учасників», щоб переглянути всіх та деталі по кожному.</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Список учасників", callback_data="admin_partner_list_0")],
        [InlineKeyboardButton(text="✏️ Змінити відсоток", callback_data="admin_partner_set_percent")],
        [InlineKeyboardButton(text="📋 Запити на вивід", callback_data="admin_partner_withdrawals")],
    ])
    await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(IsAdmin(), F.data == "admin_partner_set_percent")
async def admin_partner_set_percent(callback: types.CallbackQuery):
    current = get_partner_referral_percent()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="7%", callback_data="admin_partner_percent_7"),
            InlineKeyboardButton(text="10%", callback_data="admin_partner_percent_10"),
            InlineKeyboardButton(text="15%", callback_data="admin_partner_percent_15"),
        ],
        [
            InlineKeyboardButton(text="20%", callback_data="admin_partner_percent_20"),
            InlineKeyboardButton(text="25%", callback_data="admin_partner_percent_25"),
        ],
        [InlineKeyboardButton(text="← Назад", callback_data="admin_partner_back")],
    ])
    await callback.message.edit_text(
        f"{get_premium_emoji('chart')} <b>Відсоток нарахування партнерам</b>\n\nПоточний: <b>{current:.0f}%</b>\n\nОберіть новий відсоток:",
        parse_mode="HTML",
        reply_markup=kb,
    )
    await callback.answer()


@router.callback_query(IsAdmin(), F.data.startswith("admin_partner_percent_"))
async def admin_partner_percent_set(callback: types.CallbackQuery):
    value = int(callback.data.split("_")[-1])
    if set_partner_referral_percent(float(value)):
        await callback.answer(f"Відсоток змінено на {value}%", show_alert=True)
    else:
        await callback.answer("Помилка.", show_alert=True)
    current = get_partner_referral_percent()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="7%", callback_data="admin_partner_percent_7"),
            InlineKeyboardButton(text="10%", callback_data="admin_partner_percent_10"),
            InlineKeyboardButton(text="15%", callback_data="admin_partner_percent_15"),
        ],
        [
            InlineKeyboardButton(text="20%", callback_data="admin_partner_percent_20"),
            InlineKeyboardButton(text="25%", callback_data="admin_partner_percent_25"),
        ],
        [InlineKeyboardButton(text="← Назад", callback_data="admin_partner_back")],
    ])
    await callback.message.edit_text(
        f"{get_premium_emoji('chart')} <b>Відсоток нарахування партнерам</b>\n\nПоточний: <b>{current:.0f}%</b>\n\nОберіть новий відсоток:",
        parse_mode="HTML",
        reply_markup=kb,
    )


@router.callback_query(IsAdmin(), F.data == "admin_partner_withdrawals")
async def admin_partner_withdrawals(callback: types.CallbackQuery):
    pending = get_withdrawal_requests(status="pending")
    text = "📋 <b>Запити на вивід (pending)</b>\n\n"
    if not pending:
        text += "Немає очікуючих запитів."
    else:
        for row in pending:
            req_id, user_id, amount, status, created_at = row
            text += f"• ID запиту: {req_id} | User: {user_id} | {amount:.2f} ₴ | {format_datetime(created_at)}\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Назад", callback_data="admin_partner_back")],
    ])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(IsAdmin(), F.data == "admin_partner_back")
async def admin_partner_back(callback: types.CallbackQuery):
    percent = get_partner_referral_percent()
    total = get_partner_participants_count()
    text = (
        f"{get_premium_emoji('people')} <b>Партнерська програма</b>\n\n"
        f"{get_premium_emoji('chart')} <b>Відсоток нарахування:</b> {percent:.0f}%\n\n"
        f"{get_person_emoji_html()} <b>Учасників:</b> {total}\n\n"
        f"<i>Натисніть «Список учасників», щоб переглянути всіх та деталі по кожному.</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Список учасників", callback_data="admin_partner_list_0")],
        [InlineKeyboardButton(text="✏️ Змінити відсоток", callback_data="admin_partner_set_percent")],
        [InlineKeyboardButton(text="📋 Запити на вивід", callback_data="admin_partner_withdrawals")],
    ])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(IsAdmin(), F.data.startswith("admin_partner_list_"))
async def admin_partner_list_page(callback: types.CallbackQuery):
    page = int(callback.data.split("_")[-1])
    total_count = get_partner_participants_count()
    if total_count == 0:
        await callback.message.edit_text(
            f"{get_premium_emoji('people')} <b>Учасники партнерської програми</b>\n\nПоки немає учасників.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="← Назад", callback_data="admin_partner_back")],
            ]),
        )
        await callback.answer()
        return
    offset = page * PARTNER_LIST_PAGE_SIZE
    rows = get_all_partner_participants(PARTNER_LIST_PAGE_SIZE, offset)
    total_pages = (total_count + PARTNER_LIST_PAGE_SIZE - 1) // PARTNER_LIST_PAGE_SIZE
    text = (
        f"{get_premium_emoji('people')} <b>Учасники партнерської програми</b>\n\n"
        f"Сторінка {page + 1} з {total_pages} (всього {total_count}).\n\n"
        f"<i>Натисніть на учасника, щоб побачити деталі: реферали та підписки.</i>"
    )
    kb_rows = []
    for row in rows:
        uid, user_name, balance, ref_count, total_earned = row
        name = f"@{user_name}" if user_name else str(uid)
        label = f"{name} | {balance:.0f} ₴ | реф: {ref_count}"
        if len(label) > 35:
            label = (name or str(uid))[:20] + f" | {uid}"
        kb_rows.append([InlineKeyboardButton(text=label, callback_data=f"admin_partner_user_{page}_{uid}")])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="← Назад", callback_data=f"admin_partner_list_{page - 1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="Вперед →", callback_data=f"admin_partner_list_{page + 1}"))
    if nav:
        kb_rows.append(nav)
    kb_rows.append([InlineKeyboardButton(text="← До меню партнерки", callback_data="admin_partner_back")])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows))
    await callback.answer()


def _format_partner_detail(user_id: int, user_name: str, balance: float, ref_count: int, total_earned: float) -> str:
    name = f"@{user_name}" if user_name else str(user_id)
    text = (
        f"{get_person_emoji_html()} <b>Учасник</b>: {name} (ID: <code>{user_id}</code>)\n"
        f"{get_premium_emoji('money')} Баланс: {balance:.2f} ₴ | Запрошено: {ref_count} | Всього нараховано: {total_earned:.2f} ₴\n\n"
    )
    return text


@router.callback_query(IsAdmin(), F.data.startswith("admin_partner_user_"))
async def admin_partner_user_detail(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    user_id = int(parts[-1])
    from_list_page = int(parts[-2]) if len(parts) >= 5 and parts[-2].isdigit() else 0
    participants = get_all_partner_participants(9999, 0)
    partner_row = next((r for r in participants if r[0] == user_id), None)
    if not partner_row:
        partner_row = (
            user_id,
            get_user_name(user_id),
            get_partner_balance(user_id),
            len(get_referrals_of_partner(user_id)),
            get_partner_total_earned(user_id),
        )
    user_id, user_name, balance, ref_count, total_earned = partner_row
    text = _format_partner_detail(user_id, user_name, balance, ref_count, total_earned)

    subs_one = get_user_subscriptions(user_id)
    subs_rec = get_user_recurring_subscriptions(user_id)
    text += f"{get_premium_emoji('pin')} <b>Підписки учасника</b>:\n"
    if not subs_one and not subs_rec:
        text += "  Немає.\n"
    else:
        for s in subs_one:
            text += f"  • {s['product_name']} — {s['status']} до {format_date(s['end_date'])}\n"
        for row in subs_rec:
            pid, pname, months, price, next_date, status, fails = row[0], row[1], row[2], row[3], row[4], row[5], row[6]
            text += f"  • {pname} ({months} міс.) — {status}, наступний платіж: {format_date(next_date)}\n"

    refs = get_referrals_of_partner(user_id)
    text += f"\n{get_premium_emoji('people')} <b>Реферали</b> ({len(refs)}):\n"
    if not refs:
        text += "  Немає.\n"
    else:
        for ref_user_id, ref_name, join_date in refs:
            rn = f"@{ref_name}" if ref_name else str(ref_user_id)
            text += f"\n  • {rn} (ID: <code>{ref_user_id}</code>), з {format_date(join_date)}\n"
            r_subs_one = get_user_subscriptions(ref_user_id)
            r_subs_rec = get_user_recurring_subscriptions(ref_user_id)
            if r_subs_one or r_subs_rec:
                for s in r_subs_one:
                    text += f"    — {s['product_name']} ({s['status']}) до {format_date(s['end_date'])}\n"
                for row in r_subs_rec:
                    pname, status, next_date = row[1], row[5], row[4]
                    text += f"    — {pname} ({status}) наступний: {format_date(next_date)}\n"
            else:
                text += "    — підписок немає\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Написати", url=f"tg://user?id={user_id}")],
        [InlineKeyboardButton(text="← До списку учасників", callback_data=f"admin_partner_list_{from_list_page}")],
        [InlineKeyboardButton(text="← До меню партнерки", callback_data="admin_partner_back")],
    ])
    if len(text) > 4000:
        text = text[:3990] + "\n\n… (текст обрізано)"
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(IsAdmin(), F.data.startswith("admin_withdraw_done_"))
async def admin_withdraw_done(callback: types.CallbackQuery):
    req_id = int(callback.data.split("_")[-1])
    row = get_withdrawal_request_by_id(req_id)
    if not row:
        await callback.answer("Запит не знайдено.", show_alert=True)
        return
    user_id, amount, status = row[0], row[1], row[2]
    if status != "pending":
        await callback.answer("Запит вже оброблено.", show_alert=True)
        return
    if complete_withdrawal_request(req_id):
        try:
            await bot.send_message(
                user_id,
                f"{get_premium_emoji('check')} Ваш запит на вивід <b>{amount:.2f} ₴</b> виконано. Кошти надіслано.",
                parse_mode="HTML",
            )
        except Exception:
            pass
        await callback.answer("Вивід позначено як виконаний.", show_alert=True)
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.edit_text(
            callback.message.text + f"\n\n{get_premium_emoji('check')} <b>Оброблено: виведено</b>",
            parse_mode="HTML",
        )
    else:
        await callback.answer("Помилка при списанні балансу.", show_alert=True)


@router.callback_query(IsAdmin(), F.data.startswith("admin_withdraw_reject_"))
async def admin_withdraw_reject(callback: types.CallbackQuery):
    req_id = int(callback.data.split("_")[-1])
    row = get_withdrawal_request_by_id(req_id)
    if not row:
        await callback.answer("Запит не знайдено.", show_alert=True)
        return
    user_id, amount, status = row[0], row[1], row[2]
    if status != "pending":
        await callback.answer("Запит вже оброблено.", show_alert=True)
        return
    if reject_withdrawal_request(req_id):
        try:
            await bot.send_message(
                user_id,
                f"❌ Ваш запит на вивід <b>{amount:.2f} ₴</b> відхилено. Зв'яжіться з підтримкою.",
                parse_mode="HTML",
            )
        except Exception:
            pass
        await callback.answer("Запит відхилено.", show_alert=True)
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.edit_text(
            callback.message.text + "\n\n❌ <b>Відхилено</b>",
            parse_mode="HTML",
        )
    else:
        await callback.answer("Помилка.", show_alert=True)
