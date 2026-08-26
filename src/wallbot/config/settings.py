import os
from src.wallbot.utils.version import read_version

PROFILE = os.getenv("PROFILE")

# Versión de la app centralizada
APP_VERSION = read_version()

# Telegram Bot Token
TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not TOKEN:
    raise ValueError("ERROR: La variable de entorno BOT_TOKEN no está configurada o está vacía.")

# Usuarios autorizados (mantiene el orden para identificar al admin como [0])
raw_users = os.getenv("AUTHORIZED_USERS", "").strip()
if raw_users:
    AUTHORIZED_USERS = tuple(
        u.strip().lstrip("@").lower()
        for u in raw_users.split(",")
        if u.strip()
    )
else:
    AUTHORIZED_USERS = ()

# URLs de APIs
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}/"
WALLAPOP_API_URL = "https://api.wallapop.com/api/v3/search"

# Rutas según el perfil
DATABASE_PATH = "db.sqlite" if PROFILE else "/data/db.sqlite"
LOG_LEVEL = "DEBUG" if PROFILE else "INFO"
LOG_PATH = "wallbot.log" if PROFILE else "/logs/wallbot.log"
