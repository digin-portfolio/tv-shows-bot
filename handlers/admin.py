import re
from telegram import Update
from telegram.ext import ContextTypes
from database import add_file, get_stats, get_all_user_ids
from config import ADMIN_IDS

def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in ADMIN_IDS:
            await update.message.reply_text("⛔ Admin only.")
            return
        return await func(update, context)
    wrapper.__name__ = func.__name__
    return wrapper

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

@admin_only
async def admin_panel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = get_stats()
    await update.message.reply_text(
        f"🛠 *Admin Panel*\n\n📁 Files: `{stats['total_files']}`\n👤 Users: `{stats['total_users']}`\n\n"
        "• `/addfile` — manual add\n• `/stats` — statistics\n• `/broadcast <msg>` — send to all",
        parse_mode="Markdown"
    )

@admin_only
async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = get_stats()
    await update.message.reply_text(
        f"📊 *Stats*\n\n📁 Files: `{stats['total_files']}`\n👤 Users: `{stats['total_users']}`",
        parse_mode="Markdown"
    )

@admin_only
async def add_file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args and len(context.args) >= 2:
        file_id = context.args[0]
        title = " ".join(context.args[1:])
        success = add_file(title=title, filename=title, file_id=file_id, added_by=update.effective_user.id)
        msg = f"✅ Added: `{title}`" if success else "❌ Failed (duplicate?)"
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text("📤 Forward any video/document to index it.\nOr: `/addfile <file_id> <title>`", parse_mode="Markdown")

@admin_only
async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
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
        season=season, episode=episode, added_by=update.effective_user.id
    )
    if success:
        await msg.reply_text(
            f"✅ *Indexed!*\n🎬 `{title}`\n📺 S{season:02d}E{episode:02d}\n💾 {size_mb:.2f} MB",
            parse_mode="Markdown"
        )
    else:
        await msg.reply_text("⚠️ Already in database.")

@admin_only
async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/broadcast Your message`", parse_mode="Markdown")
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
    await update.message.reply_text(f"✅ Done! Sent: {sent} | Failed: {failed}")
