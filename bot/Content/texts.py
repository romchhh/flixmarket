"""Тексти та допоміжні функції для бота (емодзі, дати, повідомлення)."""
import re
from datetime import datetime
from html import escape

# Єдиний словник преміум-емодзі: ключ -> (custom_emoji_id, fallback_unicode)
PREMIUM_EMOJI: dict[str, tuple[str, str]] = {
    "welcome": ("5269475867720960040", "🤐"),
    "cabinet": ("5316727448644103237", "👤"),
    "catalog": ("5226513232549664618", "📺"),
    "about": ("5258503720928288433", "ℹ️"),
    "referral": ("5258486128742244085", "👥"),
    "support": ("5260535596941582167", "💬"),
    "faq": ("5258093637450866522", "🤖"),
    "calendar": ("5258105663359294787", "📅"),
    "tv": ("5413422358071372326", "📺"),
    "money": ("5258204546391351475", "💰"),
    "pin": ("5258461531464539536", "📌"),
    "people": ("5258513401784573443", "👥"),
    "chart": ("5231200819986047254", "📊"),
    "check": ("5260416304224936047", "✅"),
    "card": ("5258204546391351475", "💳"),
    "bell": ("5458603043203327669", "🔔"),
    "wave": ("5413694143601842851", "👋"),
    "box": ("5258134813302332906", "📦"),
    "bill": ("5258204546391351475", "💵"),
    "sparkle": ("5325547803936572038", "✨"),
}

MENU_EMOJI_IDS = {k: v[0] for k, v in PREMIUM_EMOJI.items()}


def get_premium_emoji(key: str) -> str:
    """Єдина функція для преміум-емодзі в HTML-повідомленнях. key — ключ з PREMIUM_EMOJI."""
    if key not in PREMIUM_EMOJI:
        return ""
    emoji_id, fallback = PREMIUM_EMOJI[key]
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'


def get_calendar_emoji_html() -> str:
    """Преміум емодзі календаря."""
    return get_premium_emoji("calendar")


def get_tv_emoji_html() -> str:
    """Преміум емодзі TV."""
    return get_premium_emoji("tv")


def get_person_emoji_html() -> str:
    """Преміум емодзі персони/кабінету (👤)."""
    return get_premium_emoji("cabinet")


# --- Форматування дат (єдиний формат DD.MM.YYYY скрізь) ---

def format_date(value: str | None) -> str:
    """Повертає дату у вигляді DD.MM.YYYY. value: 'YYYY-MM-DD' або 'YYYY-MM-DD HH:MM:SS'. Якщо None/порожнє — '—'."""
    if not value or not str(value).strip():
        return "—"
    s = str(value).strip()
    try:
        if " " in s:
            dt = datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")
        else:
            dt = datetime.strptime(s[:10], "%Y-%m-%d")
        return dt.strftime("%d.%m.%Y")
    except (ValueError, TypeError):
        return s[:10] if len(s) >= 10 else s


def format_datetime(value: str | None) -> str:
    """Повертає дату і час у вигляді DD.MM.YYYY о HH:MM. value: 'YYYY-MM-DD HH:MM:SS'. Якщо None/порожнє — '—'."""
    if not value or not str(value).strip():
        return "—"
    s = str(value).strip()
    try:
        if " " in s:
            dt = datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%d.%m.%Y о %H:%M")
        dt = datetime.strptime(s[:10], "%Y-%m-%d")
        return dt.strftime("%d.%m.%Y")
    except (ValueError, TypeError):
        return s[:16] if len(s) >= 16 else (s[:10] if len(s) >= 10 else s)


def format_product_name_for_display(product_name: str | None, max_text_len: int = 30) -> str:
    """Для історії нарахувань: зберігає преміум-емодзі з назви товару (tg-emoji з БД), решту екранує та обрізає."""
    if not product_name or not str(product_name).strip():
        return escape("—")
    s = str(product_name).strip()
    # Повний тег на початку: <tg-emoji emoji-id="...">...</tg-emoji>
    match = re.match(r"^(<tg-emoji\s+emoji-id=\"[^\"]+\">[^<]*</tg-emoji>)\s*(.*)$", s, re.DOTALL)
    if match:
        tag_part, rest = match.groups()
        rest = (rest.strip() or "—")[:max_text_len]
        return tag_part + " " + escape(rest)
    # Немає коректного тегу — прибираємо будь-які теги (обрізані тощо), екрануємо
    clean = (re.sub(r"<[^>]*>", "", s).strip() or "—")[:max_text_len]
    return escape(clean)


def get_greeting_message() -> str:
    return f"{get_premium_emoji('welcome')} Вітаємо вас у магазині підписок <b>Flix Market</b>! В нас ви можете придбати підписки на популярні сервіси за зниженою ціною."
    
    
def get_about_text() -> str:
    return (f"""
{get_premium_emoji("about")} <b>Про нас</b>

<i>Flix Market – це надійний онлайн-магазин підписок, який пропонує доступ до популярних сервісів за зниженими цінами. Ми працюємо з 2021 року та вже допомогли тисячам клієнтів отримати улюблені підписки швидко, вигідно та безпечно.

Наша мета – зробити якісний контент доступнішим. У нас ви можете знайти підписки на кіно та телебачення, музику, VPN-сервіси та інші корисні платформи. Ми гарантуємо оперативне підключення, підтримку на всіх етапах та зручні способи оплати.

Працюємо офіційно, маємо магазин на Prom.ua, а наша спільнота в Telegram налічує понад 5000 задоволених клієнтів. Приєднуйтесь до нас та користуйтеся улюбленими сервісами без переплат!</i>
    """
)


def get_faq_text() -> str:
    return (
    f"""
{get_premium_emoji("faq")} <b>Часті запитання та відповіді</b>

<b>• Які гарантії, що ви мене не обманете?</b>

<i>Ми працюємо з 2021 року та заслужили довіру тисяч клієнтів. Наша Telegram-група налічує понад 5000 підписників, а також ми маємо велику кількість позитивних відгуків про нашу роботу (посилання на групу з відгуками та канал – нижче). Окрім цього, у нас є офіційний магазин на Prom.ua, і ми працюємо легально, сплачуючи всі необхідні податки. Ваше задоволення та безпека – наш пріоритет!</i>

<a href="https://t.me/FLIX_vidgyki">Відгуки</a>

<a href="https://t.me/+N99gG8vIUYVkNGJi">Канал</a>

<b>• Як підключити підписку?</b>

<i>Ви обираєте підписку, оплачуєте її, і наш менеджер зв'язується з вами для підключення.(зазвичай це дуууже швидко)</i>

<b>• Які способи оплати доступні?</b>

<i>(Ви можете оплатити карткою прямо в нашому боті(Apple pay/google pay), За запитом в підтримку можна оплатити через PayPal, Revolut або Криптовалютою)</i>

<b>• Як швидко я отримаю підписку після оплати?</b>

<i>Зазвичай протягом 10-15 хв, але в деяких випадках це може зайняти трохи більше часу(якщо це не робочий час або велике навантаження)</i>

<b>• Чи можна використовувати підписку на кількох пристроях?</b>

<i>Інформація про кількість пристроїв вказана в описі кожного товару</i>

<b>• Що робити, якщо підписка перестала працювати?</b>

<i>Напишіть у підтримку, і ми оперативно вирішимо проблему. 
Контакти підтримки: telegram @kinomanage , viber 0954638612</i>

<b>• Чи є гарантія на підписку?</b>

<i>Так, гарантія діє протягом усього терміну підписки.</i>

<b>• Як зв'язатися з підтримкою?</b>

<i>Напишіть нам у telegram @kinomanage , viber 0954638612</i>
    """
    )
    

def get_help_text() -> str:
    return """
<b>🔍 Як користуватися ботом:</b>

1️⃣ Оберіть продукт у каталозі
2️⃣ Виберіть зручний тариф
3️⃣ Оплатіть підписку
4️⃣ Отримайте доступ та насолоджуйтесь!

<b>❓ Виникли питання?</b>
Зв'яжіться з нашою підтримкою: @support_username

<b>🎁 Приємного користування!</b>
"""


def get_manager_text() -> str:
    return f"""
{get_premium_emoji("support")} <b>Зв'яжіться з нашим менеджером</b>

Якщо у вас виникли питання або потрібна додаткова інформація, наш менеджер завжди готовий допомогти. 📞
"""

mailing_text = (
    "<b>СТВОРЕННЯ ПОСТУ:</b>\n\n"
    "Ця функція дозволяє створити пост і розіслати його всім користувачам бота. "
    "Ви можете додати текст, фото, відео або документ, а також URL-кнопки для посилання на зовнішні ресурси. "
    "Після створення поста, ви зможете переглянути його і підтвердити розсилку.\n\n"
    "Кроки для створення поста:\n"
    "1. Надішліть текст, фото, відео або документ, який ви хочете розіслати.\n"
    "2. Додайте опис, якщо потрібно.\n"
    "3. Додайте URL-кнопки, якщо потрібно.\n"
    "4. Перегляньте пост і підтвердьте розсилку.\n\n"
    "Після підтвердження розсилки, пост буде відправлено всім користувачам бота."
    )

def get_referral_text(
    bot_name: str,
    user_id: int,
    referral_count: int,
    balance: float = 0,
    percent: float = 20,
) -> str:
    return (
        f"{get_premium_emoji('referral')} <b>Партнерська програма</b>\n\n"
        f"<b>{get_premium_emoji('money')} Ваш баланс:</b> {balance:.2f} ₴\n"
        f"<b>{get_premium_emoji('people')} Запрошено людей:</b> {referral_count}\n"
        f"<b>{get_premium_emoji('chart')} Відсоток з покупок:</b> {percent:.0f}%\n\n"
        "<b>Як це працює:</b>\n"
        "1. Поділіться посиланням з друзями.\n"
        "2. Коли вони купують підписку — вам нараховується % від суми покупки на баланс.\n"
        "3. Нарахування з кожної покупки кожного запрошеного, постійно.\n"
        "4. Баланс можна витратити на підписки або запросити вивід.\n\n"
        f"<b>Ваше партнерське посилання:</b>\n"
        f"<code>https://t.me/{bot_name}?start={user_id}</code>"
    )

def get_contest_text(bot_name: str, user_id: int, invited_count: int) -> str:
    return (
        "<b>🏆 Конкурс на безкоштовні підписки!</b>\n\n"
        "Запрошуйте друзів та отримуйте шанси виграти круті призи!\n\n"
        f"<b>{get_premium_emoji('people')} Ви запросили:</b> {invited_count} друзів\n"
        f"<b>🎲 Ваші шанси на перемогу:</b> {invited_count}\n\n"
        "<b>Умови участі:</b>\n"
        "• Запросіть друга за цим посиланням\n"
        "• Ваш друг має лише зареєструватися\n"
        "• За кожного запрошеного друга ви отримуєте +1 шанс на виграш\n\n"
        "<b>🎁 Призи:</b>\n"
        "1️⃣ місце: Netflix + SWEET.TV на рік (1 пристрій)\n"
        "2️⃣ місце: Spotify Premium на рік\n" 
        "3️⃣ місце: SWEET.TV на рік (1 пристрій)\n"
        "4️⃣ місце: SWEET.TV на 6 місяців (1 пристрій)\n"
        "5️⃣ місце: Промокод SWEET.TV на 1 місяць\n\n"
        "<b>Як це працює:</b>\n"
        "1. Чим більше друзів ви запросите, тим більше шансів виграти\n"
        "2. Переможців буде обрано випадковим чином серед усіх учасників\n"
        "3. Кількість ваших шансів = кількості запрошених друзів\n\n"
        f"<b>Ваше реферальне посилання для участі:</b>\n<code>https://t.me/{bot_name}?start=Eve12nt145Q_{user_id}</code>\n\n"
        "🎯 <b>Не втрачайте можливість! Запрошуйте друзів та вигравайте круті призи!</b>"
    )


"""Тексти повідомлень для платежів та підписок (адмін, користувач, партнер)."""

from Content.texts import get_calendar_emoji_html, get_premium_emoji


def format_admin_user_line(user_id: int, username: str | None) -> str:
    """Рядок 'Користувач: ...' для адмін-повідомлень. Обробляє прихований профіль."""
    if username and str(username).strip():
        return f"Користувач: @{username} (ID: <code>{user_id}</code>)"
    return f"Користувач: ID <code>{user_id}</code> (прихований профіль)"


def format_admin_referral_line(
    ref_id: int | None, ref_username: str | None, credit_amount: float
) -> str:
    """Рядок про нарахування рефералу для адмін-повідомлень. Вказує, якому рефералу нараховано."""
    if not ref_id or credit_amount <= 0:
        return ""
    ref_display = (
        f"@{ref_username} (ID: <code>{ref_id}</code>)"
        if ref_username and str(ref_username).strip()
        else f"ID <code>{ref_id}</code> (прихований профіль)"
    )
    return f"\n{get_premium_emoji('sparkle')} Рефералу {ref_display} нараховано: <b>{credit_amount:.2f} ₴</b>"


def _months_word(months: int) -> str:
    if months == 1:
        return "місяць"
    if months in (2, 3, 4):
        return "місяці"
    return "місяців"


# --- Партнер ---


def get_partner_referral_purchase_text(
    buyer_display: str, product_name: str, amount: float, credit_amount: float
) -> str:
    """Текст повідомлення партнеру про покупку реферала."""
    return (
        f"{get_premium_emoji('money')} <b>Ваш реферал</b> {buyer_display} здійснив покупку!\n\n"
        f"{get_premium_emoji('box')} Товар: <b>{product_name}</b>\n"
        f"{get_premium_emoji('bill')} Сума покупки: {amount:.2f} ₴\n"
        f"{get_premium_emoji('sparkle')} Вам нараховано: <b>{credit_amount:.2f} ₴</b>"
    )


# --- Користувач ---


def get_user_subscription_success_text(
    product_name: str, months: int, amount: float, card_info: str | None = None
) -> str:
    """Текст повідомлення користувачу про успішне оформлення підписки (з автосписанням)."""
    cal = get_calendar_emoji_html()
    m = _months_word(months)
    text = (
        f"{get_premium_emoji('check')} <b>Підписка успішно оформлена!</b>\n\n"
        f"• Підписка: {product_name}\n"
        f"• Термін: {months} {m}\n"
        f"• Сума: {amount} UAH\n\n"
        f"{cal} <b>Автоматичне списання:</b> кожні {months} {m}\n"
    )
    if card_info:
        text += f"{card_info}\n\n"
    text += (
        "Зачекайте поки з вами зв'яжеться менеджер для підключення підписки\n\n"
        f"{get_premium_emoji('bell')} <b>Для отримання всіх оновлень підпишіться на наш канал:</b>\n"
    )
    return text


def get_user_subscription_token_not_found_text(product_name: str, months: int, amount: float) -> str:
    """Текст користувачу: оплата пройшла, але не вдалося зберегти дані картки для автосписання (після кількох спроб)."""
    m = _months_word(months)
    return (
        f"{get_premium_emoji('check')} <b>Оплата пройшла успішно</b>\n\n"
        f"• Підписка: {product_name}\n"
        f"• Термін: {months} {m}\n"
        f"• Сума: {amount} UAH\n\n"
        f"⚠️ <b>Не вдалося зберегти дані картки</b> для автоматичного продовження (обмеження платформи або затримка даних).\n\n"
        f"Для продовження підписки зверніться до менеджера."
    )


def get_user_one_time_success_text(product_name: str, months: int, amount: float) -> str:
    """Текст повідомлення користувачу про успішну одноразову оплату."""
    m = _months_word(months)
    return (
        f"{get_premium_emoji('check')} <b>Оплата успішна!</b>\n\n"
        f"• Підписка: {product_name}\n"
        f"• Термін: {months} {m}\n"
        f"• Сума: {amount} UAH\n\n"
        f"{get_premium_emoji('card')} <b>Одноразова оплата</b>\n\n"
        f"Зачекайте поки з вами зв'яжеться менеджер для підключення підписки\n\n"
        f"{get_premium_emoji('bell')} <b>Для отримання всіх оновлень підпишіться на наш канал:</b>\n"
    )


def get_user_contact_manager_text(payment_id: str) -> str:
    """Текст «напишіть менеджеру» після оформлення підписки."""
    return (
        f"📝 <b>Для отримання доступу до підписки напишіть менеджеру:</b>\n"
        f"• Вказавши ID платежу: <code>{payment_id}</code>\n"
        f"• Або просто написавши про куплену підписку\n\n"
        f"{get_premium_emoji('bell')} <b>Для отримання всіх оновлень підпишіться на наш канал:</b>"
    )


# --- Адмін ---


def get_admin_new_subscription_text(
    payment_id: str,
    user_id: int,
    username: str | None,
    product_name: str,
    amount: float,
    months: int,
    ref_id: int | None,
    ref_username: str | None,
    credit_amount: float,
) -> str:
    """Текст адмін-повідомлення «Нова підписка!»."""
    cal = get_calendar_emoji_html()
    m = _months_word(months)
    return (
        f"{get_premium_emoji('money')} <b>Нова підписка!</b>\n\n"
        f"ID платежу: <code>{payment_id}</code>\n"
        f"Тип: {cal} Підписка\n"
        f"{format_admin_user_line(user_id, username)}\n"
        f"Товар: {product_name}\n"
        f"Сума: {amount} UAH\n"
        f"Термін: {months} {m}"
        f"{format_admin_referral_line(ref_id, ref_username, credit_amount)}"
    )


def get_admin_new_one_time_text(
    invoice_id: str,
    user_id: int,
    username: str | None,
    product_name: str,
    amount: float,
    months: int,
    end_date_str: str,
    ref_id: int | None,
    ref_username: str | None,
    credit_amount: float,
) -> str:
    """Текст адмін-повідомлення «Нова оплата!» (одноразова)."""
    return (
        f"{get_premium_emoji('money')} <b>Нова оплата!</b>\n\n"
        f"ID платежу: <code>{invoice_id}</code>\n"
        f"Тип: {get_premium_emoji('card')} Одноразова оплата\n"
        f"{format_admin_user_line(user_id, username)}\n"
        f"Товар: {product_name}\n"
        f"Сума: {amount} UAH\n"
        f"Термін: {months} міс.\n"
        f"Активна до: {end_date_str}"
        f"{format_admin_referral_line(ref_id, ref_username, credit_amount)}"
    )


# --- Авто-платежі (cron) ---


def get_user_auto_payment_success_text(
    product_name: str, amount: float, months: int, next_date_str: str
) -> str:
    """Текст користувачу: автоматичний платіж успішно проведено."""
    m = _months_word(months)
    return (
        f"{get_premium_emoji('check')} <b>Автоматичний платіж успішно проведено</b>\n\n"
        f"Підписка: <b>{product_name}</b>\n"
        f"Сума: <b>{amount}₴</b>\n"
        f"Період: <b>{months} {m}</b>\n\n"
        f"Дата наступного списання: <b>{next_date_str}</b>"
    )


def get_admin_auto_payment_success_text(
    user_id: int,
    username: str | None,
    product_name: str,
    amount: float,
    months: int,
    next_date_str: str,
    invoice_info: str,
    card_info: str,
    token_info: str,
) -> str:
    """Текст адміну: автоматичний платіж успішно проведено."""
    m = _months_word(months)
    return (
        f"🔄 <b>Автоматичний платіж успішно проведено</b>\n\n"
        f"{format_admin_user_line(user_id, username)}\n"
        f"Підписка: <b>{product_name}</b>\n"
        f"Сума: <b>{amount}₴</b>\n"
        f"Період: <b>{months} {m}</b>\n"
        f"Наступне списання: <b>{next_date_str}</b>\n\n"
        f"{invoice_info}"
        f"{card_info}"
        f"{token_info}"
    )


def get_user_auto_payment_failed_text(
    product_name: str,
    masked_card: str,
    failures: int = None,
    max_failures: int = 3,
    retry_days: int = 1,
) -> str:
    """Текст користувачу: не вдалося провести автоматичний платіж."""
    retry_info = (
        f"Спроба {failures} з {max_failures}. Наступну спробу зробимо через {retry_days} "
        f"{'день' if retry_days == 1 else 'дні' if retry_days in (2, 3, 4) else 'днів'}.\n"
        f"Після {max_failures} невдалих спроб підписку буде автоматично скасовано.\n\n"
        if failures is not None
        else "Ми спробуємо ще раз через деякий час. Якщо проблема повториться, підписка буде скасована.\n\n"
    )
    return (
        f"❌ <b>Не вдалося провести автоматичний платіж</b>\n\n"
        f"Підписка: <b>{product_name}</b>\n"
        f"Картка: <b>{masked_card}</b>\n\n"
        f"Можливі причини:\n"
        f"• Недостатньо коштів на картці\n"
        f"• Картка заблокована\n"
        f"• Технічна помилка\n\n"
        f"{retry_info}"
        f"Переконайтеся, що на картці достатньо коштів, або скасуйте автопродовження в профілі."
    )


def get_admin_auto_payment_failed_text(
    user_id: int,
    username: str | None,
    product_name: str,
    masked_card: str,
    invoice_info: str,
    token_info: str,
    reason_info: str,
) -> str:
    """Текст адміну: невдалий автоматичний платіж."""
    return (
        f"❌ <b>Невдалий автоматичний платіж</b>\n\n"
        f"{format_admin_user_line(user_id, username)}\n"
        f"Підписка: <b>{product_name}</b>\n"
        f"Картка: <b>{masked_card}</b>\n\n"
        f"{invoice_info}"
        f"{token_info}"
        f"{reason_info}"
        f"⚠️ Потрібно перевірити стан підписки користувача"
    )


def get_user_token_invalid_text(product_name: str, masked_card: str) -> str:
    """Текст користувачу: проблема з карткою / невалідний токен."""
    return (
        f"❌ <b>Проблема з карткою для автоматичного платежу</b>\n\n"
        f"Підписка: <b>{product_name}</b>\n"
        f"Картка: <b>{masked_card}</b>\n\n"
        f"⚠️ <b>Проблема:</b> Токен картки не знайдено або застарів.\n\n"
        f"Для продовження автоматичних платежів необхідно:\n"
        f"1. Оформити нову підписку\n"
        f"2. При оплаті зберегти нову картку\n\n"
        f"Стара підписка була автоматично скасована."
    )


def get_admin_token_invalid_text(
    user_id: int,
    username: str | None,
    product_name: str,
    masked_card: str,
    error_text: str,
) -> str:
    """Текст адміну: підписка скасована через невалідний токен."""
    return (
        f"🔴 <b>Підписка скасована через невалідний токен</b>\n\n"
        f"{format_admin_user_line(user_id, username)}\n"
        f"Підписка: <b>{product_name}</b>\n"
        f"Картка: <b>{masked_card}</b>\n"
        f"Помилка: <code>{error_text}</code>\n\n"
        f"💡 Користувач має оформити нову підписку з новою карткою"
    )


def get_user_subscription_cancelled_text(product_name: str) -> str:
    """Текст користувачу: підписка скасована."""
    return (
        f"🚫 <b>Підписка скасована</b>\n\n"
        f"Підписка: <b>{product_name}</b>\n\n"
        f"Підписка була автоматично скасована через неможливість провести платіж.\n"
        f"Щоб поновити підписку, оформіть її знову в каталозі."
    )


def get_admin_subscription_cancelled_text(
    user_id: int, username: str | None, product_name: str
) -> str:
    """Текст адміну: підписка автоматично скасована."""
    return (
        f"🚫 <b>Підписка автоматично скасована</b>\n\n"
        f"{format_admin_user_line(user_id, username)}\n"
        f"Підписка: <b>{product_name}</b>\n\n"
        f"🔴 Причина: Багато невдалих спроб оплати\n"
        f"💡 Користувач може поновити підписку самостійно"
    )
