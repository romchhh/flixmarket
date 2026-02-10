import os
from config import BOT_DIR


def resolve_media_path(path: str | None) -> str | None:
    """Перетворює відносний шлях до медіа (наприклад з БД) на абсолютний. Для sendPhoto/editMessageMedia."""
    if not path or not str(path).strip():
        return None
    path = str(path).strip()
    if os.path.isabs(path):
        return path
    return os.path.join(BOT_DIR, path)
