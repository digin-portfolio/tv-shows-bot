import os

# --- Bot credentials ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8683002287:AAGmBWBrHvZAcg9ZblTRjkHz67UDsGh_Ce4")

# --- Admin user IDs ---
ADMIN_IDS = [1059586105]

# --- Force-subscribe channels ---
FORCE_SUB_CHANNELS = [
    {"id": "@mychannel1", "name": "Update Channel 1", "invite": "https://t.me/+tOUK3raFwCQwMjE1"},
    {"id": "@mychannel2", "name": "Update Channel 2", "invite": "https://t.me/+QOuWswFJbqBiOTZl"},
]

# --- Private storage channel ---
STORAGE_CHANNEL_ID = -1003779826671

# --- Auto-post source channel ---
AUTO_POST_CHANNEL_ID = -1003624969886

# --- Misc ---
MAX_SEARCH_RESULTS = 8
BOT_USERNAME = "TELEVISION_SHOWSBOT"
