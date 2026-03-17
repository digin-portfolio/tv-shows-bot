import logging
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8683002287:AAGmBWBrHvZAcg9ZblTRjkHz67UDsGh_Ce4")
DATABASE_URL = os.environ.get("DATABASE_URL", "")

if not DATABASE_URL:
    logger.error("DATABASE_URL is not set!")
    sys.exit(1)

try:
    from database import init_db
    init_db()
    logger.info("Database ready")
except Exception as e:
    logger.error(f"DB failed: {e}")
    sys.exit(1)

from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from handlers.start import start_handler, deep_link_handler
from handlers.search import search_handler
from handlers.admin import admin_panel_handler, add_file_handler, broadcast_handler, stats_handler, handle_file_upload
from handlers.force_sub import check_subscription_callback
from handlers.auto_post import setup_auto_post

class PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *args):
        pass

port = int(os.environ.get("PORT", 8080))
server = HTTPServer(("0.0.0.0", port), PingHandler)
threading.Thread(target=server.serve_forever, daemon=True).start()
logger.info(f"Web server started on port {port}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("admin", admin_panel_handler))
    app.add_handler(CommandHandler("broadcast", broadcast_handler))
    app.add_handler(CommandHandler("stats", stats_handler))
    app.add_handler(CommandHandler("addfile", add_file_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.VIDEO, handle_file_upload))
    app.add_handler(CallbackQueryHandler(check_subscription_callback, pattern="^check_sub$"))
    app.add_handler(CallbackQueryHandler(deep_link_handler, pattern="^get_file:"))
    setup_auto_post(app)
    logger.info("Bot is running!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
