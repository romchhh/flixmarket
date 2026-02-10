from aiogram import Router, types, F
from ulits.filters import IsAdmin
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from keyboards.admin_keyboards import (
    get_admin_subscriptions_keyboard,
    get_admin_subscription_list_keyboard_with_pagination,
    get_admin_subscription_actions_keyboard,
    get_confirm_run_payments_keyboard,
)
from database.admin_db import (
    get_admin_subscriptions_stats,
    search_subscriptions_for_admin,
    get_subscription_details,
    update_subscription_status,
    delete_subscription,
    get_all_subscriptions_for_admin,
    cursor,
)
from ulits.admin_states import SearchSubscription
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
import logging
from Content.texts import get_calendar_emoji_html, get_person_emoji_html, get_premium_emoji


router = Router()

current_page = 0


@router.message(IsAdmin(), F.text.in_(["Управління підписками"]))
async def manage_subscriptions(message: types.Message):
    stats = get_admin_subscriptions_stats()

    stats_text = (
        f"{get_premium_emoji('chart')} <b>Статистика підписок</b>\n\n"
        f"📋 <b>Загальна кількість підписок:</b>\n"
        f"• Одноразові: {stats.get('total_simple_subscriptions', 0)}\n"
        f"• Повторювані: {stats.get('total_recurring_subscriptions', 0)}\n\n"
        f"{get_premium_emoji('check')} <b>Активні підписки:</b>\n"
        f"• Одноразові: {stats.get('active_simple_subscriptions', 0)}\n"
        f"• Повторювані: {stats.get('active_recurring_subscriptions', 0)}\n\n"
        f"{get_premium_emoji('money')} <b>Платежі сьогодні:</b>\n"
        f"• Нові покупки: {stats.get('today_payments_count', 0)} ({stats.get('today_revenue', 0):.2f}₴)\n"
        f"• Автоплатежі: {stats.get('today_auto_payments_count', 0)} ({stats.get('today_auto_revenue', 0):.2f}₴)\n"
        f"• Невдалі: {stats.get('today_failed_payments', 0)}\n\n"
        f"📈 <b>За місяць:</b>\n"
        f"• Нові покупки: {stats.get('month_payments_count', 0)} ({stats.get('month_revenue', 0):.2f}₴)\n"
        f"• Автоплатежі: {stats.get('month_auto_payments_count', 0)} ({stats.get('month_auto_revenue', 0):.2f}₴)\n\n"
        f"{get_premium_emoji('bill')} <b>Загальний дохід сьогодні:</b> {(stats.get('today_revenue', 0) + stats.get('today_auto_revenue', 0)):.2f}₴\n"
        f"{get_premium_emoji('bill')} <b>Загальний дохід за місяць:</b> {(stats.get('month_revenue', 0) + stats.get('month_auto_revenue', 0)):.2f}₴"
    )

    await message.answer(
        stats_text,
        parse_mode="HTML",
        reply_markup=get_admin_subscriptions_keyboard(),
    )


@router.callback_query(F.data == "view_all_subscriptions")
async def view_all_subscriptions(callback: types.CallbackQuery):
    global current_page
    current_page = 0
    await callback.answer()
    await view_all_subscriptions_with_page(callback, current_page)


@router.callback_query(F.data.startswith("admin_view_"))
async def admin_view_subscription(callback: types.CallbackQuery):
    _, _, subscription_type, subscription_id = callback.data.split("_")
    subscription_id = int(subscription_id)

    details = get_subscription_details(subscription_id, subscription_type)

    if not details:
        await callback.answer("Підписка не знайдена", show_alert=True)
        return

    if subscription_type == "simple":
        user_id, username, product_name, price, start_date, end_date, status = (
            details[1],
            details[7],
            details[2],
            details[3],
            details[4],
            details[5],
            details[6],
        )

        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        days_left = (end_dt.date() - datetime.now().date()).days
        user_line = f"{get_person_emoji_html()} <b>Користувач:</b> @{username} (ID: {user_id})" if (username and str(username).strip()) else f"{get_person_emoji_html()} <b>Користувач:</b> ID {user_id} (прихований профіль)"
        details_text = (
            f"📄 <b>Одноразова підписка #{subscription_id}</b>\n\n"
            f"{user_line}\n"
            f"🏷️ <b>Продукт:</b> {product_name}\n"
            f"{get_premium_emoji('money')} <b>Сума:</b> {price}₴\n"
            f"{get_calendar_emoji_html()} <b>Початок:</b> {start_dt.strftime('%d.%m.%Y')}\n"
            f"{get_calendar_emoji_html()} <b>Закінчення:</b> {end_dt.strftime('%d.%m.%Y')}\n"
            f"⏳ <b>Залишилось днів:</b> {days_left}\n"
            f"{get_premium_emoji('chart')} <b>Статус:</b> {get_premium_emoji('check') + ' Активна' if status == 'active' else '❌ Неактивна'}"
        )
    else:
        (
            user_id,
            username,
            product_name,
            price,
            months,
            next_payment_date,
            status,
            payment_failures,
        ) = (
            details[1],
            details[8],
            details[2],
            details[3],
            details[4],
            details[5],
            details[6],
            details[7],
        )

        next_payment_dt = datetime.strptime(
            next_payment_date, "%Y-%m-%d %H:%M:%S"
        )
        user_line_rec = f"{get_person_emoji_html()} <b>Користувач:</b> @{username} (ID: {user_id})" if (username and str(username).strip()) else f"{get_person_emoji_html()} <b>Користувач:</b> ID {user_id} (прихований профіль)"
        details_text = (
            f"🔄 <b>Повторювана підписка #{subscription_id}</b>\n\n"
            f"{user_line_rec}\n"
            f"🏷️ <b>Продукт:</b> {product_name}\n"
            f"{get_premium_emoji('money')} <b>Сума:</b> {price}₴\n"
            f"🔄 <b>Періодичність:</b> Кожні {months} {'місяць' if months == 1 else 'місяці' if months in [2, 3, 4] else 'місяців'}\n"
            f"{get_calendar_emoji_html()} <b>Наступний платіж:</b> {next_payment_dt.strftime('%d.%m.%Y о %H:%M')}\n"
            f"{get_premium_emoji('chart')} <b>Статус:</b> {get_premium_emoji('check') + ' Активна' if status == 'active' else '❌ Неактивна'}\n"
            f"⚠️ <b>Невдалих спроб:</b> {payment_failures}/3"
        )

    await callback.message.edit_text(
        details_text,
        parse_mode="HTML",
        reply_markup=get_admin_subscription_actions_keyboard(
            subscription_id, subscription_type
        ),
    )


@router.callback_query(F.data.startswith("admin_activate_"))
async def admin_activate_subscription(callback: types.CallbackQuery):
    _, _, subscription_type, subscription_id = callback.data.split("_")
    subscription_id = int(subscription_id)

    if update_subscription_status(subscription_id, subscription_type, "active"):
        await callback.answer("✅ Підписка активована", show_alert=True)
        await admin_view_subscription(callback)
    else:
        await callback.answer("❌ Помилка при активації", show_alert=True)


@router.callback_query(F.data.startswith("admin_deactivate_"))
async def admin_deactivate_subscription(callback: types.CallbackQuery):
    _, _, subscription_type, subscription_id = callback.data.split("_")
    subscription_id = int(subscription_id)

    if update_subscription_status(subscription_id, subscription_type, "inactive"):
        await callback.answer("❌ Підписка деактивована", show_alert=True)
        await admin_view_subscription(callback)
    else:
        await callback.answer("❌ Помилка при деактивації", show_alert=True)


@router.callback_query(F.data.startswith("admin_delete_"))
async def admin_delete_subscription(callback: types.CallbackQuery):
    _, _, subscription_type, subscription_id = callback.data.split("_")
    subscription_id = int(subscription_id)

    if delete_subscription(subscription_id, subscription_type):
        await callback.answer("🗑️ Підписка видалена", show_alert=True)
        await view_all_subscriptions(callback)
    else:
        await callback.answer("❌ Помилка при видаленні", show_alert=True)


@router.callback_query(F.data.startswith("admin_contact_"))
async def admin_contact_user(callback: types.CallbackQuery):
    _, _, subscription_type, subscription_id = callback.data.split("_")
    subscription_id = int(subscription_id)

    details = get_subscription_details(subscription_id, subscription_type)

    if not details:
        await callback.answer("Підписка не знайдена", show_alert=True)
        return

    user_id = details[1]

    contact_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👤 Написати користувачу",
                    url=f"tg://user?id={user_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="← Назад до підписки",
                    callback_data=f"admin_view_{subscription_type}_{subscription_id}",
                )
            ],
        ]
    )

    await callback.message.edit_text(
        f"{get_person_emoji_html()} <b>Контакт з користувачем</b>\n\n"
        f"ID користувача: <code>{user_id}</code>\n"
        f"Натисніть кнопку нижче для написання користувачу:",
        parse_mode="HTML",
        reply_markup=contact_keyboard,
    )


@router.callback_query(F.data == "detailed_stats")
async def detailed_stats(callback: types.CallbackQuery):
    stats = get_admin_subscriptions_stats()

    detailed_text = (
        f"{get_premium_emoji('chart')} <b>Детальна статистика</b>\n\n"
        f"📋 <b>Підписки:</b>\n"
        f"• Всього одноразових: {stats.get('total_simple_subscriptions', 0)}\n"
        f"• Активних одноразових: {stats.get('active_simple_subscriptions', 0)}\n"
        f"• Всього повторюваних: {stats.get('total_recurring_subscriptions', 0)}\n"
        f"• Активних повторюваних: {stats.get('active_recurring_subscriptions', 0)}\n\n"
        f"{get_premium_emoji('money')} <b>Платежі сьогодні:</b>\n"
        f"• Нових покупок: {stats.get('today_payments_count', 0)}\n"
        f"• Сума нових покупок: {stats.get('today_revenue', 0):.2f}₴\n"
        f"• Автоплатежів: {stats.get('today_auto_payments_count', 0)}\n"
        f"• Сума автоплатежів: {stats.get('today_auto_revenue', 0):.2f}₴\n"
        f"• Невдалих платежів: {stats.get('today_failed_payments', 0)}\n\n"
        f"📈 <b>Платежі за місяць:</b>\n"
        f"• Нових покупок: {stats.get('month_payments_count', 0)}\n"
        f"• Сума нових покупок: {stats.get('month_revenue', 0):.2f}₴\n"
        f"• Автоплатежів: {stats.get('month_auto_payments_count', 0)}\n"
        f"• Сума автоплатежів: {stats.get('month_auto_revenue', 0):.2f}₴\n\n"
        f"{get_premium_emoji('bill')} <b>Загальні доходи:</b>\n"
        f"• Сьогодні: {(stats.get('today_revenue', 0) + stats.get('today_auto_revenue', 0)):.2f}₴\n"
        f"• За місяць: {(stats.get('month_revenue', 0) + stats.get('month_auto_revenue', 0)):.2f}₴"
    )

    back_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="← Назад",
                    callback_data="back_to_admin_subscriptions",
                )
            ]
        ]
    )

    await callback.message.edit_text(
        detailed_text,
        parse_mode="HTML",
        reply_markup=back_keyboard,
    )


@router.callback_query(F.data == "back_to_admin_subscriptions")
async def back_to_admin_subscriptions(callback: types.CallbackQuery):
    await manage_subscriptions(callback.message)


@router.callback_query(IsAdmin(), F.data == "search_subscription")
async def search_subscription_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(SearchSubscription.waiting_for_query)
    cancel_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Скасувати",
                    callback_data="cancel_search_subscription",
                )
            ]
        ]
    )
    await callback.message.edit_text(
        "🔍 <b>Пошук підписки</b>\n\n"
        "Введіть один з варіантів:\n"
        "• <b>User ID</b> — Telegram ID користувача\n"
        "• <b>Username</b> — без @ (наприклад: username)\n"
        "• <b>Назва товару</b> — частина назви підписки\n"
        "• <b>ID підписки</b> — номер підписки",
        parse_mode="HTML",
        reply_markup=cancel_kb,
    )


@router.callback_query(IsAdmin(), F.data == "cancel_search_subscription")
async def cancel_search_subscription(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await manage_subscriptions(callback.message)


@router.message(
    IsAdmin(), StateFilter(SearchSubscription.waiting_for_query)
)
async def search_subscription_process(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer(
            "Будь ласка, введіть текстовий запит (user_id, username або назву товару)."
        )
        return

    query = message.text.strip()
    await state.clear()

    if not query:
        await message.answer(
            "Введіть запит для пошуку.",
            reply_markup=get_admin_subscriptions_keyboard(),
        )
        return

    subscriptions = search_subscriptions_for_admin(query)

    if not subscriptions:
        await message.answer(
            f"🔍 За запитом «<b>{query}</b>» нічого не знайдено.\n\n"
            "Спробуйте user_id, username або назву товару.",
            parse_mode="HTML",
            reply_markup=get_admin_subscriptions_keyboard(),
        )
        return

    items_per_page = 20
    page_subscriptions = subscriptions[:items_per_page]
    total_pages = 1
    shown = len(page_subscriptions)
    total = len(subscriptions)

    text = (
        f"🔍 <b>Результати пошуку: «{query}»</b>\n\n"
        f"Знайдено підписок: <b>{total}</b>\n"
    )
    if total > items_per_page:
        text += f"Показано перші {shown} з {total}. Уточніть запит для звуження.\n\n"
    text += (
        f"🔄 — Повторювана підписка | {get_premium_emoji('card')} — Одноразова\n"
        f"{get_premium_emoji('check')} — Активна | ❌ — Неактивна\n\n"
        "Натисніть на підписку для деталей:"
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_admin_subscription_list_keyboard_with_pagination(
            page_subscriptions,
            0,
            total_pages,
        ),
    )


@router.callback_query(F.data == "prev_page")
async def prev_page_subscriptions(callback: types.CallbackQuery):
    global current_page
    await callback.answer()
    if current_page > 0:
        current_page -= 1
    await view_all_subscriptions_with_page(callback, current_page)


@router.callback_query(F.data == "next_page")
async def next_page_subscriptions(callback: types.CallbackQuery):
    global current_page
    await callback.answer()
    current_page += 1
    await view_all_subscriptions_with_page(callback, current_page)


async def view_all_subscriptions_with_page(
    callback: types.CallbackQuery, page: int = 0
):
    subscriptions = get_all_subscriptions_for_admin()

    if not subscriptions:
        await callback.message.edit_text(
            "📋 <b>Управління підписками</b>\n\n"
            "Підписок поки немає.",
            parse_mode="HTML",
            reply_markup=get_admin_subscriptions_keyboard(),
        )
        return

    items_per_page = 20
    start_index = page * items_per_page
    end_index = start_index + items_per_page
    page_subscriptions = subscriptions[start_index:end_index]

    if not page_subscriptions and page > 0:
        global current_page
        current_page = page - 1
        await view_all_subscriptions_with_page(callback, current_page)
        return

    total_pages = (len(subscriptions) + items_per_page - 1) // items_per_page

    list_text = (
        f"📋 <b>Всі підписки ({len(subscriptions)})</b>\n"
        f"📄 Сторінка {page + 1} з {total_pages}\n\n"
        f"🔄 - Повторювана підписка\n"
        f"{get_premium_emoji('card')} - Одноразова оплата\n"
        f"{get_premium_emoji('check')} - Активна\n"
        f"❌ - Неактивна\n\n"
        f"Натисніть на підписку для детального перегляду:"
    )

    await callback.message.edit_text(
        list_text,
        parse_mode="HTML",
        reply_markup=get_admin_subscription_list_keyboard_with_pagination(
            page_subscriptions,
            page,
            total_pages,
        ),
    )


@router.callback_query(F.data == "confirm_run_payments")
async def confirm_run_payments(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "⚠️ <b>Увага!</b>\n\n"
        "Ви хочете запустити обробку повторюваних платежів.\n\n"
        "Це простиме всі активні повторювані підписки, які мають настав час для списання.\n\n"
        "Ви впевнені?",
        parse_mode="HTML",
        reply_markup=get_confirm_run_payments_keyboard(),
    )


@router.callback_query(F.data == "cancel_run_payments")
async def cancel_run_payments(callback: types.CallbackQuery):
    await callback.answer("Скасовано", show_alert=True)

    stats = get_admin_subscriptions_stats()

    stats_text = (
        f"{get_premium_emoji('chart')} <b>Статистика підписок</b>\n\n"
        f"📋 <b>Загальна кількість підписок:</b>\n"
        f"• Одноразові: {stats.get('total_simple_subscriptions', 0)}\n"
        f"• Повторювані: {stats.get('total_recurring_subscriptions', 0)}\n\n"
        f"{get_premium_emoji('check')} <b>Активні підписки:</b>\n"
        f"• Одноразові: {stats.get('active_simple_subscriptions', 0)}\n"
        f"• Повторювані: {stats.get('active_recurring_subscriptions', 0)}\n\n"
        f"{get_premium_emoji('money')} <b>Платежі сьогодні:</b>\n"
        f"• Нові покупки: {stats.get('today_payments_count', 0)} ({stats.get('today_revenue', 0):.2f}₴)\n"
        f"• Автоплатежі: {stats.get('today_auto_payments_count', 0)} ({stats.get('today_auto_revenue', 0):.2f}₴)\n"
        f"• Невдалі: {stats.get('today_failed_payments', 0)}\n\n"
        f"📈 <b>За місяць:</b>\n"
        f"• Нові покупки: {stats.get('month_payments_count', 0)} ({stats.get('month_revenue', 0):.2f}₴)\n"
        f"• Автоплатежі: {stats.get('month_auto_payments_count', 0)} ({stats.get('month_auto_revenue', 0):.2f}₴)\n\n"
        f"{get_premium_emoji('bill')} <b>Загальний дохід сьогодні:</b> {(stats.get('today_revenue', 0) + stats.get('today_auto_revenue', 0)):.2f}₴\n"
        f"{get_premium_emoji('bill')} <b>Загальний дохід за місяць:</b> {(stats.get('month_revenue', 0) + stats.get('month_auto_revenue', 0)):.2f}₴"
    )

    await callback.message.edit_text(
        stats_text,
        parse_mode="HTML",
        reply_markup=get_admin_subscriptions_keyboard(),
    )


@router.callback_query(F.data == "run_payments_now")
async def run_payments_now(callback: types.CallbackQuery):
    from ulits.cron_functions import process_recurring_payments
    from database.client_db import get_active_recurring_subscriptions

    await callback.message.edit_text(
        "🔄 <b>Запуск повторюваних платежів...</b>\n\n"
        "⏳ Обробляю платежі...",
        parse_mode="HTML",
    )

    subscriptions = get_active_recurring_subscriptions()

    if not subscriptions:
        await callback.message.edit_text(
            f"{get_premium_emoji('check')} <b>Готово!</b>\n\n"
            "Немає активних повторюваних підписок для обробки.",
            parse_mode="HTML",
            reply_markup=get_admin_subscriptions_keyboard(),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        f"🔄 <b>Обробка платежів...</b>\n\n"
        f"Знайдено підписок: {len(subscriptions)}\n"
        f"⏳ Зачекайте...",
        parse_mode="HTML",
    )

    try:
        await process_recurring_payments()

        successful = 0
        failed = 0

        for subscription in subscriptions:
            subscription_id = subscription[0]
            cursor.execute(
                """
                SELECT COUNT(*) FROM subscription_payments
                WHERE subscription_id = ? AND status = 'success'
                AND DATE(payment_date) = DATE('now')
            """,
                (subscription_id,),
            )
            successful += cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT COUNT(*) FROM subscription_payments
                WHERE subscription_id = ? AND status IN ('failed', 'error')
                AND DATE(payment_date) = DATE('now')
            """,
                (subscription_id,),
            )
            failed += cursor.fetchone()[0]

        result_text = (
            f"{get_premium_emoji('check')} <b>Обробка завершена!</b>\n\n"
            f"{get_premium_emoji('chart')} <b>Результати:</b>\n"
            f"• Знайдено підписок: {len(subscriptions)}\n"
            f"• Успішних платежів: {successful}\n"
            f"• Невдалих платежів: {failed}\n\n"
            f"{get_calendar_emoji_html()} <b>Час:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
        )

        await callback.message.edit_text(
            result_text,
            parse_mode="HTML",
            reply_markup=get_admin_subscriptions_keyboard(),
        )

    except Exception as e:
        logging.error(f"Помилка при запуску платежів: {e}")
        await callback.message.edit_text(
            f"❌ <b>Помилка при обробці платежів!</b>\n\n"
            f"Деталі: {str(e)}",
            parse_mode="HTML",
            reply_markup=get_admin_subscriptions_keyboard(),
        )

    await callback.answer()
