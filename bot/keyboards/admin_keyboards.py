from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from database.client_db import get_product_types, get_products_by_catalog
from database.links_db import get_all_links

def get_write_to_user_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавіатура з кнопкою «Написати користувачу» (для адмін-повідомлень)."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Написати користувачу", url=f"tg://user?id={user_id}")],
    ])


def admin_keyboard():
    keyboard = [
        [KeyboardButton(text="Розсилка") ,KeyboardButton(text="Статистика")],
        [KeyboardButton(text="Управління підписками")],
        [KeyboardButton(text="Управління товарами"), KeyboardButton(text="➕ Додати товар")],
        [KeyboardButton(text="👥 Партнерська програма") , KeyboardButton(text="Посилання")],
        [KeyboardButton(text="Головне меню")],
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    return keyboard


def create_post(user_data, user_id, url_buttons=None):
    inline_kb_list = []
    if url_buttons:
        for row in url_buttons:
            inline_kb_list.append([
                InlineKeyboardButton(text=button_text, url=button_url) for button_text, button_url in row
            ])
    inline_kb_list.append([
        InlineKeyboardButton(text="Медіа", callback_data=f"media_"),
        InlineKeyboardButton(text="Додати опис", callback_data=f"add_")
    ])
    inline_kb_list.append([
        InlineKeyboardButton(text="🔔" if user_data.get(user_id, {}).get('bell', 0) == 1 else "🔕", callback_data=f"bell_"),
        InlineKeyboardButton(text="URL-кнопки", callback_data=f"url_buttons_")
    ])
    inline_kb_list.append([
        InlineKeyboardButton(text="← Відміна", callback_data=f"back_to"),
        InlineKeyboardButton(text="Далі →", callback_data=f"nextmailing_")
    ])
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def publish_post(user_data, user_id):
    inline_kb_list = [
        [InlineKeyboardButton(text="💈 Опублікувати", callback_data=f"publish_")],
        [InlineKeyboardButton(text="← Назад", callback_data=f"back_to")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def confirm_mailing():
    keyboard = [
        [InlineKeyboardButton(text="✓ Так", callback_data=f"confirm_publish_")],
        [InlineKeyboardButton(text="❌ Ні", callback_data="cancel_publish")]  
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def back_mailing_keyboard():
    inline_kb_list = [
        [InlineKeyboardButton(text="Назад", callback_data="back_to_my_post")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def post_keyboard(user_data, user_id, url_buttons=None):
    inline_kb_list = []
    if url_buttons:
        for row in url_buttons:
            inline_kb_list.append([InlineKeyboardButton(text=button_text, url=button_url) for button_text, button_url in row])
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def get_broadcast_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="Зробити розсилку", callback_data="create_post")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)



def get_admin_catalog_keyboard():
    keyboard = []
    products = get_product_types()
    row = []
    
    for catalog_id, product_type, count in products:
        row.append(
            InlineKeyboardButton(
                text=f"{product_type} [{count}]",
                callback_data=f"admincategory_{catalog_id}"
            )
        )
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_products_keyboard(catalog_id: int):
    keyboard = []
    products = get_products_by_catalog(catalog_id)
    row = []
    
    for product_id, product_name, price in products:
        row.append(
            InlineKeyboardButton(
                text=f"{product_name}",
                callback_data=f"adminproduct_{product_id}"
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
            callback_data="back_to_admin_products"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def edit_product_keyboard(product_id: int):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✏️ Редагувати",
                callback_data=f"edit_product_{product_id}"
            ),
            InlineKeyboardButton(
                text="🗑 Видалити",
                callback_data=f"delete_product_{product_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="← Назад",
                callback_data=f"back_to_admin_products"
            )
        ]
    ])
    return keyboard


def edit_options_keyboard(product_id: int):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✏️ Редагувати назву",
                callback_data=f"edit_name_{product_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="✏️ Редагувати опис",
                callback_data=f"edit_description_{product_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="✏️ Редагувати тарифи",
                callback_data=f"edit_price_{product_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="✏️ Редагувати тип оплати",
                callback_data=f"edit_payment_type_{product_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="← Назад",
                callback_data=f"back_to_product_{product_id}"
            )
        ]
    ])
    return keyboard


def cancel_button():
    keyboard = [
        [KeyboardButton(text="❌ Скасувати")] 
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)

def payment_type_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📅 Модель підписки",
                callback_data="payment_type_subscription"
            )
        ],
        [
            InlineKeyboardButton(
                text="💳 Одноразова оплата",
                callback_data="payment_type_one_time"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Скасувати",
                callback_data="cancel_payment_type"
            )
        ]
    ])
    return keyboard


def get_admin_subscriptions_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📊 Детальна статистика",
                callback_data="detailed_stats"
            )
        ],
        [
            InlineKeyboardButton(
                text="📋 Переглянути всі підписки",
                callback_data="view_all_subscriptions"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔍 Пошук підписки",
                callback_data="search_subscription"
            )
        ],
        [
            InlineKeyboardButton(
                text="▶️ Запустити повторювані платежі",
                callback_data="confirm_run_payments"
            )
        ]
    ])


def get_admin_subscription_actions_keyboard(subscription_id: int, subscription_type: str) -> InlineKeyboardMarkup:
    """Клавіатура дій для конкретної підписки"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Активувати",
                callback_data=f"admin_activate_{subscription_type}_{subscription_id}"
            ),
            InlineKeyboardButton(
                text="❌ Деактивувати",
                callback_data=f"admin_deactivate_{subscription_type}_{subscription_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🗑️ Видалити підписку",
                callback_data=f"admin_delete_{subscription_type}_{subscription_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="👤 Написати користувачу",
                callback_data=f"admin_contact_{subscription_type}_{subscription_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="← Назад до списку",
                callback_data="view_all_subscriptions"
            )
        ]
    ])


def get_admin_subscription_list_keyboard(subscriptions: list) -> InlineKeyboardMarkup:
    """Клавіатура зі списком підписок"""
    keyboard = []
    
    for i, sub in enumerate(subscriptions[:20]):  # Обмежуємо до 20 підписок на сторінку
        status_emoji = "✅" if sub['status'] == 'active' else "❌"
        type_emoji = "🔄" if sub['type'] == 'recurring' else "💳"
        
        keyboard.append([
            InlineKeyboardButton(
                text=f"{status_emoji} {type_emoji} {sub['product_name']} - @{sub['username']}",
                callback_data=f"admin_view_{sub['type']}_{sub['id']}"
            )
        ])
    
    # Кнопки навігації
    nav_buttons = []
    if len(subscriptions) > 20:
        nav_buttons.extend([
            InlineKeyboardButton(text="◀️ Попередня", callback_data="prev_page"),
            InlineKeyboardButton(text="▶️ Наступна", callback_data="next_page")
        ])
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([
        InlineKeyboardButton(
            text="🔄 Оновити",
            callback_data="view_all_subscriptions"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_subscription_list_keyboard_with_pagination(subscriptions: list, current_page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Клавіатура зі списком підписок з пагінацією"""
    keyboard = []
    
    for sub in subscriptions:
        status_emoji = "✅" if sub['status'] == 'active' else "❌"
        type_emoji = "🔄" if sub['type'] == 'recurring' else "💳"
        
        keyboard.append([
            InlineKeyboardButton(
                text=f"{status_emoji} {type_emoji} {sub['product_name']} - @{sub['username']}",
                callback_data=f"admin_view_{sub['type']}_{sub['id']}"
            )
        ])
    
    # Кнопки навігації
    nav_buttons = []
    if current_page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="◀️ Попередня", callback_data="prev_page")
        )
    if current_page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton(text="▶️ Наступна", callback_data="next_page")
        )
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([
        InlineKeyboardButton(
            text="🔄 Оновити",
            callback_data="view_all_subscriptions"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirm_run_payments_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура підтвердження запуску повторюваних платежів"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Так, запустити",
                callback_data="run_payments_now"
            ),
            InlineKeyboardButton(
                text="❌ Ні, відмінити",
                callback_data="cancel_run_payments"
            )
        ]
    ])




# LINKS KEYBOARD
def get_links_keyboard() -> InlineKeyboardMarkup:
    keyboard = []
    links = get_all_links()
    
    for link in links:
        visits = link[3] if len(link) > 3 else 0
        registrations = link[4] if len(link) > 4 else 0
        purchases = link[5] if len(link) > 5 else 0
        keyboard.append([
            InlineKeyboardButton(
                text=f"{link[1]} ({visits} пер. / {registrations} реєстр. / {purchases} покуп.)",
                callback_data=f"link_stats_{link[0]}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            text="➕ Додати посилання",
            callback_data="add_link"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)



def cancel_button() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="Скасувати")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_link_stats_keyboard(link_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="✏️ Редагувати", callback_data=f"edit_link_{link_id}"),
            InlineKeyboardButton(text="🗑 Видалити", callback_data=f"delete_link_{link_id}")
        ],
        [InlineKeyboardButton(text="🔄 Оновити", callback_data=f"link_stats_{link_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_links")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_delete_link_confirm_keyboard(link_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Так", callback_data=f"confirm_delete_{link_id}"),
            InlineKeyboardButton(text="❌ Ні", callback_data="back_to_links")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)