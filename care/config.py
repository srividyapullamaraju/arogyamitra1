import os

# API Keys
TELEGRAM_BOT_TOKEN = "8395025281:AAGWN1Za9Ak9yyoEU_f0kfkfrwYxOxnBzuY"
GEMINI_API_KEY = "AIzaSyA3_WAvqpijgn6kFW6oaRJOipBQZenksvk"
MAPS_API_EMAIL = os.getenv("MAPS_API_EMAIL", "caregenie-bot@example.com")

# Bot Settings
MAX_MESSAGE_LENGTH = 4000
# Primary/secondary model defaults can be overridden via env vars.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "models/gemini-2.0-flash-thinking-exp-01-21")
GEMINI_MAX_CALLS_PER_MINUTE = int(os.getenv("GEMINI_MAX_CALLS_PER_MINUTE", "8"))

# Timezone (IANA name, e.g., "Asia/Kolkata", "Europe/Berlin")
BOT_TIMEZONE = os.getenv("BOT_TIMEZONE", "Asia/Kolkata")

MAPS_GEOSERVICE = {
    "radius": int(os.getenv("HOSPITAL_SEARCH_RADIUS", "5000")),  # meters
    "contact_email": MAPS_API_EMAIL,
}
MAPS_MAX_RESULTS = int(os.getenv("HOSPITAL_MAX_RESULTS", "5"))