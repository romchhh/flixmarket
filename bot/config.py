import os
from dotenv import load_dotenv

# Корінь проєкту (FlixMarketBot), база даних спільна для bot та app
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

DB_PATH = os.getenv('DATABASE_PATH') or os.path.join(PROJECT_ROOT, 'database', 'data.db')

def normalize_bot_token(raw: str | None) -> str:
    return (raw or '').strip().strip('"').strip("'")


token = normalize_bot_token(os.getenv('BOT_TOKEN', ''))
administrators = [int(x.strip()) for x in os.getenv('ADMIN_IDS', '').split(',') if x.strip()]
# ID групи для повідомлень про оплати (бот має бути доданий у групу). Без пробілів.
_admin_chat_id_raw = (os.getenv('ADMIN_CHAT_ID') or '').strip()
admin_chat_id = int(_admin_chat_id_raw) if _admin_chat_id_raw else 0
XTOKEN = os.getenv('XTOKEN', '')
MIN_WITHDRAWAL = int(os.getenv('MIN_WITHDRAWAL', '200'))
# Публічний URL мініапки / сайту: кнопка в боті, CORS, каталог по API
SITE_URL = (
    os.getenv('SITE_URL')
    or os.getenv('WEB_APP_URL')
    or os.getenv('MINIAPP_API_URL')
    or 'https://market.easyplayy.com'
).rstrip('/')
WEB_SITE_URL = (os.getenv('WEB_SITE_URL') or SITE_URL).rstrip('/')
WEB_APP_URL = SITE_URL
MINIAPP_API_URL = SITE_URL
BOT_USERNAME = os.getenv('BOT_USERNAME', 'FlixMarketBot')

# Публічне API бота (сайт і мініапка ходять сюди з X-API-Key)
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', '8088'))
API_KEY = os.getenv('API_KEY', '')
PUBLIC_API_URL = os.getenv('PUBLIC_API_URL', '').rstrip('/')

# Абсолютний шлях до зображення каталогу (щоб sendPhoto працював незалежно від cwd)
BOT_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOG_IMAGE_PATH = os.path.join(BOT_DIR, 'Content', 'catalog.png')

# Директорія для збереження фото товарів (абсолютний шлях)
CONTENT_PRODUCTS_DIR = os.path.join(BOT_DIR, 'Content', 'products')