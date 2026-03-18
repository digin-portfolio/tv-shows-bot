import logging
import os
import sys
import threading
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler

# ------------------ LOGGING ------------------
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ------------------ ENV ------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")

if not BOT_TOKEN:
    logger.error("BOT_TOKEN is not set!")
    sys.exit(1)

if not DATABASE_URL:
    logger.error("DATABASE_URL is not set!")
    sys.exit(1)

# ------------------ DATABASE ------------------
try:
    from database import init_db
    init_db()
    logger.info("Database ready")
except Exception as e:
    logger.error(f"DB failed: {e}")
    sys.exit(1)

# ------------------ TELEGRAM ------------------
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

# ✅ FIXED IMPORT (REMOVED try_again_handler)
from handlers.start import start_handler
from handlers.search import search_handler
from handlers.admin import (
    admin_panel_handler,
    add_file_handler,
    broadcast_handler,
    stats_handler,
    handle_file_upload
)
from handlers.force_sub import check_subscription_callback
from handlers.auto_post import setup_auto_post

# ------------------ KEEP ALIVE SERVER ------------------
class PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, *args):
        return


def start_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), PingHandler)
    logger.info(f"Web server started on port {port}")
    server.serve_forever()


# ------------------ BOT MAIN ------------------
async def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()

    # ------------------ COMMANDS ------------------
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("admin", admin_panel_handler))
    app.add_handler(CommandHandler("broadcast", broadcast_handler))
    app.add_handler(CommandHandler("stats", stats_handler))
    app.add_handler(CommandHandler("addfile", add_file_handler))

    # ------------------ SEARCH ------------------
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler))

    # ------------------ FILE INDEXING (CHANNEL ONLY) ------------------
    app.add_handler(
        MessageHandler(
            (filters.Document.ALL | filters.VIDEO) & filters.ChatType.CHANNEL,
            handle_file_upload
        )
    )

    # ------------------ VERIFY ------------------
    app.add_handler(
        CallbackQueryHandler(check_subscription_callback, pattern="^check_sub$")
    )

    # ❌ REMOVED try_again_handler (NOT NEEDED)

    # ------------------ AUTO POST ------------------
    setup_auto_post(app)

    logger.info("Bot is running!")

    # ------------------ START BOT ------------------
    await app.initialize()
    await app.bot.delete_webhook(drop_pending_updates=True)

    await app.start()
    await app.updater.start_polling()

    await asyncio.Event().wait()


# ------------------ RUN ------------------
if __name__ == "__main__":
    threading.Thread(target=start_web_server, daemon=True).start()
    asyncio.run(run_bot())
