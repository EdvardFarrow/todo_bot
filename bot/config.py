from decouple import config


BOT_TOKEN = config("BOT_TOKEN")

API_BASE_URL = config("API_BASE_URL", default="http://127.0.0.1:8000/api/v1")

GEMINI_API_KEY = config("GEMINI_API_KEY")