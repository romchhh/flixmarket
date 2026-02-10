from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from database.client_db import get_user_info, get_user_subscriptions, get_user_recurring_subscriptions
from keyboards.client_keyboards import get_start_keyboard
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from Content.texts import get_calendar_emoji_html, get_person_emoji_html, get_premium_emoji

router = Router()

@router.message(F.text.in_(["Мій кабінет", "/profile"]))
async def profile_handler(message: types.Message):
    user_id = message.from_user.id
    user_info = get_user_info(user_id)
    
    if not user_info:
        await message.answer("❌ Профіль не знайдено")
        return
    
    # Отримуємо звичайні підписки
    subscriptions = get_user_subscriptions(user_id)
    
    # Отримуємо повторювані підписки
    recurring_subscriptions = get_user_recurring_subscriptions(user_id)
    
    join_date = datetime.strptime(user_info['join_date'], '%Y-%m-%d %H:%M:%S')

    profile_text = (
        f"{get_person_emoji_html()} <b>Ваш профіль</b>\n\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        f"{get_calendar_emoji_html()} <b>Дата реєстрації:</b> {join_date.strftime('%d.%m.%Y')}\n\n"
    )

    if subscriptions or recurring_subscriptions:
        profile_text += "📋 <b>Ваші підписки</b>\n\n"
        
        # Звичайні підписки
        for sub in subscriptions:
            product_name = sub['product_name']
            price = sub['price']
            end_date = datetime.strptime(sub['end_date'], '%Y-%m-%d')
            status = sub['status']
            
            status_emoji = get_premium_emoji("check") if status == "active" else "❌"
            
            profile_text += (
                f"{status_emoji} <b>{product_name}</b>\n"
                f"   {get_premium_emoji('money')} {price}₴ (одноразова оплата)\n"
                f"   {get_calendar_emoji_html()} До: {end_date.strftime('%d.%m.%Y')}\n\n"
            )
        
        # Повторювані підписки
        for sub in recurring_subscriptions:
            sub_id, product_name, months, price, next_payment_date, status, payment_failures = sub
            
            status_emoji = get_premium_emoji("check") if status == "active" else "❌"
            next_payment = datetime.strptime(next_payment_date, '%Y-%m-%d %H:%M:%S')
            
            profile_text += (
                f"{status_emoji} <b>{product_name}</b> (підписка)\n"
                f"   {get_premium_emoji('money')} {price}₴ кожні {months} {'місяць' if months == 1 else 'місяці' if months in [2,3,4] else 'місяців'}\n"
                f"   {get_calendar_emoji_html()} Наступний платіж: {next_payment.strftime('%d.%m.%Y')}\n"
            )
            
            if payment_failures > 0:
                profile_text += f"   ⚠️ Невдалих спроб: {payment_failures}\n"
            
            profile_text += "\n"
    else:
        profile_text += (
            "📋 <b>Підписки</b>\n\n"
            "<i>У вас поки немає активних підписок.</i>\n"
            "Обирайте сервіси у каталозі — кіно, музика, VPN та інше зі зручною оплатою."
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📋 Управління підписками",
                callback_data="manage_subscriptions"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 Оновити",
                callback_data="refresh_profile"
            )
        ]
    ])

    await message.answer(profile_text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data == "refresh_profile")
async def refresh_profile(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_info = get_user_info(user_id)
    
    if not user_info:
        await callback.answer("❌ Профіль не знайдено")
        return
    
    subscriptions = get_user_subscriptions(user_id)
    recurring_subscriptions = get_user_recurring_subscriptions(user_id)
    
    join_date = datetime.strptime(user_info['join_date'], '%Y-%m-%d %H:%M:%S')

    profile_text = (
        f"{get_person_emoji_html()} <b>Ваш профіль</b>\n\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        f"{get_calendar_emoji_html()} <b>Дата реєстрації:</b> {join_date.strftime('%d.%m.%Y')}\n\n"
    )

    if subscriptions or recurring_subscriptions:
        profile_text += "📋 <b>Ваші підписки</b>\n\n"

        for sub in subscriptions:
            product_name = sub['product_name']
            price = sub['price']
            end_date = datetime.strptime(sub['end_date'], '%Y-%m-%d')
            status = sub['status']
            
            status_emoji = get_premium_emoji("check") if status == "active" else "❌"
            
            profile_text += (
                f"{status_emoji} <b>{product_name}</b>\n"
                f"   {get_premium_emoji('money')} {price}₴ (одноразова оплата)\n"
                f"   {get_calendar_emoji_html()} До: {end_date.strftime('%d.%m.%Y')}\n\n"
            )
        
        for sub in recurring_subscriptions:
            sub_id, product_name, months, price, next_payment_date, status, payment_failures = sub
            
            status_emoji = get_premium_emoji("check") if status == "active" else "❌"
            next_payment = datetime.strptime(next_payment_date, '%Y-%m-%d %H:%M:%S')
            
            profile_text += (
                f"{status_emoji} <b>{product_name}</b> (підписка)\n"
                f"   {get_premium_emoji('money')} {price}₴ кожні {months} {'місяць' if months == 1 else 'місяці' if months in [2,3,4] else 'місяців'}\n"
                f"   {get_calendar_emoji_html()} Наступний платіж: {next_payment.strftime('%d.%m.%Y')}\n"
            )
            
            if payment_failures > 0:
                profile_text += f"   ⚠️ Невдалих спроб: {payment_failures}\n"
            
            profile_text += "\n"
    else:
        profile_text += (
            "📋 <b>Підписки</b>\n\n"
            "<i>У вас поки немає активних підписок.</i>\n"
            "Обирайте сервіси у каталозі — кіно, музика, VPN та інше зі зручною оплатою."
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📋 Управління підписками",
                callback_data="manage_subscriptions"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 Оновити",
                callback_data="refresh_profile"
            )
        ]
    ])

    await callback.message.edit_text(profile_text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer("✅ Профіль оновлено")


@router.callback_query(F.data == "manage_subscriptions")
async def manage_subscriptions(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    subscriptions = get_user_subscriptions(user_id)
    recurring_subscriptions = get_user_recurring_subscriptions(user_id)
    
    if not subscriptions and not recurring_subscriptions:
        await callback.message.edit_text(
            "📋 <b>Управління підписками</b>\n\n"
            "У вас поки немає активних підписок.\n\n"
            "Для перегляду доступних сервісів натисніть кнопку нижче:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 Переглянути сервіси",
                        callback_data="show_services"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="← Назад до профілю",
                        callback_data="refresh_profile"
                    )
                ]
            ])
        )
        return
    
    keyboard = []
    
    # Додаємо кнопки для детального перегляду кожної підписки
    for i, sub in enumerate(subscriptions):
        product_name = sub['product_name']
        keyboard.append([
            InlineKeyboardButton(
                text=f"📄 {product_name} (одноразова)",
                callback_data=f"view_simple_{i}"
            )
        ])
    
    for sub in recurring_subscriptions:
        sub_id, product_name, months, price, next_payment_date, status, payment_failures = sub
        status_text = get_premium_emoji("check") if status == "active" else "❌"
        keyboard.append([
            InlineKeyboardButton(
                text=f"📄 {status_text} {product_name} (підписка)",
                callback_data=f"view_recurring_{sub_id}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            text="← Назад до профілю",
            callback_data="refresh_profile"
        )
    ])
    
    await callback.message.edit_text(
        "📋 <b>Управління підписками</b>\n\n"
        "Виберіть підписку для детального перегляду:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


@router.callback_query(F.data.startswith("view_simple_"))
async def view_simple_subscription(callback: types.CallbackQuery):
    subscription_index = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    # Знаходимо підписку
    subscriptions = get_user_subscriptions(user_id)
    
    if subscription_index >= len(subscriptions):
        await callback.answer("Підписка не знайдена", show_alert=True)
        return
    
    subscription = subscriptions[subscription_index]
    product_name = subscription['product_name']
    
    start_date = datetime.strptime(subscription['start_date'], '%Y-%m-%d')
    end_date = datetime.strptime(subscription['end_date'], '%Y-%m-%d')
    days_left = (end_date.date() - datetime.now().date()).days
    status = subscription['status']
    
    status_emoji = get_premium_emoji("check") if status == "active" else "❌"
    status_text = "Активна" if status == "active" else "Неактивна"
    
    subscription_text = (
        f"📋 <b>Деталі підписки</b>\n\n"
        f"🏷️ <b>Назва:</b> {product_name}\n"
        f"{get_premium_emoji('chart')} <b>Статус:</b> {status_emoji} {status_text}\n"
        f"{get_premium_emoji('money')} <b>Сума:</b> {subscription['price']}₴ (одноразова оплата)\n"
        f"{get_calendar_emoji_html()} <b>Дата початку:</b> {start_date.strftime('%d.%m.%Y')}\n"
        f"{get_calendar_emoji_html()} <b>Дата закінчення:</b> {end_date.strftime('%d.%m.%Y')}\n"
    )
    
    if status == "active":
        subscription_text += f"⏳ <b>Залишилось днів:</b> {days_left}\n"
    
    subscription_text += "\n💡 <i>Це одноразова оплата. Для продовження після закінчення потрібно буде оформити нову підписку.</i>"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="← Назад до управління",
                callback_data="manage_subscriptions"
            )
        ]
    ])
    
    await callback.message.edit_text(
        subscription_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("view_recurring_"))
async def view_recurring_subscription(callback: types.CallbackQuery):
    subscription_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    # Знаходимо підписку
    recurring_subscriptions = get_user_recurring_subscriptions(user_id)
    subscription = None
    for sub in recurring_subscriptions:
        if sub[0] == subscription_id:  # sub[0] - це id
            subscription = sub
            break
    
    if not subscription:
        await callback.answer("Підписка не знайдена", show_alert=True)
        return
    
    sub_id, product_name, months, price, next_payment_date, status, payment_failures = subscription
    next_payment = datetime.strptime(next_payment_date, '%Y-%m-%d %H:%M:%S')
    
    status_emoji = get_premium_emoji("check") if status == "active" else "❌"
    status_text = "Активна" if status == "active" else "Неактивна"
    
    subscription_text = (
        f"📋 <b>Деталі підписки</b>\n\n"
        f"🏷️ <b>Назва:</b> {product_name}\n"
        f"{get_premium_emoji('chart')} <b>Статус:</b> {status_emoji} {status_text}\n"
        f"{get_premium_emoji('money')} <b>Сума:</b> {price}₴\n"
        f"🔄 <b>Періодичність:</b> Кожні {months} {'місяць' if months == 1 else 'місяці' if months in [2,3,4] else 'місяців'}\n"
        f"{get_calendar_emoji_html()} <b>Наступна оплата:</b> {next_payment.strftime('%d.%m.%Y о %H:%M')}\n"
    )
    
    if payment_failures > 0:
        subscription_text += f"⚠️ <b>Невдалих спроб оплати:</b> {payment_failures}/3\n"
    
    subscription_text += "\n"
    
    keyboard = []
    
    if status == "active":
        subscription_text += (
            "🔧 <b>Доступні дії:</b>\n"
            "• Відключити автосплату\n"
            "• Змінити тариф*\n"
            "• Змінити платіжну карту*\n\n"
            "<i>* Для зміни тарифу або карти потрібно скасувати поточну підписку і оформити нову.</i>"
        )
        
        keyboard.extend([
            [
                InlineKeyboardButton(
                    text="🚫 Відключити автосплату",
                    callback_data=f"confirm_cancel_{subscription_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Змінити тариф",
                    callback_data=f"change_tariff_{subscription_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💳 Змінити карту",
                    callback_data=f"change_card_{subscription_id}"
                )
            ]
        ])
    else:
        subscription_text += "ℹ️ <i>Підписка неактивна. Автоматичні платежі зупинені.</i>"
    
    keyboard.append([
        InlineKeyboardButton(
            text="← Назад до управління",
            callback_data="manage_subscriptions"
        )
    ])
    
    await callback.message.edit_text(
        subscription_text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


@router.callback_query(F.data.startswith("confirm_cancel_"))
async def confirm_cancel_subscription(callback: types.CallbackQuery):
    subscription_id = int(callback.data.split("_")[2])
    
    # Отримуємо інформацію про підписку
    user_id = callback.from_user.id
    recurring_subscriptions = get_user_recurring_subscriptions(user_id)
    subscription = None
    for sub in recurring_subscriptions:
        if sub[0] == subscription_id:
            subscription = sub
            break
    
    if not subscription:
        await callback.answer("Підписка не знайдена", show_alert=True)
        return
    
    _, product_name, months, price, next_payment_date, status, _ = subscription
    next_payment = datetime.strptime(next_payment_date, '%Y-%m-%d %H:%M:%S')
    
    confirmation_text = (
        f"⚠️ <b>Підтвердження скасування</b>\n\n"
        f"Ви дійсно хочете скасувати підписку?\n\n"
        f"📋 <b>Підписка:</b> {product_name}\n"
        f"{get_premium_emoji('money')} <b>Сума:</b> {price}₴ кожні {months} {'місяць' if months == 1 else 'місяці' if months in [2,3,4] else 'місяців'}\n"
        f"{get_calendar_emoji_html()} <b>Наступна оплата:</b> {next_payment.strftime('%d.%m.%Y')}\n\n"
        f"<b>Важливо:</b>\n"
        f"• Автоматичні платежі будуть зупинені\n"
        f"• Доступ до сервісу зберігається до кінця поточного оплаченого періоду\n"
        f"• Для відновлення потрібно буде оформити нову підписку"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Так, скасувати",
                callback_data=f"cancel_subscription_{subscription_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Ні, залишити",
                callback_data=f"view_recurring_{subscription_id}"
            )
        ]
    ])
    
    await callback.message.edit_text(
        confirmation_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("cancel_subscription_"))
async def cancel_subscription(callback: types.CallbackQuery):
    subscription_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    # Отримуємо інформацію про підписку перед скасуванням
    recurring_subscriptions = get_user_recurring_subscriptions(user_id)
    subscription = None
    for sub in recurring_subscriptions:
        if sub[0] == subscription_id:
            subscription = sub
            break
    
    if not subscription:
        await callback.answer("Підписка не знайдена", show_alert=True)
        return
    
    _, product_name, months, price, next_payment_date, status, _ = subscription
    
    # Імпортуємо функцію деактивації
    from database.client_db import deactivate_subscription
    
    if deactivate_subscription(subscription_id):
        # Повідомляємо адміністраторів про скасування
        await notify_admins_user_cancelled_subscription(user_id, product_name, "користувач")
        
        await callback.answer("✅ Підписка успішно скасована", show_alert=True)
        
        # Показуємо повідомлення про успішне скасування
        cancellation_text = (
            f"{get_premium_emoji('check')} <b>Підписка скасована</b>\n\n"
            f"📋 <b>Підписка:</b> {product_name}\n"
            f"🚫 <b>Статус:</b> Автосплата відключена\n\n"
            f"ℹ️ <b>Важливо:</b>\n"
            f"• Доступ до сервісу зберігається до кінця поточного оплаченого періоду\n"
            f"• Автоматичні платежі зупинені\n"
            f"• Для поновлення підписки оформіть її знову в каталозі"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Переглянути сервіси",
                    callback_data="show_services"
                )
            ],
            [
                InlineKeyboardButton(
                    text="← Назад до профілю",
                    callback_data="refresh_profile"
                )
            ]
        ])
        
        await callback.message.edit_text(
            cancellation_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await callback.answer("❌ Помилка при скасуванні підписки", show_alert=True)


@router.callback_query(F.data.startswith("change_tariff_"))
async def change_tariff_info(callback: types.CallbackQuery):
    subscription_id = int(callback.data.split("_")[2])
    
    info_text = (
        f"🔄 <b>Зміна тарифу</b>\n\n"
        f"Для зміни тарифу необхідно:\n\n"
        f"1️⃣ Скасувати поточну підписку\n"
        f"2️⃣ Оформити нову підписку з бажаним тарифом\n\n"
        f"<b>Важливо:</b>\n"
        f"• Доступ до поточної підписки зберігається до кінця оплаченого períоду\n"
        f"• Нова підписка почне діяти після оформлення\n"
        f"• Потрібно буде знову ввести дані картки"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🚫 Скасувати поточну підписку",
                callback_data=f"confirm_cancel_{subscription_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="← Назад",
                callback_data=f"view_recurring_{subscription_id}"
            )
        ]
    ])
    
    await callback.message.edit_text(
        info_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("change_card_"))
async def change_card_info(callback: types.CallbackQuery):
    subscription_id = int(callback.data.split("_")[2])
    
    info_text = (
        f"{get_premium_emoji('card')} <b>Зміна платіжної картки</b>\n\n"
        f"Для зміни платіжної картки необхідно:\n\n"
        f"1️⃣ Скасувати поточну підписку\n"
        f"2️⃣ Оформити нову підписку з новою карткою\n\n"
        f"<b>Важливо:</b>\n"
        f"• Доступ до поточної підписки зберігається до кінця оплаченого періоду\n"
        f"• При оформленні нової підписки буде збережена нова картка\n"
        f"• Всі подальші платежі будуть проходити з нової картки"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🚫 Скасувати поточну підписку",
                callback_data=f"confirm_cancel_{subscription_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="← Назад",
                callback_data=f"view_recurring_{subscription_id}"
            )
        ]
    ])
    
    await callback.message.edit_text(
        info_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def notify_admins_user_cancelled_subscription(user_id: int, product_name: str, cancellation_reason: str):
    """Повідомляє адміністраторів про скасування підписки користувачем"""
    try:
        from config import admin_chat_id
        from database.client_db import get_username_by_id
        from main import bot
        
        username = get_username_by_id(user_id)
        user_line = f"Користувач: @{username} (ID: <code>{user_id}</code>)" if (username and str(username).strip()) else f"Користувач: ID <code>{user_id}</code> (прихований профіль)"
        admin_message = (
            f"🚫 <b>Підписка скасована користувачем</b>\n\n"
            f"{user_line}\n"
            f"Підписка: <b>{product_name}</b>\n"
            f"Причина: <b>{cancellation_reason}</b>\n\n"
            f"💡 Користувач самостійно скасував підписку через профіль"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👤 Написати користувачу",
                    url=f"tg://user?id={user_id}"
                )
            ]
        ])
        
        await bot.send_message(admin_chat_id, admin_message, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        print(f"Помилка при надсиланні повідомлення адміну про скасування: {e}") 