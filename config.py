import os

# На Render токен подставится сам из переменной окружения BOT_TOKEN
# (Dashboard -> Environment -> Add Environment Variable)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "ВСТАВЬТЕ_СЮДА_ВАШ_ТОКЕН")

DB_PATH = "tgauth.db"
