"""
handlers/auto_post.py
Monitors AUTO_POST_CHANNEL_ID for new video/document posts
and automatically indexes them in the database.
"""

from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from database import add_file
from handlers.admin import _parse_filename
from config import AUTO_POST_CHANNEL_ID, ADMIN_IDS
import logging

logger = logging.getLogger(__name__)


async def _auto_index(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Called whenever a message arrives in the source channel."""
    msg = update.channel_post or update.message
    if not msg:
        return

    # Only process messages from the designated channel
    chat_id = msg.chat_id
    if chat_id != AUTO_POST_CHANNEL_ID:
        return

    tg_file = None
    file_type = "video"

    if msg.video:
        tg_file  = msg.video
        file_type = "video"
        raw_name  = tg_file.file_name or "Unknown"
        size_mb   = (tg_file.file_size or 0) / (1024 * 1024)
    elif msg.document:
        tg_file  = msg.document
        file_type = "document"
        raw_name  = tg_file.file_name or "Unknown"
        size_mb   = (tg_file.file_size or 0) / (1024 * 1024)
    else:
        return  # Not a file post — skip

    file_id = tg_file.file_id
    title, season, episode = _parse_filename(raw_name)

    success = add_file(
        title=title,
        filename=raw_name,
        file_id=file_id,
        file_type=file_type,
        size_mb=round(size_mb, 2),
        season=season,
        episode=episode,
        added_by=0   # 0 = auto-indexed
    )

    status = "✅ Indexed" if success else "⚠️ Duplicate"
    logger.info(f"Auto-post: {status} → {raw_name}")

    # Notify admins silently
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin_id,
                f"🤖 *Auto-indexed*\n"
                f"📁 `{raw_name}`\n"
                f"🎬 {title}  S{season:02d}E{episode:02d}\n"
                f"💾 {size_mb:.2f} MB\n"
                f"Status: {status}",
                parse_mode="Markdown"
            )
        except Exception:
            pass


def setup_auto_post(app: Application):
    """Register the auto-index handler on the application."""
    app.add_handler(
        MessageHandler(
            (filters.VIDEO | filters.Document.ALL) & filters.ChatType.CHANNEL,
            _auto_index
        )
    )
    logger.info("Auto-post listener registered.")
