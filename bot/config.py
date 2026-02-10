import os
from dotenv import load_dotenv

# Корінь проєкту (FlixMarketBot), база даних спільна для bot та app
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

DB_PATH = os.getenv('DATABASE_PATH') or os.path.join(PROJECT_ROOT, 'database', 'data.db')

token = os.getenv('BOT_TOKEN', '')
administrators = [int(x.strip()) for x in os.getenv('ADMIN_IDS', '').split(',') if x.strip()]
# ID групи для повідомлень про оплати (бот має бути доданий у групу). Без пробілів.
_admin_chat_id_raw = (os.getenv('ADMIN_CHAT_ID') or '').strip()
admin_chat_id = int(_admin_chat_id_raw) if _admin_chat_id_raw else 0
XTOKEN = os.getenv('XTOKEN', '')
MIN_WITHDRAWAL = int(os.getenv('MIN_WITHDRAWAL', '200'))
# URL міні-додатку (каталог у браузері) для кнопки в головному меню
WEB_APP_URL = os.getenv('WEB_APP_URL', '').rstrip('/')

# Абсолютний шлях до зображення каталогу (щоб sendPhoto працював незалежно від cwd)
BOT_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOG_IMAGE_PATH = os.path.join(BOT_DIR, 'Content', 'catalog.png')

# Директорія для збереження фото товарів (абсолютний шлях)
CONTENT_PRODUCTS_DIR = os.path.join(BOT_DIR, 'Content', 'products')