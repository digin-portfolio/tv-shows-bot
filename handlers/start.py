from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import os, sys
sys.path.insert(0, '/app')
from database import upsert_user, set_pending_search
from handlers.force_sub import is_subscribed, build_join_keyboard

BOT_USERNAME = os.environ.get("BOT_USERNAME", "TELEVISION_SHOWSBOT")

WELCOME_TEXT = """
👋 *Welcome to TV Shows Bot!*

I can help you find and download movies & series.

🔍 *How to use:*
Just type the name of any movie or series!

_Example: `One Piece Season 2`_
"""

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    upsert_user(user.id, user.username or "", user.first_name or "")
    args = context.args

    if args and args[0].startswith("search_"):
        query = args[0].replace("search_", "").replace("_", " ")
        if not await is_subscribed(context.bot, user.id):
            set_pending_search(user.id, query)
            await update.message.reply_text(
                f"🔒 *Join our channels first!*\n\n🎬 *Requested:* `{query}`\n\nTap ✅ after joining.",
                parse_mode="Markdown",
                reply_markup=build_join_keyboard()
            )
            return
        from handlers.search import perform_search
        await perform_search(update, context, query_text=query, user_id=user.id)
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Search Files", switch_inline_query_current_chat="")]
    ])
    await update.message.reply_text(WELCOME_TEXT, parse_mode="Markdown", reply_markup=keyboard)


async def deep_link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, db_id = query.data.split(":")
    import sys
    sys.path.insert(0, '/app')
    from database import get_file_by_id
    file_rec = get_file_by_id(int(db_id))
    if not file_rec:
        await query.message.reply_text("❌ File not found.")
        return
    size_str = f"{file_rec['size_mb']:.2f} MB" if file_rec.get("size_mb") else ""
    caption = f"🎬 *{file_rec['title']}*\n📁 `{file_rec['filename']}`\n💾 {size_str}"
    try:
        if file_rec.get("file_type") == "document":
            await query.message.reply_document(file_rec["file_id"], caption=caption, parse_mode="Markdown")
        else:
            await query.message.reply_video(file_rec["file_id"], caption=caption, parse_mode="Markdown")
    except Exception:
        await query.message.reply_document(file_rec["file_id"], caption=caption, parse_mode="Markdown")
