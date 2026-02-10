from database.client_db import get_user_info, get_user_subscriptions, get_user_recurring_subscriptions
from datetime import datetime
from Content.texts import get_calendar_emoji_html, get_person_emoji_html, get_premium_emoji


async def get_profile_text(user_id: int, username: str) -> str:
    user_info = get_user_info(user_id)
    
    if not user_info:
        return "❌ Помилка отримання даних профілю"
    
    username = username or "Не вказано"
    joined_date = user_info['join_date']
    
    joined_datetime = datetime.strptime(joined_date, '%Y-%m-%d %H:%M:%S')
    days_using = (datetime.now() - joined_datetime).days
    
    subscriptions = get_user_subscriptions(user_id)
    
    recurring_subscriptions = get_user_recurring_subscriptions(user_id)
    
    profile_text = (
        f"{get_person_emoji_html()} <b>Мій кабінет</b>\n\n"
        f"• Логін: @{username}\n"
        f"• ID: <code>{user_id}</code>\n"
        f"• З нами з: {joined_datetime.strftime('%d.%m.%Y')}\n"
        f"• Днів користування: {days_using}\n\n"
    )
    
    if subscriptions or recurring_subscriptions:
        profile_text += "📋 <b>Ваші підписки:</b>\n\n"
        
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
        profile_text += "📋 <b>Підписки:</b> Немає активних підписок"
    
    return profile_text
    

def get_days_word(days: int) -> str:
    if days == 1:
        return "день"
    elif days in [2, 3, 4]:
        return "дні"
    else:
        return "днів"


def get_status_text(status: str) -> str:
    """Повертає статус українською мовою"""
    statuses = {
        'active': 'Активна',
        'inactive': 'Неактивна',
        'pending': 'Очікує оплати',
        'expired': 'Закінчилась'
    }
    return statuses.get(status, status)