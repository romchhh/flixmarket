from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from config import administrators, WEB_APP_URL
from database.client_db import get_product_types, get_products_by_catalog
from ulits.admin_functions import strip_html_for_button

def get_start_keyboard(user_id: int):
    keyboard = [
        [KeyboardButton(text="Мій кабінет") ,KeyboardButton(text="Каталог")],
        [KeyboardButton(text="Про нас"), KeyboardButton(text="Партнерська програма")],
        [KeyboardButton(text="Підтримка"), KeyboardButton(text="Часті питання")],
    ]
    if WEB_APP_URL:
        keyboard.append([KeyboardButton(text="Відкрити каталог у браузері", web_app=WebAppInfo(url=WEB_APP_URL))])
    if user_id in administrators:
        keyboard.append([KeyboardButton(text="Адмін панель 💻")])
    
    keyboard = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    return keyboard


def get_socials_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="Правила та умови платформи Flix Market", url=f"https://telegra.ph/Pravila-ta-umovi-platformi-Flix-Market-05-03-2")],
        [InlineKeyboardButton(text="Telegram", url=f"https://t.me/+4KiUb2eGd-oyMDNi")],
        [InlineKeyboardButton(text="Відгуки", url=f"https://t.me/FLIX_vidgyki")],  
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_manager_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="Менеджер", url=f"https://t.me/kinomanage")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_catalog_keyboard():
    keyboard = []
    products = get_product_types()
    row = []
    
    for catalog_id, product_type, count in products:
        row.append(
            InlineKeyboardButton(
                text=f"{product_type} [{count}]",
                callback_data=f"category_{catalog_id}"
            )
        )
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_products_keyboard(catalog_id: int):
    from ulits.admin_functions import format_product_button_label

    keyboard = []
    products = get_products_by_catalog(catalog_id)
    row = []

    for product_id, product_name, price in products:
        label = format_product_button_label(product_name, price)
        row.append(
            InlineKeyboardButton(
                text=label,
                callback_data=f"product_{product_id}"
            )
        )
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton(
            text="← Назад",
            callback_data="back_to_categories"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_product_info_keyboard(product_id: int, product_name: str, description: str, price_str: str | int | float):
    keyboard = []
    if price_str is None:
        price_str = "1-0"
    price_str = str(price_str).strip()
    if not price_str:
        price_str = "1-0"
    tariffs = [t.strip() for t in price_str.split(',')] if ',' in price_str else [price_str]
    
    for tariff in tariffs:
        if '-' not in tariff:
            tariff = f"1-{tariff}"
        months, price = tariff.split('-', 1)
        months = months.strip()
        price = price.strip()
        
        month_word = "місяць" if months == "1" else "місяці" if months in ["2", "3", "4"] else "місяців"
        
        keyboard.append([
            InlineKeyboardButton(
                text=f"{months} {month_word} - {price}₴",
                callback_data=f"buy_{product_id}_{months}_{price}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            text="← Назад",
            callback_data="back_to_categories"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_payment_keyboard(payment_link: str, product_id: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💳 Оплатити",
                url=payment_link
            )
        ],
        [
            InlineKeyboardButton(
                text="← Назад",
                callback_data=f"product_{product_id}"
            )
        ]
    ])
    return keyboard


def get_one_time_confirm_keyboard(product_id: int, months: int, price: float) -> InlineKeyboardMarkup:
    """Підтвердження одноразової оплати + опційний промокод."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💳 Оплатити карткою",
                callback_data=f"one_time_card_{product_id}_{months}_{price}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎟 Ввести промокод",
                callback_data=f"promo_ask_{product_id}_{months}_{price}"
            )
        ],
        [
            InlineKeyboardButton(text="← Назад", callback_data=f"product_{product_id}")
        ],
    ])


def get_payment_choice_keyboard(product_id: int, months: int, price: float) -> InlineKeyboardMarkup:
    """Клавіатура вибору: оплата карткою або з партнерського балансу."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💳 Оплатити карткою",
                callback_data=f"one_time_card_{product_id}_{months}_{price}"
            )
        ],
        [
            InlineKeyboardButton(
                text="💰 Сплатити з балансу",
                callback_data=f"pay_balance_{product_id}_{months}_{price}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎟 Промокод",
                callback_data=f"promo_ask_{product_id}_{months}_{price}"
            )
        ],
        [
            InlineKeyboardButton(text="← Назад", callback_data=f"product_{product_id}")
        ],
    ])


def get_channel_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Підписатися на канал", url="https://t.me/+N99gG8vIUYVkNGJi")],
    ])
    return keyboard



def get_services_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Переглянути доступні сервіси", callback_data="show_services")]
    ])
    return keyboard


def get_profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📋 Управління підписками",
                callback_data="my_subscriptions"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 Доступні сервіси",
                callback_data="show_services"
            )
        ]
    ])


def get_subscription_terms_keyboard(product_id: int, months: int, price: float) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Погоджуюся з умовами",
                callback_data=f"agree_subscription_{product_id}_{months}_{price}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎟 Промокод",
                callback_data=f"promo_ask_{product_id}_{months}_{price}"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Відмінити",
                callback_data=f"product_{product_id}"
            )
        ]
    ])
    
def get_back_to_profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="← Назад", 
                callback_data="back_to_profile"
            )
        ]
    ])

def get_referral_keyboard(bot_name: str, user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📤 Поділитися посиланням",
                switch_inline_query=f"🎬 Підписки на кіно, музику та сервіси зі знижкою — переходь за моїм посиланням:\n\nhttps://t.me/{bot_name}?start={user_id}"
            )
        ],
        [
            InlineKeyboardButton(text="📋 Історія нарахувань", callback_data="partner_history"),
            InlineKeyboardButton(text="💸 Запитати вивід", callback_data="partner_withdraw"),
        ],
    ])


def get_contest_keyboard(bot_name: str, user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔥 Запросити друга",
                switch_inline_query=f"Приєднуйся за моїм посиланням та отримай шанс виграти безкоштовну підписку на будь який сервіс 🔥: \n\nhttps://t.me/{bot_name}?start=Eve12nt145Q_{user_id}"
            )
        ]
    ])


