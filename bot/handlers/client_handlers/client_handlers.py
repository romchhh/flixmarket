from aiogram import Router, types, F
from aiogram.types import FSInputFile, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from config import administrators
from main import bot, scheduler
from aiogram.filters import Command
from keyboards.client_keyboards import get_start_keyboard, get_socials_keyboard, get_manager_keyboard, get_catalog_keyboard, get_products_keyboard, get_product_info_keyboard, get_payment_keyboard, get_payment_choice_keyboard, get_profile_keyboard, get_back_to_profile_keyboard, get_referral_keyboard, get_contest_keyboard
from Content.texts import get_greeting_message, get_about_text, get_faq_text, get_manager_text, get_help_text, get_referral_text, get_contest_text, MENU_EMOJI_IDS, get_calendar_emoji_html, get_tv_emoji_html, get_person_emoji_html, get_premium_emoji, format_date, format_product_name_for_display
from database.client_db import create_table, check_user, add_user, create_products_table, get_product_by_id, save_payment_info, create_payments_table, create_subscriptions_table, get_user_info, get_user_subscriptions, get_user_name, cursor, conn, create_contest_table, get_partner_balance, get_partner_referral_percent, get_partner_earnings_history, create_withdrawal_request, deduct_partner_balance, add_subscription, get_product_type
from ulits.monopay_functions import PaymentManager, check_pending_payments
import asyncio
import os
from ulits.cron_functions import check_expiring_subscriptions, process_recurring_payments
from datetime import datetime
from ulits.client_functions import get_profile_text, get_status_text
from ulits.client_states import WithdrawPartner
from aiogram.fsm.context import FSMContext
from config import admin_chat_id, MIN_WITHDRAWAL, CATALOG_IMAGE_PATH
from ulits.path_utils import resolve_media_path
from html import escape


router = Router()

payment_manager = PaymentManager()

async def scheduler_jobs():
    scheduler.add_job(check_pending_payments, "interval", minutes=0.5)
    scheduler.add_job(check_expiring_subscriptions, "cron", hour=16, minute=0)
    scheduler.add_job(process_recurring_payments, "interval", hours=6)




@router.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id

    create_contest_table()

    if check_user(user_id):
        await message.answer(get_greeting_message(), parse_mode="HTML", reply_markup=get_start_keyboard(user_id))
        return

    args = message.text.split()[1] if len(message.text.split()) > 1 else None
    if args:
        # Перевіряємо, чи це посилання для конкурсу
        if args.startswith("Eve12nt145Q_"):
            ref_id = int(args.split("_")[1])
            user_name = get_user_name(ref_id)
            
            # Додаємо запис про участь в конкурсі
            cursor.execute("""
                INSERT INTO contest (user_id, invite_id, invite_date)
                VALUES (?, ?, datetime('now'))
            """, (user_id, ref_id))
            conn.commit()
            
            # Повідомлення для нового учасника
            await bot.send_message(
                user_id,
                "🎉 <b>Вітаємо! Ви берете участь у розіграші призів!</b>\n\n"
                "<b>Призи:</b>\n"
                "1️⃣ Netflix + SWEET.TV на рік (1 пристрій)\n"
                "2️⃣ Spotify Premium на рік\n"
                "3️⃣ SWEET.TV на рік (1 пристрій)\n"
                "4️⃣ SWEET.TV на 6 місяців (1 пристрій)\n"
                "5️⃣ Промокод SWEET.TV на 1 місяць\n\n"
                f"Вас запросив: @{user_name}\n"
                "Запрошуйте друзів і збільшуйте свої шанси на перемогу! 🎁",
                parse_mode="HTML"
            )
            
            # Повідомлення для того, хто запросив
            await bot.send_message(
                ref_id,
                f"🎯 <b>Вітаємо! @{message.from_user.username if message.from_user.username else message.from_user.id} "
                f"приєднався за вашим запрошенням!</b>\n\n"
                "Ви отримали +1 шанс на перемогу в розіграші! 🎁\n"
                "Продовжуйте запрошувати друзів, щоб збільшити свої шанси!",
                parse_mode="HTML"
            )
        else:
            # Партнерське посилання: зберігаємо ref_id для нарахувань партнеру
            ref_id = int(args)
            try:
                user_name = get_user_name(ref_id) or str(ref_id)
            except (TypeError, IndexError):
                user_name = str(ref_id)
            await bot.send_message(
                user_id,
                f"<b>{get_premium_emoji('wave')} Вас запросив @{user_name}</b>\n\n"
                "Ласкаво просимо! Обирайте підписки у каталозі.",
                parse_mode="HTML",
            )
            await bot.send_message(
                ref_id,
                f"<b>{get_person_emoji_html()} Користувач @{message.from_user.username or message.from_user.id} перейшов за вашим посиланням.</b>\n\n"
                "Від кожної його покупки вам нараховуватиметься % на партнерський баланс.",
                parse_mode="HTML",
            )
    else:
        ref_id = None
    
    add_user(user_id, message.from_user.username, ref_id)
    await message.answer(get_greeting_message(), parse_mode="HTML", reply_markup=get_start_keyboard(user_id))



@router.message(F.text=="/help")
async def help(message: types.Message):
    await message.answer(
        text=get_help_text(),
        parse_mode="HTML"
    )
    

@router.callback_query(lambda c: c.data == "back_to_profile")
async def back_to_profile(callback: types.CallbackQuery):
    profile_text = await get_profile_text(callback.from_user.id, callback.from_user.username)
    await callback.message.edit_text(
        profile_text,
        parse_mode="HTML",
        reply_markup=get_profile_keyboard()
    )


@router.callback_query(lambda c: c.data == "my_subscriptions")
async def show_subscriptions(callback: types.CallbackQuery):
    # Перенаправляємо на детальне управління підписками з profile_handlers
    from handlers.client_handlers.profile_handlers import manage_subscriptions
    await manage_subscriptions(callback)
    
    
@router.message(F.text.in_(["Про нас", "/about"]))
async def about(message: types.Message):
    await message.answer(
        text=get_about_text(),
        reply_markup=get_socials_keyboard(),
        parse_mode="HTML"
    )
    
@router.message(F.text.in_(["Каталог", "/catalog"]))
async def catalog(message: types.Message):
    e = MENU_EMOJI_IDS["catalog"]
    await message.answer_photo(
        photo=FSInputFile(CATALOG_IMAGE_PATH),
        caption=f'<tg-emoji emoji-id="{e}">📂</tg-emoji> <b>Оберіть категорію підписки на сервіс:</b>',
        parse_mode="HTML",
        reply_markup=get_catalog_keyboard()
    )


@router.callback_query(F.data == "show_services")
async def show_services(callback: types.CallbackQuery):
    e = MENU_EMOJI_IDS["catalog"]
    await callback.message.answer_photo(
        photo=FSInputFile(CATALOG_IMAGE_PATH),
        caption=f'<tg-emoji emoji-id="{e}">📂</tg-emoji> <b>Оберіть категорію підписки на сервіс:</b>',
        parse_mode="HTML",
        reply_markup=get_catalog_keyboard()
    )


@router.message(F.text.in_(["Часті питання", "/faq"]))
async def faq(message: types.Message):
    await message.answer(
        text=get_faq_text(),
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    
    
@router.callback_query(F.data.startswith("category_"))
async def show_products(callback: types.CallbackQuery):
    catalog_id = int(callback.data.split("_")[1])
    await callback.message.edit_caption(
        caption=f"<b>{get_tv_emoji_html()} Оберіть підписку:</b>",
        parse_mode="HTML",
        reply_markup=get_products_keyboard(catalog_id)
    )

@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: types.CallbackQuery):
    photo = FSInputFile(CATALOG_IMAGE_PATH)
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=photo,
            caption=f"<b>{get_tv_emoji_html()} Оберіть категорію підписки на сервіс:</b>",
            parse_mode="HTML"
        ),
        reply_markup=get_catalog_keyboard()
    )


@router.message(F.text.in_(["Підтримка", "/support"]))
async def support(message: types.Message):
    await message.answer(
        text=get_manager_text(),
        parse_mode="HTML",
        reply_markup=get_manager_keyboard()
    )


@router.message(F.text.in_(["Партнерська програма", "/referral"]))
async def referral(message: types.Message):
    bot_name = await bot.get_me()
    user_id = message.from_user.id
    cursor.execute("SELECT COUNT(*) FROM users WHERE ref_id = ?", (user_id,))
    referral_count = cursor.fetchone()[0]
    balance = get_partner_balance(user_id)
    percent = get_partner_referral_percent()
    await message.answer(
        text=get_referral_text(bot_name.username, user_id, referral_count, balance, percent),
        reply_markup=get_referral_keyboard(bot_name.username, user_id),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "partner_history")
async def partner_history(callback: types.CallbackQuery):
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    user_id = callback.from_user.id
    history = get_partner_earnings_history(user_id, limit=20)
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Назад", callback_data="back_to_referral")],
    ])
    if not history:
        await callback.message.edit_text(
            f"{get_premium_emoji('box')} <b>Історія нарахувань</b>\n\nПоки немає нарахувань.",
            parse_mode="HTML",
            reply_markup=back_kb,
        )
        await callback.answer()
        return
    lines = []
    for buyer_id, purchase_amount, credit_amount, product_name, payment_type, created_at in history:
        pt = "підписка" if payment_type == "subscription" else "разова"
        name = format_product_name_for_display(product_name, max_text_len=30)
        buyer_un = get_user_name(buyer_id)
        buyer_display = escape(f"@{buyer_un}") if buyer_un and not str(buyer_un).isdigit() else escape(f"ID {buyer_id}")
        lines.append(
            f"• {format_date(created_at)} | +{credit_amount:.2f}₴ (з {purchase_amount:.2f}₴, {name}) — реферал {buyer_display} [{pt}]"
        )
    text = f"{get_premium_emoji('box')} <b>Історія нарахувань</b>\n\n" + "\n".join(lines)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_kb)
    await callback.answer()


@router.callback_query(F.data == "back_to_referral")
async def back_to_referral(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    bot_me = await bot.get_me()
    bot_username = bot_me.username
    cursor.execute("SELECT COUNT(*) FROM users WHERE ref_id = ?", (user_id,))
    referral_count = cursor.fetchone()[0]
    balance = get_partner_balance(user_id)
    percent = get_partner_referral_percent()
    await callback.message.edit_text(
        text=get_referral_text(bot_username, user_id, referral_count, balance, percent),
        parse_mode="HTML",
        reply_markup=get_referral_keyboard(bot_username, user_id),
    )
    await callback.answer()


@router.callback_query(F.data == "partner_withdraw")
async def partner_withdraw_start(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    balance = get_partner_balance(user_id)
    if balance <= 0:
        await callback.answer("На балансі немає коштів для виводу.", show_alert=True)
        return
    await state.set_state(WithdrawPartner.waiting_for_amount)
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="partner_withdraw_cancel")],
    ])
    await callback.message.edit_text(
        f"💸 <b>Запит на вивід</b>\n\n"
        f"Ваш баланс: <b>{balance:.2f} ₴</b>\n\n"
        f"Введіть суму для виводу (мінімум <b>{MIN_WITHDRAWAL} ₴</b>):",
        parse_mode="HTML",
        reply_markup=cancel_kb,
    )
    await callback.answer()


@router.callback_query(F.data == "partner_withdraw_cancel")
async def partner_withdraw_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Запит на вивід скасовано.",
        reply_markup=None,
    )
    await callback.answer()


@router.message(WithdrawPartner.waiting_for_amount, F.text)
async def partner_withdraw_amount(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        amount = float(message.text.replace(",", ".").strip())
    except ValueError:
        await message.answer("Введіть коректну суму (число).")
        return
    if amount < MIN_WITHDRAWAL:
        await message.answer(f"Мінімальна сума виводу — <b>{MIN_WITHDRAWAL} ₴</b>.", parse_mode="HTML")
        return
    balance = get_partner_balance(user_id)
    if amount > balance:
        await message.answer(f"На балансі недостатньо коштів. Доступно: {balance:.2f} ₴")
        return
    await state.update_data(withdraw_amount=amount)
    await state.set_state(WithdrawPartner.waiting_for_destination)
    await message.answer(
        "Куди вивести кошти? Напишіть, наприклад:\n"
        "• номер картки (наприклад 4149 **** **** 1234)\n"
        "• інші реквізити",
        parse_mode="HTML",
    )


@router.message(WithdrawPartner.waiting_for_destination, F.text)
async def partner_withdraw_destination(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    amount = data.get("withdraw_amount")
    if amount is None:
        await state.clear()
        await message.answer("Сесію скинуто. Почніть запит на вивід знову.")
        return
    destination = (message.text or "").strip()
    if not destination:
        await message.answer("Введіть реквізити для виводу (картка, телефон тощо).")
        return
    req_id = create_withdrawal_request(user_id, amount, payout_details=destination)
    await state.clear()
    if not req_id:
        await message.answer("Помилка створення запиту. Спробуйте пізніше.")
        return
    un = message.from_user.username
    user_line = f"Користувач: @{un} (ID: <code>{user_id}</code>)" if (un and un.strip()) else f"Користувач: ID <code>{user_id}</code> (прихований профіль)"
    try:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👤 Написати користувачу", url=f"tg://user?id={user_id}")],
            [
                InlineKeyboardButton(text="✅ Підтвердити", callback_data=f"admin_withdraw_done_{req_id}"),
                InlineKeyboardButton(text="❌ Відхилити", callback_data=f"admin_withdraw_reject_{req_id}"),
            ],
        ])
        await bot.send_message(
            admin_chat_id,
            f"💸 <b>Запит на вивід</b>\n\n"
            f"{get_person_emoji_html()} {user_line}\n"
            f"{get_premium_emoji('money')} Сума: <b>{amount:.2f} ₴</b>\n"
            f"📋 Куди вивести: <b>{escape(destination)}</b>\n"
            f"📋 ID запиту: <code>{req_id}</code>\n\n"
            f"<i>При підтвердженні баланс партнера буде списано.</i>",
            parse_mode="HTML",
            reply_markup=kb,
        )
    except Exception:
        pass
    await message.answer(
        f"{get_premium_emoji('check')} Запит на вивід <b>{amount:.2f} ₴</b> створено. Очікуйте обробки адміністратором.",
        parse_mode="HTML",
    )

@router.callback_query(F.data.startswith("product_"))
async def show_product_info(callback: types.CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    
    product = get_product_by_id(product_id)
    if not product:
        await callback.answer("Продукт не знайдено!", show_alert=True)
        return
    
    product_name, description, price, photo_path = product
    
    message_text = (
        f"<b>{product_name}</b>\n\n"
        f"{description}\n\n"
        f"Оберіть тариф:"
    )
    
    keyboard = get_product_info_keyboard(
        product_id=product_id,
        product_name=product_name,
        description=description,
        price_str=price
    )
    
    media_path = resolve_media_path(photo_path)
    if not media_path or not os.path.exists(media_path):
        media_path = CATALOG_IMAGE_PATH
    photo = FSInputFile(media_path)
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=photo,
            caption=message_text,
            parse_mode="HTML"
        ),
        reply_markup=keyboard
    )
    
    await callback.answer()


@router.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: types.CallbackQuery):
    _, product_id, months, price = callback.data.split("_")
    product_id, months, price = int(product_id), int(months), float(price)
    
    product = get_product_by_id(product_id)
    if not product:
        await callback.answer("Продукт не знайдено!", show_alert=True)
        return
    
    product_name, description, _, photo = product
    
    # Імпортуємо функцію для отримання типу оплати
    from database.admin_db import get_product_payment_type
    payment_type = get_product_payment_type(product_id)
    
    discounted_price = price
    if payment_type == "subscription":
        payment_text = (
            f"<b>Оформлення підписки</b>\n\n"
            f"Товар: <b>{product_name}</b>\n"
            f"Тариф: <b>{months} {'місяць' if months == 1 else 'місяці' if months in [2,3,4] else 'місяців'}</b>\n"
            f"Сума до сплати: <b>{price}₴</b>\n\n"
            f"<i>{get_calendar_emoji_html()} Це підписка з автоматичним списанням кожні {months} {'місяць' if months == 1 else 'місяці' if months in [2,3,4] else 'місяців'}.\n"
            f"Після першої оплати ваша картка буде збережена для подальших платежів.</i>"
        )
    else:
        payment_text = (
            f"<b>Оформлення замовлення</b>\n\n"
            f"Товар: <b>{product_name}</b>\n"
            f"Тариф: <b>{months} {'місяць' if months == 1 else 'місяці' if months in [2,3,4] else 'місяців'}</b>\n"
            f"Сума до сплати: <b>{price}₴</b>\n\n"
            f"<i>{get_premium_emoji('card')} Одноразова оплата. Після оплати з вами зв'яжеться менеджер для підключення.</i>"
        )
    
    # Для підписки потрібно погодження з умовами автосплати
    if payment_type == "subscription":
        # Показуємо умови автосплати
        subscription_terms_text = (
            f"📝 <b>Умови автоматичної підписки</b>\n\n"
            f"Товар: <b>{product_name}</b>\n"
            f"Тариф: <b>{months} {'місяць' if months == 1 else 'місяці' if months in [2,3,4] else 'місяців'}</b>\n"
            f"Сума: <b>{discounted_price}₴</b>\n\n"
            f"<b>⚠️ Важливо:</b>\n"
            f"• Після успішної оплати буде активована автоматична підписка\n"
            f"• Кошти будуть автоматично списуватися кожні {months} {'місяць' if months == 1 else 'місяці' if months in [2,3,4] else 'місяців'}\n"
            f"• Ваша картка буде збережена для подальших платежів\n"
            f"• Ви можете скасувати підписку в будь-який час у своєму профілі\n"
            f"• При скасуванні підписки доступ зберігається до кінця оплаченого періоду\n\n"
            f"Продовжуючи, ви погоджуєтеся з умовами автоматичної підписки."
        )
        
        from keyboards.client_keyboards import get_subscription_terms_keyboard
        
        await callback.message.edit_caption(
            caption=subscription_terms_text,
            reply_markup=get_subscription_terms_keyboard(product_id, months, discounted_price),
            parse_mode="HTML"
        )
    else:
        user_id = callback.from_user.id
        balance = get_partner_balance(user_id)
        if balance >= discounted_price:
            choice_text = (
                payment_text + f"\n\n{get_premium_emoji('money')} <b>Ваш партнерський баланс:</b> " + "{:.2f} ₴\n"
                "Можете сплатити з балансу або карткою."
            ).format(balance)
            await callback.message.edit_caption(
                caption=choice_text,
                reply_markup=get_payment_choice_keyboard(product_id, months, discounted_price),
                parse_mode="HTML",
            )
        else:
            local_payment_id, invoice_id, payment_link = payment_manager.create_payment(
                user_id=user_id,
                product_name=product_name,
                months=months,
                price=discounted_price,
            )
            save_payment_info(
                payment_id=local_payment_id,
                invoice_id=invoice_id,
                user_id=user_id,
                product_id=product_id,
                months=months,
                amount=discounted_price,
                status="pending",
                payment_type=payment_type,
            )
            await callback.message.edit_caption(
                caption=payment_text,
                reply_markup=get_payment_keyboard(payment_link, product_id),
                parse_mode="HTML",
            )
    
    await callback.answer()


@router.callback_query(F.data.startswith("one_time_card_"))
async def one_time_pay_card(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    product_id, months, price = int(parts[3]), int(parts[4]), float(parts[5])
    product = get_product_by_id(product_id)
    if not product:
        await callback.answer("Продукт не знайдено!", show_alert=True)
        return
    product_name, description, _, photo = product
    user_id = callback.from_user.id
    local_payment_id, invoice_id, payment_link = payment_manager.create_payment(
        user_id=user_id,
        product_name=product_name,
        months=months,
        price=price,
    )
    save_payment_info(
        payment_id=local_payment_id,
        invoice_id=invoice_id,
        user_id=user_id,
        product_id=product_id,
        months=months,
        amount=price,
        status="pending",
        payment_type="one_time",
    )
    payment_text = (
        f"<b>Оформлення замовлення</b>\n\n"
        f"Товар: <b>{product_name}</b>\n"
        f"Тариф: <b>{months} {'місяць' if months == 1 else 'місяці' if months in [2,3,4] else 'місяців'}</b>\n"
        f"Сума до сплати: <b>{price}₴</b>\n\n"
        f"<i>{get_premium_emoji('card')} Оплата карткою.</i>"
    )
    await callback.message.edit_caption(
        caption=payment_text,
        reply_markup=get_payment_keyboard(payment_link, product_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pay_balance_"))
async def pay_with_balance(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    product_id, months, price = int(parts[2]), int(parts[3]), float(parts[4])
    product = get_product_by_id(product_id)
    if not product:
        await callback.answer("Продукт не знайдено!", show_alert=True)
        return
    product_name, description, _, photo = product
    user_id = callback.from_user.id
    if get_partner_balance(user_id) < price:
        await callback.answer("Недостатньо коштів на балансі.", show_alert=True)
        return
    if not deduct_partner_balance(user_id, price):
        await callback.answer("Помилка списання.", show_alert=True)
        return
    from datetime import timedelta
    start_date = datetime.now()
    end_date = start_date + timedelta(days=30 * months)
    product_type = get_product_type(product_id)
    add_subscription(
        user_id=user_id,
        product_type=product_type,
        product_id=product_id,
        product_name=product_name,
        price=price,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        status="active",
    )
    await callback.message.edit_caption(
        caption=(
            f"{get_premium_emoji('check')} <b>Оплата з балансу успішна!</b>\n\n"
            f"• Підписка: {product_name}\n"
            f"• Термін: {months} {'місяць' if months == 1 else 'місяці' if months in [2,3,4] else 'місяців'}\n"
            f"• Сплачено: {price} ₴ з партнерського балансу\n\n"
            "Зачекайте поки з вами зв'яжеться менеджер для підключення."
        ),
        reply_markup=None,
        parse_mode="HTML",
    )
    await callback.answer()
    try:
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
        un = callback.from_user.username
        pay_user_line = f"Користувач: @{un} (ID: <code>{user_id}</code>)" if (un and un.strip()) else f"Користувач: ID <code>{user_id}</code> (прихований профіль)"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👤 Написати", url=f"tg://user?id={user_id}")],
        ])
        await bot.send_message(
            admin_chat_id,
            f"{get_premium_emoji('money')} <b>Оплата з балансу</b>\n\n"
            f"{pay_user_line}\n"
            f"Товар: {product_name}\n"
            f"Сума: {price} ₴\n"
            f"До: {end_date.strftime('%d.%m.%Y')}",
            parse_mode="HTML",
            reply_markup=kb,
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("agree_subscription_"))
async def agree_subscription_terms(callback: types.CallbackQuery):
    _, _, product_id, months, price = callback.data.split("_")
    product_id, months, price = int(product_id), int(months), float(price)
    
    product = get_product_by_id(product_id)
    if not product:
        await callback.answer("Продукт не знайдено!", show_alert=True)
        return
    
    product_name, description, _, photo = product
    
    # Створюємо платіж підписки
    local_payment_id, invoice_id, payment_link, wallet_id = payment_manager.create_payment_with_tokenization(
        user_id=callback.from_user.id,
        product_name=product_name,
        months=months,
        price=price
    )
    
    print(f"Створено платіж підписки: local_payment_id={local_payment_id}, invoice_id={invoice_id}, wallet_id={wallet_id}")
    
    # Зберігаємо wallet_id для подальшого використання
    cursor.execute("""
        INSERT OR REPLACE INTO payments_temp_data (invoice_id, wallet_id, payment_type, local_payment_id)
        VALUES (?, ?, ?, ?)
    """, (invoice_id, wallet_id, "subscription", local_payment_id))
    conn.commit()
    
    print(f"Збережено тимчасові дані для платежу {local_payment_id}")
    
    save_payment_info(
        payment_id=local_payment_id,
        invoice_id=invoice_id,
        user_id=callback.from_user.id,
        product_id=product_id,
        months=months,
        amount=price,
        status="pending",
        payment_type="subscription"
    )
    
    payment_text = (
        f"<b>Оформлення підписки</b>\n\n"
        f"Товар: <b>{product_name}</b>\n"
        f"Тариф: <b>{months} {'місяць' if months == 1 else 'місяці' if months in [2,3,4] else 'місяців'}</b>\n"
        f"Сума до сплати: <b>{price}₴</b>\n\n"
        f"<i>{get_calendar_emoji_html()} Після оплати буде активована автоматична підписка.</i>"
    )
    
    await callback.message.edit_caption(
        caption=payment_text,
        reply_markup=get_payment_keyboard(payment_link, product_id),
        parse_mode="HTML"
    )
    
    await callback.answer()
 


async def on_startup(router):
    me = await bot.get_me()
    await scheduler_jobs()
    if admin_chat_id:
        try:
            await bot.get_chat(admin_chat_id)
        except Exception as e:
            if "chat not found" in str(e).lower() or "400" in str(e):
                print(
                    f"⚠️ ADMIN_CHAT_ID={admin_chat_id}: чат не знайдено. Додайте бота в групу та перевірте ID. "
                    "Як отримати ID: додайте бота в групу → надішліть повідомлення в групу → https://api.telegram.org/bot<TOKEN>/getUpdates — у відповіді chat.id."
                )
            else:
                print(f"⚠️ ADMIN_CHAT_ID перевірка: {e}")
    print(f'Bot: @{me.username} запущений!')


async def on_shutdown(router):
    me = await bot.get_me()
    print(f'Bot: @{me.username} зупинений!')
