import asyncio
import logging
from datetime import datetime, timedelta
from database.client_db import get_active_subscriptions, get_active_recurring_subscriptions, get_user_token, update_subscription_next_payment, increment_payment_failures, deactivate_subscription, save_subscription_payment, get_ref_id_by_user, add_partner_credit, get_partner_referral_percent, get_username_by_id
from database.links_db import track_link_purchase
from ulits.monopay_functions import PaymentManager
from Content.texts import get_premium_emoji
from Content.texts import (
    get_partner_referral_purchase_text,
    get_user_auto_payment_success_text,
    get_admin_auto_payment_success_text,
    get_user_auto_payment_failed_text,
    get_admin_auto_payment_failed_text,
    get_user_token_invalid_text,
    get_admin_token_invalid_text,
    get_user_subscription_cancelled_text,
    get_admin_subscription_cancelled_text,
)
from keyboards.admin_keyboards import get_write_to_user_keyboard
from main import bot
from keyboards.client_keyboards import get_services_keyboard
from ulits.client_functions import get_days_word
from config import administrators, admin_chat_id
import time


async def check_expiring_subscriptions():
    try:
        today = datetime.now().date()
        subscriptions = get_active_subscriptions()
        
        for sub in subscriptions:
            user_id = sub['user_id']
            product_name = sub['product_name']
            end_date = datetime.strptime(sub['end_date'], '%Y-%m-%d').date()
            
            days_left = (end_date - today).days
            
            if 0 < days_left <= 5:
                days_word = get_days_word(days_left)
                message_text = (
                    f"<b>Ваша підписка на {product_name} закінчиться через {days_left} {days_word}!</b>\n\n"
                    f"Не забудьте поновити підписку, щоб продовжити користуватися сервісом!"
                )
                
                await bot.send_message(
                    user_id,
                    message_text,
                    parse_mode="HTML",
                    reply_markup=get_services_keyboard()
                )
            
            elif days_left == 0:
                message_text = (
                    f"❌ <b>Ваша підписка на {product_name} закінчилась!</b>\n\n"
                    f"Для продовження користування сервісом необхідно поновити підписку."
                )
                
                await bot.send_message(
                    user_id,
                    message_text,
                    parse_mode="HTML",
                    reply_markup=get_services_keyboard()
                )
                
    except Exception as e:
        print(f"Помилка при перевірці підписок: {e}")


async def process_recurring_payments():
    try:
        logging.info("🔄 Початок обробки повторюваних платежів")
        payment_manager = PaymentManager()
        subscriptions = get_active_recurring_subscriptions()
        logging.info(f"📋 Знайдено {len(subscriptions)} активних повторюваних підписок")
        print(subscriptions)
        
        for subscription in subscriptions:
            subscription_id, user_id, product_id, product_name, months, price, wallet_id, next_payment_date = subscription
            logging.info(f"💳 Обробка підписки {subscription_id} для користувача {user_id} ({product_name})")
            
            try:
                # Отримуємо токен картки користувача
                logging.info(f"🔑 Отримання токену картки для користувача {user_id}")
                token_data = get_user_token(user_id)
                if not token_data:
                    logging.error(f"❌ Токен не знайдено для користувача {user_id}")
                    await increment_payment_failures(subscription_id)
                    continue
                
                wallet_id_db, card_token, masked_card, card_type = token_data
                logging.info(f"✅ Токен знайдено: wallet_id={wallet_id_db}, masked_card={masked_card}, card_type={card_type}")
                
                # Створюємо платіж по токену
                logging.info(f"💳 Створення платежу по токену для підписки {subscription_id}")
                try:
                    local_payment_id, invoice_id = payment_manager.create_token_payment(
                        wallet_id=wallet_id_db,
                        card_token=card_token,
                        product_name=product_name,
                        months=months,
                        price=price
                    )
                    logging.info(f"✅ Платіж створено: local_payment_id={local_payment_id}, invoice_id={invoice_id}")
                except Exception as payment_error:
                    # Обробляємо помилки створення платежу
                    error_message = str(payment_error)
                    logging.error(f"❌ Помилка створення платежу для підписки {subscription_id}: {error_message}")
                    
                    # Парсимо помилку з JSON, якщо вона є
                    err_code = None
                    err_text = None
                    
                    try:
                        import json
                        # Шукаємо JSON в повідомленні помилки
                        if 'errCode' in error_message or 'errText' in error_message:
                            # Спробуємо витягнути JSON з повідомлення
                            if '{' in error_message:
                                json_start = error_message.find('{')
                                json_end = error_message.rfind('}') + 1
                                if json_start < json_end:
                                    error_json = json.loads(error_message[json_start:json_end])
                                    err_code = error_json.get('errCode')
                                    err_text = error_json.get('errText', error_message)
                    except:
                        pass
                    
                    # Якщо не вдалося розпарсити, використовуємо повне повідомлення
                    if not err_code:
                        err_code = 'UNKNOWN_ERROR'
                        err_text = error_message
                    
                    logging.warning(f"📋 Код помилки: {err_code}, Текст: {err_text}")
                    
                    # Зберігаємо помилку в базу даних
                    save_subscription_payment(
                        subscription_id=subscription_id,
                        user_id=user_id,
                        amount=price,
                        status='failed',
                        invoice_id=None,
                        payment_id=None,
                        error_message=f"{err_code}: {err_text}"
                    )
                    
                    # Обробляємо різні типи помилок
                    if err_code == 'TOKEN_NOT_FOUND':
                        # Токен не знайдено - деактивуємо підписку, бо токен не дійсний
                        logging.error(f"🚫 Токен картки не знайдено для підписки {subscription_id}. Деактивуємо підписку.")
                        deactivate_subscription(subscription_id)
                        await notify_user_token_invalid(user_id, product_name, masked_card, err_text)
                    elif err_code == 'ERROR_VISA' or 'no longer allowed' in err_text:
                        # Картка заблокована - збільшуємо лічильник помилок
                        logging.warning(f"⚠️ Картка заблокована для підписки {subscription_id}")
                        increment_payment_failures(subscription_id)
                        await notify_user_payment_failed(
                            user_id=user_id,
                            product_name=product_name,
                            masked_card=masked_card,
                            invoice_id=None,
                            card_token=None,
                            failure_reason=err_text
                        )
                    else:
                        # Інші помилки - збільшуємо лічильник помилок
                        increment_payment_failures(subscription_id)
                        await notify_user_payment_failed(
                            user_id=user_id,
                            product_name=product_name,
                            masked_card=masked_card,
                            invoice_id=None,
                            card_token=None,
                            failure_reason=err_text
                        )
                    
                    # Перевіряємо ліміт помилок
                    from database.client_db import cursor
                    cursor.execute("""
                        SELECT payment_failures FROM recurring_subscriptions WHERE id = ?
                    """, (subscription_id,))
                    result = cursor.fetchone()
                    current_failures = result[0] if result else 0
                    
                    if current_failures >= 3:
                        logging.warning(f"🚫 Підписка {subscription_id} деактивується через перевищення ліміту помилок")
                        deactivate_subscription(subscription_id)
                        await notify_user_subscription_cancelled(user_id, product_name)
                    
                    continue  # Переходимо до наступної підписки
                
                # Чекаємо трохи перед перевіркою статусу (платіж може бути ще не готовий)
                await asyncio.sleep(2)
                
                # Перевіряємо статус платежу з повторними спробами
                max_attempts = 5
                attempt = 0
                payment_status = None
                final_status = None
                
                while attempt < max_attempts:
                    attempt += 1
                    logging.info(f"🔍 Перевірка статусу платежу {invoice_id} (спроба {attempt}/{max_attempts})")
                    
                    try:
                        payment_status = payment_manager.get_payment_status(invoice_id)
                        current_status = payment_status.get('status')
                        modified_date = payment_status.get('modifiedDate')
                        
                        logging.info(f"📊 Статус платежу: {current_status}, modifiedDate: {modified_date}")
                        
                        # Якщо платіж завершений (success або failure), виходимо з циклу
                        if current_status in ['success', 'failure', 'expired']:
                            final_status = current_status
                            break
                        # Якщо платіж в обробці, чекаємо і перевіряємо знову
                        elif current_status == 'processing':
                            if attempt < max_attempts:
                                wait_time = min(5 * attempt, 30)  # Збільшуємо час очікування з кожною спробою
                                logging.info(f"⏳ Платіж в обробці, чекаємо {wait_time} секунд перед наступною перевіркою")
                                await asyncio.sleep(wait_time)
                            else:
                                final_status = 'processing'
                                break
                        else:
                            logging.warning(f"❓ Невідомий статус: {current_status}")
                            final_status = current_status
                            break
                            
                    except Exception as e:
                        logging.error(f"❌ Помилка при перевірці статусу платежу: {e}")
                        if attempt < max_attempts:
                            await asyncio.sleep(5)
                        else:
                            raise
                
                if not payment_status:
                    logging.error(f"❌ Не вдалося отримати статус платежу {invoice_id} після {max_attempts} спроб")
                    save_subscription_payment(
                        subscription_id=subscription_id,
                        user_id=user_id,
                        amount=price,
                        status='error',
                        invoice_id=invoice_id,
                        payment_id=local_payment_id,
                        error_message=f"Не вдалося отримати статус після {max_attempts} спроб"
                    )
                    increment_payment_failures(subscription_id)
                    continue
                
                # Витягуємо детальну інформацію з payment_status для перевірки
                payment_info = payment_status.get('paymentInfo', {})
                status_masked_card = payment_info.get('maskedPan') or masked_card
                status_card_type = payment_info.get('paymentSystem', card_type)
                modified_date = payment_status.get('modifiedDate')
                
                # Логуємо всі дані для діагностики
                logging.info(f"💳 Дані платежу: invoice_id={invoice_id}, masked_card={status_masked_card}, card_type={status_card_type}")
                logging.info(f"🔑 Токен картки (частково): {card_token[:8] + '...' + card_token[-4:] if card_token and len(card_token) > 12 else 'N/A'}")
                logging.info(f"📅 ModifiedDate: {modified_date}")
                
                current_status = payment_status.get('status')
                
                if current_status == 'success':
                    # Успішний платіж
                    logging.info(f"✅ Успішний платіж для підписки {subscription_id}")
                    save_subscription_payment(
                        subscription_id=subscription_id,
                        user_id=user_id,
                        amount=price,
                        status='success',
                        invoice_id=invoice_id,
                        payment_id=local_payment_id
                    )
                    
                    # Оновлюємо дату наступного платежу
                    logging.info(f"📅 Оновлення дати наступного платежу для підписки {subscription_id}")
                    update_subscription_next_payment(subscription_id, months)
                    track_link_purchase(user_id)

                    ref_id = get_ref_id_by_user(user_id)
                    if ref_id:
                        add_partner_credit(
                            partner_id=ref_id,
                            buyer_id=user_id,
                            purchase_amount=price,
                            product_name=product_name,
                            payment_type="subscription",
                        )
                        credit_amount = round(price * (get_partner_referral_percent() / 100), 1)
                        if credit_amount > 0:
                            buyer_username = get_username_by_id(user_id)
                            buyer_line = f"@{buyer_username}" if (buyer_username and str(buyer_username).strip()) else f"користувач (ID: {user_id}, прихований профіль)"
                            try:
                                await bot.send_message(
                                    ref_id,
                                    get_partner_referral_purchase_text(buyer_line, product_name, price, credit_amount),
                                    parse_mode="HTML",
                                )
                            except Exception:
                                pass

                    # Повідомляємо користувача про успішний платіж з усіма даними для перевірки
                    logging.info(f"📱 Відправка повідомлення користувачу {user_id} про успішний платіж")
                    await notify_user_payment_success(
                        user_id=user_id, 
                        product_name=product_name, 
                        amount=price, 
                        months=months,
                        invoice_id=invoice_id,
                        masked_card=status_masked_card,
                        card_token=card_token
                    )
                    
                    logging.info(f"✅ Успішний платіж для підписки {subscription_id}, користувач {user_id}, invoice_id={invoice_id}")
                
                elif current_status == 'processing':
                    # Платіж в обробці - НЕ оновлюємо дату наступного платежу, бо платіж ще не завершений
                    # Зберігаємо інформацію про платіж для подальшої перевірки
                    logging.warning(f"⏳ Платіж {invoice_id} для підписки {subscription_id} все ще в обробці після {max_attempts} спроб")
                    save_subscription_payment(
                        subscription_id=subscription_id,
                        user_id=user_id,
                        amount=price,
                        status='processing',
                        invoice_id=invoice_id,
                        payment_id=local_payment_id
                    )
                    # НЕ оновлюємо дату наступного платежу - платіж ще не завершений
                    # Платіж буде перевірений при наступному запуску cron або через webhook
                    logging.info(f"⏳ Платіж {invoice_id} залишається в обробці, дата наступного платежу НЕ оновлена")
                    
                elif current_status == 'failure':
                    # Невдалий платіж
                    failure_reason = payment_status.get('failureReason', 'Невідома помилка')
                    logging.warning(f"❌ Невдалий платіж для підписки {subscription_id}: {failure_reason}")
                    
                    save_subscription_payment(
                        subscription_id=subscription_id,
                        user_id=user_id,
                        amount=price,
                        status='failed',
                        invoice_id=invoice_id,
                        payment_id=local_payment_id,
                        error_message=failure_reason
                    )
                    
                    # Збільшуємо лічильник помилок
                    logging.info(f"⚠️ Збільшення лічильника помилок для підписки {subscription_id}")
                    increment_payment_failures(subscription_id)
                    
                    # Перевіряємо, чи не перевищено ліміт помилок
                    current_failures = payment_status.get('payment_failures', 0)
                    logging.info(f"📊 Поточні помилки: {current_failures}/3")
                    
                    if current_failures >= 3:
                        logging.warning(f"🚫 Підписка {subscription_id} деактивується через перевищення ліміту помилок")
                        deactivate_subscription(subscription_id)
                        await notify_user_subscription_cancelled(user_id, product_name)
                        logging.warning(f"❌ Підписка {subscription_id} деактивована через багато помилок")
                    else:
                        logging.info(f"📱 Відправка повідомлення користувачу {user_id} про невдалий платіж")
                        await notify_user_payment_failed(
                            user_id=user_id, 
                            product_name=product_name, 
                            masked_card=status_masked_card,
                            invoice_id=invoice_id,
                            card_token=card_token,
                            failure_reason=failure_reason
                        )
                        logging.warning(f"⚠️ Невдалий платіж для підписки {subscription_id}, invoice_id={invoice_id}")
                
                elif current_status == 'expired':
                    # Рахунок застарів - обробляємо як невдалий платіж
                    logging.warning(f"⏰ Рахунок {invoice_id} для підписки {subscription_id} застарів")
                    save_subscription_payment(
                        subscription_id=subscription_id,
                        user_id=user_id,
                        amount=price,
                        status='failed',
                        invoice_id=invoice_id,
                        payment_id=local_payment_id,
                        error_message='Рахунок застарів'
                    )
                    increment_payment_failures(subscription_id)
                    await notify_user_payment_failed(
                        user_id=user_id,
                        product_name=product_name,
                        masked_card=status_masked_card,
                        invoice_id=invoice_id,
                        card_token=card_token,
                        failure_reason='Рахунок застарів'
                    )
                    logging.warning(f"⏰ Рахунок {invoice_id} застарів, підписка {subscription_id}")
                
                else:
                    logging.warning(f"❓ Невідомий статус платежу: {current_status}")
                    save_subscription_payment(
                        subscription_id=subscription_id,
                        user_id=user_id,
                        amount=price,
                        status='error',
                        invoice_id=invoice_id,
                        payment_id=local_payment_id,
                        error_message=f"Невідомий статус: {current_status}"
                    )
                    increment_payment_failures(subscription_id)
                
            except Exception as e:
                logging.error(f"💥 Помилка при обробці підписки {subscription_id}: {e}")
                save_subscription_payment(
                    subscription_id=subscription_id,
                    user_id=user_id,
                    amount=price,
                    status='error',
                    error_message=str(e)
                )
                increment_payment_failures(subscription_id)
                
        logging.info("✅ Завершено обробку повторюваних платежів")
                
    except Exception as e:
        logging.error(f"💥 Помилка при обробці повторюваних платежів: {e}")


async def notify_user_payment_success(user_id: int, product_name: str, amount: float, months: int,
                                     invoice_id: str = None, masked_card: str = None, card_token: str = None):
    try:
        next_date_str = (datetime.now() + timedelta(days=30 * months)).strftime('%d.%m.%Y')
        await bot.send_message(
            user_id,
            get_user_auto_payment_success_text(product_name, amount, months, next_date_str),
            parse_mode="HTML",
        )
        username = get_username_by_id(user_id)
        card_info = f"{get_premium_emoji('card')} <b>Картка:</b> <code>{masked_card}</code>\n" if masked_card else ""
        token_info = ""
        if card_token:
            token_preview = card_token[:8] + "..." + card_token[-4:] if len(card_token) > 12 else card_token[:8] + "..."
            token_info = f"🔑 <b>Токен:</b> <code>{token_preview}</code>\n"
        invoice_info = f"📄 <b>Invoice ID:</b> <code>{invoice_id}</code>\n" if invoice_id else ""

        try:
            await bot.send_message(
                admin_chat_id,
                get_admin_auto_payment_success_text(
                    user_id, username, product_name, amount, months, next_date_str,
                    invoice_info, card_info, token_info,
                ),
                parse_mode="HTML",
                reply_markup=get_write_to_user_keyboard(user_id),
            )
        except Exception as e:
            logging.error(f"Помилка при відправці повідомлення адміну про автоматичний платіж: {e}")
            
    except Exception as e:
        logging.error(f"Помилка при надсиланні повідомлення про успішний платіж: {e}")


async def notify_user_payment_failed(user_id: int, product_name: str, masked_card: str,
                                     invoice_id: str = None, card_token: str = None,
                                     failure_reason: str = None):
    try:
        await bot.send_message(
            user_id,
            get_user_auto_payment_failed_text(product_name, masked_card),
            parse_mode="HTML",
        )
        username = get_username_by_id(user_id)
        invoice_info = f"📄 <b>Invoice ID:</b> <code>{invoice_id}</code>\n" if invoice_id else ""
        token_info = ""
        if card_token:
            token_preview = card_token[:8] + "..." + card_token[-4:] if len(card_token) > 12 else card_token[:8] + "..."
            token_info = f"🔑 <b>Токен:</b> <code>{token_preview}</code>\n"
        reason_info = f"⚠️ <b>Причина:</b> {failure_reason}\n" if failure_reason else ""

        try:
            await bot.send_message(
                admin_chat_id,
                get_admin_auto_payment_failed_text(
                    user_id, username, product_name, masked_card,
                    invoice_info, token_info, reason_info,
                ),
                parse_mode="HTML",
                reply_markup=get_write_to_user_keyboard(user_id),
            )
        except Exception as e:
            logging.error(f"Помилка при відправці повідомлення адміну про невдалий платіж: {e}")
            
    except Exception as e:
        logging.error(f"Помилка при надсиланні повідомлення про невдалий платіж: {e}")


async def notify_user_token_invalid(user_id: int, product_name: str, masked_card: str, error_text: str):
    """Повідомляє користувача про невалідний токен картки"""
    try:
        await bot.send_message(
            user_id,
            get_user_token_invalid_text(product_name, masked_card),
            parse_mode="HTML",
        )
        username = get_username_by_id(user_id)
        try:
            await bot.send_message(
                admin_chat_id,
                get_admin_token_invalid_text(user_id, username, product_name, masked_card, error_text),
                parse_mode="HTML",
                reply_markup=get_write_to_user_keyboard(user_id),
            )
        except Exception as e:
            logging.error(f"Помилка при відправці повідомлення адміну про невалідний токен: {e}")
            
    except Exception as e:
        logging.error(f"Помилка при надсиланні повідомлення про невалідний токен: {e}")


async def notify_user_subscription_cancelled(user_id: int, product_name: str):
    try:
        await bot.send_message(
            user_id,
            get_user_subscription_cancelled_text(product_name),
            parse_mode="HTML",
        )
        username = get_username_by_id(user_id)
        try:
            await bot.send_message(
                admin_chat_id,
                get_admin_subscription_cancelled_text(user_id, username, product_name),
                parse_mode="HTML",
                reply_markup=get_write_to_user_keyboard(user_id),
            )
        except Exception as e:
            logging.error(f"Помилка при відправці повідомлення адміну про скасування підписки: {e}")
            
    except Exception as e:
        logging.error(f"Помилка при надсиланні повідомлення про скасування підписки: {e}")


async def notify_admins_subscription_stats():
    try:
        from database.client_db import cursor
        
        cursor.execute("SELECT COUNT(*) FROM recurring_subscriptions WHERE status = 'active'")
        active_subscriptions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM subscription_payments WHERE status = 'success' AND DATE(payment_date) = DATE('now')")
        successful_payments_today = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM subscription_payments WHERE status = 'failed' AND DATE(payment_date) = DATE('now')")
        failed_payments_today = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(amount) FROM subscription_payments WHERE status = 'success' AND DATE(payment_date) = DATE('now')")
        revenue_today = cursor.fetchone()[0] or 0
        
        message = (
            f"{get_premium_emoji('chart')} <b>Статистика підписок</b>\n\n"
            f"Активних підписок: <b>{active_subscriptions}</b>\n"
            f"Успішних платежів сьогодні: <b>{successful_payments_today}</b>\n"
            f"Невдалих платежів сьогодні: <b>{failed_payments_today}</b>\n"
            f"Дохід сьогодні: <b>{revenue_today:.2f}₴</b>"
        )
        
        for admin_id in administrators:
            try:
                await bot.send_message(admin_id, message, parse_mode="HTML")
            except Exception as e:
                logging.error(f"Помилка при надсиланні статистики адміну {admin_id}: {e}")
                
    except Exception as e:
        logging.error(f"Помилка при формуванні статистики підписок: {e}")


async def check_processing_payments():
    """Перевіряє платежі, які залишилися в статусі processing"""
    try:
        from database.client_db import cursor, conn, get_user_token, update_subscription_next_payment, increment_payment_failures
        from ulits.monopay_functions import PaymentManager
        
        logging.info("🔍 Перевірка платежів в статусі processing...")
        
        # Знаходимо платежі в статусі processing, які створені більше 5 хвилин тому
        cursor.execute("""
            SELECT sp.id, sp.subscription_id, sp.user_id, sp.invoice_id, sp.payment_id, sp.amount,
                   rs.product_name, rs.months, rs.price
            FROM subscription_payments sp
            JOIN recurring_subscriptions rs ON sp.subscription_id = rs.id
            WHERE sp.status = 'processing'
            AND datetime(sp.created_at) < datetime('now', '-5 minutes')
            ORDER BY sp.created_at ASC
            LIMIT 20
        """)
        
        processing_payments = cursor.fetchall()
        logging.info(f"📋 Знайдено {len(processing_payments)} платежів в статусі processing для перевірки")
        
        payment_manager = PaymentManager()
        
        for payment in processing_payments:
            payment_db_id, subscription_id, user_id, invoice_id, local_payment_id, amount, product_name, months, price = payment
            
            try:
                logging.info(f"🔍 Перевірка платежу {invoice_id} для підписки {subscription_id}")
                payment_status = payment_manager.get_payment_status(invoice_id)
                current_status = payment_status.get('status')
                
                logging.info(f"📊 Статус платежу {invoice_id}: {current_status}")
                
                if current_status == 'success':
                    # Платіж успішний - оновлюємо статус
                    logging.info(f"✅ Платіж {invoice_id} тепер успішний!")
                    
                    # Оновлюємо статус платежу в БД
                    cursor.execute("""
                        UPDATE subscription_payments 
                        SET status = 'success', payment_date = datetime('now')
                        WHERE id = ?
                    """, (payment_db_id,))
                    conn.commit()
                    
                    # Оновлюємо дату наступного платежу
                    update_subscription_next_payment(subscription_id, months)
                    track_link_purchase(user_id)

                    ref_id = get_ref_id_by_user(user_id)
                    if ref_id:
                        add_partner_credit(
                            partner_id=ref_id,
                            buyer_id=user_id,
                            purchase_amount=price,
                            product_name=product_name,
                            payment_type="subscription",
                        )
                        credit_amount = round(price * (get_partner_referral_percent() / 100), 1)
                        if credit_amount > 0:
                            buyer_username = get_username_by_id(user_id)
                            buyer_line = f"@{buyer_username}" if (buyer_username and str(buyer_username).strip()) else f"користувач (ID: {user_id}, прихований профіль)"
                            try:
                                await bot.send_message(
                                    ref_id,
                                    get_partner_referral_purchase_text(buyer_line, product_name, price, credit_amount),
                                    parse_mode="HTML",
                                )
                            except Exception:
                                pass

                    # Отримуємо дані про картку
                    token_data = get_user_token(user_id)
                    masked_card = token_data[2] if token_data else "**** **** **** ****"
                    card_token = token_data[1] if token_data else None

                    # Повідомляємо користувача та адміна
                    await notify_user_payment_success(
                        user_id=user_id,
                        product_name=product_name,
                        amount=price,
                        months=months,
                        invoice_id=invoice_id,
                        masked_card=masked_card,
                        card_token=card_token
                    )
                    
                elif current_status == 'failure':
                    # Платіж невдалий - оновлюємо статус
                    logging.warning(f"❌ Платіж {invoice_id} невдалий")
                    
                    failure_reason = payment_status.get('failureReason', 'Невідома помилка')
                    
                    cursor.execute("""
                        UPDATE subscription_payments 
                        SET status = 'failed', error_message = ?
                        WHERE id = ?
                    """, (failure_reason, payment_db_id))
                    conn.commit()
                    
                    increment_payment_failures(subscription_id)
                    
                    token_data = get_user_token(user_id)
                    masked_card = token_data[2] if token_data else "**** **** **** ****"
                    card_token = token_data[1] if token_data else None
                    
                    await notify_user_payment_failed(
                        user_id=user_id,
                        product_name=product_name,
                        masked_card=masked_card,
                        invoice_id=invoice_id,
                        card_token=card_token,
                        failure_reason=failure_reason
                    )
                    
                elif current_status == 'expired':
                    # Рахунок застарів
                    logging.warning(f"⏰ Рахунок {invoice_id} застарів")
                    
                    cursor.execute("""
                        UPDATE subscription_payments 
                        SET status = 'failed', error_message = 'Рахунок застарів'
                        WHERE id = ?
                    """, (payment_db_id,))
                    conn.commit()
                    
                    increment_payment_failures(subscription_id)
                    
                # Якщо все ще processing - залишаємо як є, перевіримо пізніше
                
            except Exception as e:
                logging.error(f"❌ Помилка при перевірці платежу {invoice_id}: {e}")
                continue
        
        logging.info("✅ Завершено перевірку платежів в статусі processing")
        
    except Exception as e:
        logging.error(f"💥 Помилка при перевірці processing платежів: {e}")


# Функція для запуску cron завдань
async def run_subscription_cron():
    """Запускає cron завдання для обробки підписок"""
    while True:
        try:
            await process_recurring_payments()
            # Також перевіряємо платежі, які залишилися в processing
            await check_processing_payments()
            await asyncio.sleep(3600)  # Перевіряємо кожну годину
        except Exception as e:
            logging.error(f"Помилка в cron завданні підписок: {e}")
            await asyncio.sleep(300)  # При помилці чекаємо 5 хвилин


