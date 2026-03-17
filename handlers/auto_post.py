import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from database import add_file
from config import AUTO_POST_CHANNEL_ID, ADMIN_IDS
import re

logger = logging.getLogger(__name__)

def _parse_filename(filename):
    name = filename.rsplit(".", 1)[0]
    name = name.replace(".", " ").replace("_", " ")
    season, episode = 0, 0
    se_match = re.search(r"[Ss](\d{1,2})[Ee](\d{1,2})", name)
    if se_match:
        season = int(se_match.group(1))
        episode = int(se_match.group(2))
        title = name[:se_match.start()].strip()
    else:
        title = re.sub(r"\b(720p|1080p|4K|WEBRip|BluRay|HDRip|x265|x264|HEVC|AAC|2CH)\b", "", name, flags=re.IGNORECASE).strip()
    title = re.sub(r"\s+", " ", title).strip() or filename
    return title, season, episode

async def _auto_index(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.channel_post or update.message
    if not msg:
        return
    if msg.chat_id != AUTO_POST_CHANNEL_ID:
        return
    if msg.video:
        tg_file = msg.video
        file_type = "video"
    elif msg.document:
        tg_file = msg.document
        file_type = "document"
    else:
        return
    raw_name = tg_file.file_name or "Unknown"
    size_mb = (tg_file.file_size or 0) / (1024 * 1024)
    title, season, episode = _parse_filename(raw_name)
    success = add_file(
        title=title, filename=raw_name, file_id=tg_file.file_id,
        file_type=file_type, size_mb=round(size_mb, 2),
        season=season, episode=episode, added_by=0
    )
    status = "✅ Indexed" if success else "⚠️ Duplicate"
    logger.info(f"Auto-post: {status} → {raw_name}")
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin_id,
                f"🤖 *Auto-indexed*\n📁 `{raw_name}`\n🎬 {title}\n💾 {size_mb:.2f} MB\n{status}",
                parse_mode="Markdown"
            )
        except Exception:
            pass

def setup_auto_post(app: Application):
    app.add_handler(
        MessageHandler(
            (filters.VIDEO | filters.Document.ALL) & filters.ChatType.CHANNEL,
            _auto_index
        )
    )
    logger.info("Auto-post listener registered.")
