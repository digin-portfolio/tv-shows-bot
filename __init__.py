"""
handlers/admin.py
Admin commands: panel, add file, broadcast, stats, file upload listener.
"""

import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import add_file, get_stats, get_all_user_ids, get_all_files, delete_file
from config import ADMIN_IDS


# ── Guard decorator ───────────────────────────────────────

def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in ADMIN_IDS:
            await update.message.reply_text("⛔ Admin only.")
            return
        return await func(update, context)
    wrapper.__name__ = func.__name__
    return wrapper


# ── /admin ────────────────────────────────────────────────

@admin_only
async def admin_panel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = get_stats()
    text = (
        "🛠 *Admin Panel*\n\n"
        f"📁 Total Files : `{stats['total_files']}`\n"
        f"👤 Total Users : `{stats['total_users']}`\n\n"
        "*Commands:*\n"
        "• `/addfile` — enter manual file-add mode\n"
        "• `/stats` — show stats\n"
        "• `/broadcast <message>` — send to all users\n\n"
        "*Upload mode:*\n"
        "Just forward any video/document to this bot and it will be indexed automatically."
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ── /stats ────────────────────────────────────────────────

@admin_only
async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = get_stats()
    await update.message.reply_text(
        f"📊 *Stats*\n\n"
        f"📁 Files  : `{stats['total_files']}`\n"
        f"👤 Users  : `{stats['total_users']}`",
        parse_mode="Markdown"
    )


# ── /addfile (manual mode) ────────────────────────────────

@admin_only
async def add_file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📤 *Manual Add Mode*\n\n"
        "Forward a video or document to this bot.\n"
        "I'll auto-detect title, season, episode from the filename.\n\n"
        "Or send:\n`/addfile <file_id> <title>`",
        parse_mode="Markdown"
    )
    if context.args and len(context.args) >= 2:
        file_id = context.args[0]
        title = " ".join(context.args[1:])
        success = add_file(title=title, filename=title, file_id=file_id, added_by=update.effective_user.id)
        if success:
            await update.message.reply_text(f"✅ Added: `{title}`", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Failed to add (duplicate file_id?)")


# ── File upload listener ──────────────────────────────────

@admin_only
async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin sends/forwards a video or document → auto-index it."""
    msg = update.message
    user_id = update.effective_user.id

    if msg.video:
        tg_file = msg.video
        file_type = "video"
        raw_name = tg_file.file_name or "Unknown"
        size_mb = (tg_file.file_size or 0) / (1024 * 1024)
    elif msg.document:
        tg_file = msg.document
        file_type = "document"
        raw_name = tg_file.file_name or "Unknown"
        size_mb = (tg_file.file_size or 0) / (1024 * 1024)
    else:
        return

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
        added_by=user_id
    )

    if success:
        await msg.reply_text(
            f"✅ *Indexed!*\n"
            f"🎬 Title   : `{title}`\n"
            f"📺 S{season:02d}E{episode:02d}\n"
            f"💾 Size    : `{size_mb:.2f} MB`\n"
            f"🔑 File ID : `{file_id}`",
            parse_mode="Markdown"
        )
    else:
        await msg.reply_text("⚠️ Already in database (duplicate file_id).")


# ── /broadcast ────────────────────────────────────────────

@admin_only
async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/broadcast Your message here`", parse_mode="Markdown")
        return

    text = " ".join(context.args)
    user_ids = get_all_user_ids()
    sent, failed = 0, 0

    await update.message.reply_text(f"📡 Broadcasting to {len(user_ids)} users...")

    for uid in user_ids:
        try:
            await context.bot.send_message(uid, text)
            sent += 1
        except Exception:
            failed += 1

    await update.message.reply_text(
        f"✅ Broadcast done!\n✉️ Sent: {sent}\n❌ Failed: {failed}"
    )


# ── Helpers ───────────────────────────────────────────────

def _parse_filename(filename: str) -> tuple[str, int, int]:
    """
    Extract human title, season, episode from a filename like:
    One.Piece.2023.S02E05.720p.WEBRip.mkv
    """
    name = filename.rsplit(".", 1)[0]   # strip extension
    name = name.replace(".", " ").replace("_", " ")

    season, episode = 0, 0
    se_match = re.search(r"[Ss](\d{1,2})[Ee](\d{1,2})", name)
    if se_match:
        season  = int(se_match.group(1))
        episode = int(se_match.group(2))
        # Title = everything before the SxxExx tag
        title = name[:se_match.start()].strip()
    else:
        # No episode tag — use full name minus quality tags
        title = re.sub(r"\b(720p|1080p|4K|WEBRip|BluRay|HDRip|x265|x264|HEVC|AAC|2CH)\b",
                       "", name, flags=re.IGNORECASE).strip()

    # Clean up multiple spaces
    title = re.sub(r"\s+", " ", title).strip() or filename
    return title, season, episode
