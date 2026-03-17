# ============================================================
#  config.py  —  Fill in your values before running the bot
# ============================================================

# --- Bot credentials (from @BotFather) ---
BOT_TOKEN = "8683002287:AAGmBWBrHvZAcg9ZblTRjkHz67UDsGh_Ce4"

# --- Admin user IDs (Telegram numeric IDs) ---
ADMIN_IDS = [1059586105]

# --- Force-subscribe channels ---
# Bot must be admin in these channels
FORCE_SUB_CHANNELS = [
    {"id": "@mychannel1", "name": "Update Channel 1", "invite": "https://t.me/+tOUK3raFwCQwMjE1"},
    {"id": "@mychannel2", "name": "Update Channel 2", "invite": "https://t.me/+QOuWswFJbqBiOTZl"},
]

# --- Private storage channel ---
# Upload files here; bot reads file_id automatically
# Bot must be admin in this channel
STORAGE_CHANNEL_ID = -1003779826671

# --- Auto-post source channel ---
# Bot monitors this channel and indexes new files automatically
AUTO_POST_CHANNEL_ID = -1003624969886

# --- Database ---
# PostgreSQL — DATABASE_URL is set automatically by Railway Postgres plugin
# No changes needed here!

# --- Misc ---
MAX_SEARCH_RESULTS = 8
BOT_USERNAME = "TELEVISION_SHOWSBOT"   # Without @
