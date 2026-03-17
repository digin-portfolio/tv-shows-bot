"""
Telegram Movie Bot - Main Entry Point
Features: Search by name, Force Subscribe Gate, Auto-post from channel, Admin Upload Panel
"""

import logging
import asyncio
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters
)
from config import BOT_TOKEN
from handlers.start import start_handler, deep_link_handler
from handlers.search import search_handler
from handlers.admin import (
    admin_panel_handler, add_file_handler,
    broadcast_handler, stats_handler, handle_file_upload
)
from handlers.force_sub import check_subscription_callback
from handlers.auto_post import setup_auto_post

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Command Handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("admin", admin_panel_handler))
    app.add_handler(CommandHandler("broadcast", broadcast_handler))
    app.add_handler(CommandHandler("stats", stats_handler))
    app.add_handler(CommandHandler("addfile", add_file_handler))

    # Message Handlers
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, search_handler
    ))
    app.add_handler(MessageHandler(
        filters.Document.ALL | filters.VIDEO, handle_file_upload
    ))

    # Callback Query Handlers
    app.add_handler(CallbackQueryHandler(
        check_subscription_callback, pattern="^check_sub$"
    ))
    app.add_handler(CallbackQueryHandler(
        deep_link_handler, pattern="^get_file:"
    ))

    # Auto-post listener setup
    setup_auto_post(app)

    logger.info("🤖 Bot is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
