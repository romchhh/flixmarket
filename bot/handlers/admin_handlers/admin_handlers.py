from aiogram import Router, types
from config import administrators
from ulits.filters import IsAdmin
from aiogram.fsm.context import FSMContext
from keyboards.client_keyboards import get_start_keyboard
from keyboards.admin_keyboards import admin_keyboard
from Content.texts import get_greeting_message, get_calendar_emoji_html, get_premium_emoji
from database.admin_db import get_admin_subscriptions_stats

router = Router()


@router.message(
    IsAdmin(),
    lambda message: message.text == "Адмін панель 💻" or message.text == "/admin",
)
async def admin_panel(message: types.Message):
    user_id = message.from_user.id
    if user_id in administrators:
        await message.answer(
            "Вітаю в адмін панелі. Ось ваші доступні опції.",
            reply_markup=admin_keyboard(),
        )


@router.message(IsAdmin(), lambda message: message.text == "Головне меню")
async def my_parcel(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    await message.answer(
        get_greeting_message(),
        reply_markup=get_start_keyboard(user_id),
        parse_mode="HTML",
    )


@router.message(IsAdmin(), lambda message: message.text == "Статистика")
async def statistic_handler(message: types.Message):
    stats = get_admin_subscriptions_stats()
    if not stats:
        await message.answer(
            "❌ Не вдалося завантажити статистику.",
            parse_mode="HTML",
        )
        return

    total_revenue = stats.get("total_revenue", 0) + stats.get("total_auto_revenue", 0)
    today_revenue = stats.get("today_revenue", 0) + stats.get("today_auto_revenue", 0)
    month_revenue = stats.get("month_revenue", 0) + stats.get(
        "month_auto_revenue", 0
    )
    today_payments_total = stats.get("today_payments_count", 0) + stats.get(
        "today_auto_payments_count", 0
    )
    month_payments_total = stats.get("month_payments_count", 0) + stats.get(
        "month_auto_payments_count", 0
    )

    response_message = (
        f"<b>{get_premium_emoji('chart')} СТАТИСТИКА</b>\n\n"
        f"<b>{get_premium_emoji('people')} Користувачі</b>\n"
        f"• Всього: <b>{stats.get('total_users', 0)}</b>\n"
        f"• Нових сьогодні: <b>{stats.get('new_users_today', 0)}</b>\n"
        f"• За тиждень: <b>{stats.get('new_users_week', 0)}</b>\n"
        f"• За місяць: <b>{stats.get('new_users_month', 0)}</b>\n\n"
        f"<b>{get_premium_emoji('box')} Товари та підписки</b>\n"
        f"• Товарів у каталозі: <b>{stats.get('total_products', 0)}</b>\n"
        f"• Одноразових підписок: <b>{stats.get('total_simple_subscriptions', 0)}</b> (активних: {stats.get('active_simple_subscriptions', 0)})\n"
        f"• Помісячних підписок: <b>{stats.get('total_recurring_subscriptions', 0)}</b> (активних: {stats.get('active_recurring_subscriptions', 0)})\n\n"
        f"<b>{get_premium_emoji('money')} Дохід</b>\n"
        f"• Сьогодні: <b>{today_revenue:.2f} ₴</b> ({today_payments_total} платежів)\n"
        f"• За місяць: <b>{month_revenue:.2f} ₴</b> ({month_payments_total} платежів)\n"
        f"• Всього: <b>{total_revenue:.2f} ₴</b>\n\n"
        f"<b>{get_calendar_emoji_html()} Деталі за сьогодні</b>\n"
        f"• Одноразові: {stats.get('today_payments_count', 0)} шт. / {stats.get('today_revenue', 0):.2f} ₴\n"
        f"• Автосписання: {stats.get('today_auto_payments_count', 0)} шт. / {stats.get('today_auto_revenue', 0):.2f} ₴\n"
        f"• Невдалих авто: <b>{stats.get('today_failed_payments', 0)}</b>\n"
    )
    await message.answer(response_message, parse_mode="HTML")
