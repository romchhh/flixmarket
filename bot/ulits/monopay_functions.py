from datetime import datetime, timedelta
import asyncio
import base64
import json
import requests
from typing import Tuple
from database.client_db import (
    update_payment_status,
    get_pending_payments,
    add_subscription,
    get_product_by_id,
    get_product_type,
    cursor,
    conn,
    get_username_by_id,
    get_ref_id_by_user,
    add_partner_credit,
    get_partner_referral_percent,
)
from main import bot
from config import admin_chat_id, XTOKEN
from keyboards.client_keyboards import get_channel_keyboard, get_manager_keyboard
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from Content.texts import get_premium_emoji
from Content.texts import (
    get_partner_referral_purchase_text,
    get_user_subscription_success_text,
    get_user_subscription_token_not_found_text,
    get_user_one_time_success_text,
    get_user_contact_manager_text,
    get_admin_new_subscription_text,
    get_admin_new_one_time_text,
)
import logging
import sqlite3
import uuid


class PaymentManager:
    def __init__(self):
        self.token = XTOKEN  # Заміни на реальний токен
        self.host = "https://api.monobank.ua/"

    def create_payment(self, user_id: int, product_name: str, months: int, price: float) -> tuple[str, str, str]:
        local_payment_id = f"order_{user_id}_{int(datetime.now().timestamp())}"
        
        # Додаємо merchantPaymInfo з інформацією про товар
        payload = {
            "amount": int(price * 100),  # Сума в копійках
            "ccy": 980,                  # Код валюти UAH
            "description": f"Оплата {product_name} на {months} міс.",
            "orderReference": local_payment_id,
            "destination": "Оплата через Telegram-бот",
            "redirectUrl": "https://t.me/FlixMarketBot",
            "merchantPaymInfo": {
                "basketOrder": [
                    {
                        "name": product_name,           # Назва товару
                        "qty": 1,                       # Кількість одиниць
                        "sum": int(price * 100),        # Сума в копійках
                        "code": f"prod_{product_name}", # Унікальний код товару (можна адаптувати)
                        "unit": "шт."                   # Одиниця виміру
                    }
                ]
            }
        }
        
        headers = {"X-Token": self.token, "Content-Type": "application/json"}
        response = requests.post(f"{self.host}api/merchant/invoice/create", json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            invoice_id = result["invoiceId"]  # Отримуємо invoiceId від monobank
            payment_url = result["pageUrl"]
            return local_payment_id, invoice_id, payment_url
        else:
            raise Exception(f"Помилка створення платежу: {response.text}")

    def create_payment_with_tokenization(self, user_id: int, product_name: str, months: int, price: float) -> tuple[str, str, str, str]:
        """Створює платіж з токенізацією картки для підписки"""
        local_payment_id = f"subscription_{user_id}_{int(datetime.now().timestamp())}"
        wallet_id = f"wallet_{user_id}_{uuid.uuid4().hex[:8]}"
        
        payload = {
            "amount": int(price * 100),
            "ccy": 980,
            "merchantPaymInfo": {
                "reference": local_payment_id,
                "destination": f"Підписка на {product_name}",
                "comment": f"Підписка на {product_name} на {months} міс.",
                "customerEmails": [],
                "discounts": [],
                "basketOrder": [
                    {
                        "name": product_name,
                        "qty": 1,
                        "sum": int(price * 100),
                        "total": int(price * 100),
                        "icon": None,
                        "unit": "шт.",
                        "code": f"sub_{product_name}",
                        "barcode": None,
                        "header": None,
                        "footer": None,
                        "tax": [],
                        "uktzed": None,
                        "discounts": []
                    }
                ]
            },
            "redirectUrl": "https://t.me/FlixMarketBot",
            "webHookUrl": f"https://your-webhook-url.com/mono/webhook/{local_payment_id}",
            "validity": 3600,  # 1 година
            "paymentType": "debit",
            "saveCardData": {
                "saveCard": True,  # МАЄ БУТИ True для токенізації згідно документації!
                "walletId": wallet_id
            }
        }
        
        headers = {"X-Token": self.token, "Content-Type": "application/json"}
        logging.info(f"Створення платежу з токенізацією. Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        response = requests.post(f"{self.host}api/merchant/invoice/create", json=payload, headers=headers)
        
        logging.info(f"Статус відповіді створення платежу: {response.status_code}")
        logging.info(f"Заголовки відповіді: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            logging.info(f"Повна відповідь створення платежу з токенізацією: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            invoice_id = result["invoiceId"]
            payment_url = result["pageUrl"]
            return local_payment_id, invoice_id, payment_url, wallet_id
        else:
            logging.error(f"Помилка створення платежу: {response.status_code} - {response.text}")
            raise Exception(f"Помилка створення платежу: {response.text}")

    def create_token_payment(self, wallet_id: str, card_token: str, product_name: str, months: int, price: float) -> tuple[str, str]:
        """Створює платіж по збереженому токену"""
        local_payment_id = f"token_payment_{int(datetime.now().timestamp())}"
        
        payload = {
            "cardToken": card_token,
            "amount": int(price * 100),
            "ccy": 980,
            "redirectUrl": "https://t.me/FlixMarketBot",
            "webHookUrl": f"https://your-webhook-url.com/mono/webhook/{local_payment_id}",
            "initiationKind": "merchant",  # merchant - автоматичне списання
            "merchantPaymInfo": {
                "reference": local_payment_id,
                "destination": f"Автоматичне списання підписки {product_name}",
                "comment": f"Підписка на {product_name} на {months} міс.",
                "customerEmails": [],
                "discounts": [],
                "basketOrder": [
                    {
                        "name": product_name,
                        "qty": 1,
                        "sum": int(price * 100),
                        "total": int(price * 100),
                        "icon": None,
                        "unit": "шт.",
                        "code": f"auto_sub_{product_name}",
                        "barcode": None,
                        "header": None,
                        "footer": None,
                        "tax": [],
                        "uktzed": None,
                        "discounts": []
                    }
                ]
            },
            "paymentType": "debit"
        }
        
        headers = {"X-Token": self.token, "Content-Type": "application/json"}
        logging.info(f"Створення токен-платежу. Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        response = requests.post(f"{self.host}api/merchant/wallet/payment", json=payload, headers=headers)
        
        logging.info(f"Статус відповіді токен-платежу: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logging.info(f"Повна відповідь токен-платежу: {json.dumps(result, indent=2, ensure_ascii=False)}")
            invoice_id = result["invoiceId"]
            return local_payment_id, invoice_id
        else:
            logging.error(f"Помилка оплати по токену: {response.status_code} - {response.text}")
            raise Exception(f"Помилка оплати по токену: {response.text}")

    def get_payment_status(self, invoice_id: str) -> dict:
        """Отримує статус платежу по invoice_id"""
        headers = {"X-Token": self.token}
        response = requests.get(f"{self.host}api/merchant/invoice/status?invoiceId={invoice_id}", headers=headers)
        
        logging.info(f"Запит статусу платежу {invoice_id}: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logging.info(f"Повна відповідь статусу платежу {invoice_id}: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
        else:
            logging.error(f"Помилка отримання статусу платежу {invoice_id}: {response.status_code} - {response.text}")
            raise Exception(f"Помилка отримання статусу: {response.text}")

    def cancel_payment(self, invoice_id: str) -> bool:
        """Скасовує платіж"""
        payload = {"invoiceId": invoice_id}
        headers = {"X-Token": self.token, "Content-Type": "application/json"}
        response = requests.post(f"{self.host}api/merchant/invoice/cancel", json=payload, headers=headers)
        
        return response.status_code == 200
        
    def get_wallet_info(self, wallet_id: str) -> dict:
        """Отримує інформацію про wallet, включаючи токени карток"""
        headers = {"X-Token": self.token}
        response = requests.get(f"{self.host}api/merchant/wallet", headers=headers)
        
        logging.info(f"Запит інформації про wallet: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logging.info(f"Повна відповідь про wallet: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
        else:
            logging.error(f"Помилка отримання wallet: {response.status_code} - {response.text}")
            return {}
    
    def get_wallet_by_id(self, wallet_id: str) -> dict:
        """Отримує інформацію про конкретний wallet по ID"""
        headers = {"X-Token": self.token}
        url = f"{self.host}api/merchant/wallet/{wallet_id}"
        response = requests.get(url, headers=headers)
        
        logging.info(f"Запит wallet по ID {wallet_id}: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logging.info(f"Повна відповідь про wallet {wallet_id}: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
        else:
            logging.error(f"Помилка отримання wallet {wallet_id}: {response.status_code} - {response.text}")
            return {}

    def get_wallet_cards(self, wallet_id: str) -> list:
        """Отримує список збережених карток для конкретного wallet"""
        headers = {"X-Token": self.token}
        url = f"{self.host}api/merchant/wallet/{wallet_id}/cards"
        response = requests.get(url, headers=headers)
        
        logging.info(f"Запит карток для wallet {wallet_id}: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logging.info(f"Повна відповідь про картки для wallet {wallet_id}: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
        else:
            logging.error(f"Помилка отримання карток для wallet {wallet_id}: {response.status_code} - {response.text}")
            return []
        
        
        
async def check_pending_payments():
    payment_manager = PaymentManager()
    
    pending_payments = get_pending_payments()
    
    logging.info(f"Знайдено {len(pending_payments)} платежів у базі для перевірки")
    if not pending_payments:
        logging.warning("Список pending_payments порожній. Перевірте базу даних")

    for payment in pending_payments:
        invoice_id, user_id, product_id, months, amount, payment_type = payment
        logging.info(f"Перевірка платежу з БД: {invoice_id} (користувач: {user_id}, тип: {payment_type})")
        
        headers = {"X-Token": payment_manager.token}
        url = f"{payment_manager.host}api/merchant/invoice/status?invoiceId={invoice_id}"
        try:
            response = requests.get(
                f"{payment_manager.host}api/merchant/invoice/status?invoiceId={invoice_id}",
                headers=headers
            )

            print(response.json())
            
            if response.status_code == 200:
                payment_data = response.json()
                status = payment_data.get("status", "невідомо")
                logging.info(f"Статус платежу {invoice_id} з API: {status}")
                logging.info(f"Дані платежу від Monobank: {payment_data}")
                
                if status == "success":
                    logging.info(f"Платіж {invoice_id} успішний. Оновлення статусу")
                    
                    username = get_username_by_id(user_id)
                    update_payment_status(invoice_id, "success")

                    product = get_product_by_id(product_id)
                    product_name_for_partner = product[0] if product else ""
                    ref_id = get_ref_id_by_user(user_id)
                    if ref_id:
                        add_partner_credit(
                            partner_id=ref_id,
                            buyer_id=user_id,
                            purchase_amount=amount,
                            product_name=product_name_for_partner,
                            payment_type=payment_type,
                        )
                        percent = get_partner_referral_percent()
                        credit_amount = round(amount * (percent / 100), 1)
                        if credit_amount > 0:
                            buyer_username = get_username_by_id(user_id)
                            buyer_line = f"@{buyer_username}" if (buyer_username and str(buyer_username).strip()) else f"користувач (ID: {user_id}, прихований профіль)"
                            try:
                                await bot.send_message(
                                    ref_id,
                                    get_partner_referral_purchase_text(buyer_line, product_name_for_partner, amount, credit_amount),
                                    parse_mode="HTML",
                                )
                            except Exception:
                                pass

                    if payment_type == "subscription":
                        logging.info(f"Обробка підписки для платежу {invoice_id}")
                        
                        cursor.execute("SELECT payment_id FROM payments WHERE invoice_id = ?", (invoice_id,))
                        payment_result = cursor.fetchone()
                        if not payment_result:
                            logging.error(f"Не знайдено payment_id для invoice_id: {invoice_id}")
                            continue
                        
                        payment_id = payment_result[0]
                        
                        product = get_product_by_id(product_id)
                        if not product:
                            logging.error(f"Продукт {product_id} не знайдено")
                            continue
                        
                        product_name, description, _, photo_path = product
                        
                        cursor.execute("SELECT wallet_id FROM payments_temp_data WHERE local_payment_id = ?", (payment_id,))
                        temp_data = cursor.fetchone()
                        
                        wallet_id = temp_data[0] if temp_data else None
                        if not wallet_id and "walletData" in payment_data and isinstance(payment_data.get("walletData"), dict):
                            wallet_id = payment_data["walletData"].get("walletId")
                        if not wallet_id:
                            wallet_id = f"wallet_{user_id}_{uuid.uuid4().hex[:8]}"
                            if not temp_data:
                                logging.warning(f"Тимчасових даних немає для платежу {payment_id}, використовуємо wallet_id: {wallet_id}")
                        
                        from database.client_db import save_user_token, create_recurring_subscription
                        
                        MAX_TOKEN_ATTEMPTS = 3
                        DELAY_SEC = 15
                        current_payment_data = payment_data
                        card_token = None
                        masked_card = "**** **** **** 1234"
                        card_type = "unknown"
                        
                        for attempt in range(1, MAX_TOKEN_ATTEMPTS + 1):
                            if attempt > 1:
                                logging.info(f"Повторна спроба {attempt}/{MAX_TOKEN_ATTEMPTS} через {DELAY_SEC} с для {invoice_id}")
                                await asyncio.sleep(DELAY_SEC)
                                try:
                                    resp = requests.get(url, headers=headers)
                                    if resp.status_code == 200:
                                        current_payment_data = resp.json()
                                        logging.info(f"Повторний запит статусу: {json.dumps(current_payment_data, indent=2, ensure_ascii=False)[:500]}...")
                                    else:
                                        logging.warning(f"Повторний запит повернув {resp.status_code}")
                                except Exception as e:
                                    logging.warning(f"Повторний запит статусу платежу {invoice_id}: {e}")
                                    continue
                            
                            if "walletData" in current_payment_data and current_payment_data["walletData"]:
                                wd = current_payment_data["walletData"]
                                card_token = wd.get("cardToken") if isinstance(wd, dict) else None
                                if card_token:
                                    logging.info(f"✅ Токен картки знайдено в walletData на спробі {attempt}")
                                    break
                                logging.warning(f"walletData є, але cardToken відсутній (спроба {attempt})")
                            else:
                                logging.warning(f"walletData не знайдено у відповіді (спроба {attempt})")
                            
                            if not card_token and wallet_id:
                                try:
                                    wallet_cards = payment_manager.get_wallet_cards(wallet_id)
                                    if wallet_cards and len(wallet_cards) > 0:
                                        card_token = wallet_cards[-1].get("cardToken") or wallet_cards[-1].get("token")
                                        if card_token:
                                            logging.info(f"✅ Токен картки отримано з wallet API на спробі {attempt}")
                                            break
                                except Exception as e:
                                    logging.warning(f"Wallet API на спробі {attempt}: {e}")
                            
                            if "paymentInfo" in current_payment_data:
                                pi = current_payment_data["paymentInfo"]
                                if isinstance(pi, dict):
                                    masked_card = pi.get("maskedPan", masked_card)
                                    card_type = pi.get("paymentSystem", card_type)
                            
                            if not card_token:
                                logging.warning(f"Токен не знайдено, спроба {attempt}/{MAX_TOKEN_ATTEMPTS}")
                        
                        if card_token:
                            logging.info(f"💳 Дані картки: token=..., masked={masked_card}, type={card_type}")
                            save_user_token(user_id, wallet_id, card_token, masked_card, card_type)
                            create_recurring_subscription(
                                user_id=user_id,
                                product_id=product_id,
                                product_name=product_name,
                                months=months,
                                price=amount,
                                wallet_id=wallet_id
                            )
                            card_info = f"{get_premium_emoji('card')} <b>Картка:</b> {masked_card}"
                            if card_type != "unknown":
                                card_info += f" ({card_type.upper()})"
                            await bot.send_message(
                                user_id,
                                get_user_subscription_success_text(product_name, months, amount, card_info=card_info),
                                parse_mode="HTML",
                                reply_markup=get_channel_keyboard()
                            )
                            cursor.execute("DELETE FROM payments_temp_data WHERE local_payment_id = ?", (payment_id,))
                            conn.commit()
                            sub_username = get_username_by_id(user_id)
                            sub_ref_username = get_username_by_id(ref_id) if ref_id else None
                            sub_credit = round(amount * (get_partner_referral_percent() / 100), 1) if ref_id else 0
                            try:
                                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                                    [InlineKeyboardButton(text="👤 Написати користувачу", url=f"tg://user?id={user_id}")],
                                ])
                                await bot.send_message(
                                    admin_chat_id,
                                    get_admin_new_subscription_text(payment_id, user_id, sub_username, product_name, amount, months, ref_id, sub_ref_username, sub_credit),
                                    parse_mode="HTML",
                                    reply_markup=keyboard
                                )
                            except Exception as e:
                                logging.error(f"Помилка при відправці повідомлення адміну про підписку: {e}")
                                await bot.send_message(
                                    admin_chat_id,
                                    get_admin_new_subscription_text(payment_id, user_id, sub_username, product_name, amount, months, ref_id, sub_ref_username, sub_credit),
                                    parse_mode="HTML"
                                )
                        else:
                            logging.error("❌ Токен картки не знайдено після всіх спроб. Повідомляємо користувача.")
                            try:
                                await bot.send_message(
                                    user_id,
                                    get_user_subscription_token_not_found_text(product_name, months, amount),
                                    parse_mode="HTML"
                                )
                            except Exception as e:
                                logging.error(f"Не вдалося відправити повідомлення користувачу: {e}")
                    
                    else:
                        # Звичайна одноразова оплата
                        logging.info(f"Обробка одноразової оплати для платежу {invoice_id}")
                        
                        product = get_product_by_id(product_id)
                        if not product:
                            logging.error(f"Продукт {product_id} не знайдено")
                            continue
                            
                        product_name, description, _, photo_path = product
                        start_date = datetime.now()
                        end_date = start_date + timedelta(days=30 * months)
                        product_type = get_product_type(product_id)
                        
                        add_subscription(
                            user_id=user_id,
                            product_type=product_type,
                            product_id=product_id,
                            product_name=product_name,
                            price=amount,
                            start_date=start_date.strftime("%Y-%m-%d"),
                            end_date=end_date.strftime("%Y-%m-%d"),
                            status="active"
                        )
                        
                        await bot.send_message(
                            user_id,
                            get_user_one_time_success_text(product_name, months, amount),
                            parse_mode="HTML",
                            reply_markup=get_channel_keyboard()
                        )
                        ref_username_one_time = get_username_by_id(ref_id) if ref_id else None
                        credit_one_time = round(amount * (get_partner_referral_percent() / 100), 1) if ref_id else 0
                        try:
                            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                                [InlineKeyboardButton(text="👤 Написати користувачу", url=f"tg://user?id={user_id}")],
                            ])
                            await bot.send_message(
                                admin_chat_id,
                                get_admin_new_one_time_text(
                                    invoice_id, user_id, username, product_name, amount, months,
                                    end_date.strftime('%d.%m.%Y'), ref_id, ref_username_one_time, credit_one_time
                                ),
                                parse_mode="HTML",
                                reply_markup=keyboard
                            )
                        except Exception as e:
                            logging.error(f"Помилка при відправці повідомлення адміну про оплату: {e}")
                            await bot.send_message(
                                admin_chat_id,
                                get_admin_new_one_time_text(
                                    invoice_id, user_id, username, product_name, amount, months,
                                    end_date.strftime('%d.%m.%Y'), ref_id, ref_username_one_time, credit_one_time
                                ),
                                parse_mode="HTML"
                            )
                            await bot.send_message(
                                user_id,
                                get_user_contact_manager_text(invoice_id),
                                parse_mode="HTML",
                                reply_markup=get_manager_keyboard()
                            )

                    
                    logging.info(f"Платіж {invoice_id} оброблено успішно")
                else:
                    logging.info(f"Платіж {invoice_id} ще не успішний: {status}")
            else:
                logging.error(f"Помилка API для {invoice_id}: {response.status_code} - {response.text}")
        except Exception as e:
            logging.error(f"Помилка при перевірці платежу {invoice_id}: {str(e)}", exc_info=True)
    
    logging.info("Завершення перевірки платежів")


