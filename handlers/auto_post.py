"""
handlers/start.py
/start command + deep-link entry point (t.me/Bot?start=search_One_Piece_2023)
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import upsert_user, set_pending_search
from handlers.force_sub import is_subscribed, build_join_keyboard
from config import BOT_USERNAME


WELCOME_TEXT = """
👋 *Welcome to Movie Bot!*

I can help you find and download movies & series.

🔍 *How to use:*
Just type the name of any movie or series and I'll find it for you!

_Example: `One Piece Season 2`_
"""


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    upsert_user(user.id, user.username or "", user.first_name or "")

    args = context.args  # Text after /start

    # ── Deep-link: /start search_One_Piece_2023 ──────────────
    if args and args[0].startswith("search_"):
        query = args[0].replace("search_", "").replace("_", " ")

        # Force-subscribe gate
        if not await is_subscribed(context.bot, user.id):
            set_pending_search(user.id, query)
            await update.message.reply_text(
                f"🔒 *Join our channels first to get your file!*\n\n"
                f"🎬 *Requested:* `{query}`\n\n"
                f"After joining, tap ✅ *I've Joined — Verify* below.",
                parse_mode="Markdown",
                reply_markup=build_join_keyboard()
            )
            return

        # Subscribed → run the search directly
        from handlers.search import perform_search
        await perform_search(update, context, query_text=query, user_id=user.id)
        return

    # ── Normal /start ─────────────────────────────────────────
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Search Files", switch_inline_query_current_chat="")],
        [InlineKeyboardButton("📢 Updates Channel", url=f"https://t.me/{BOT_USERNAME}")]
    ])
    await update.message.reply_text(
        WELCOME_TEXT, parse_mode="Markdown", reply_markup=keyboard
    )


async def deep_link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles 'get_file:<db_id>' callback buttons from search results."""
    query = update.callback_query
    await query.answer()

    _, db_id = query.data.split(":")
    from database import get_file_by_id
    file_rec = get_file_by_id(int(db_id))

    if not file_rec:
        await query.message.reply_text("❌ File not found. It may have been removed.")
        return

    size_str = f"{file_rec['size_mb']:.2f} MB" if file_rec.get("size_mb") else ""
    caption = (
        f"🎬 *{file_rec['title']}*\n"
        f"📁 `{file_rec['filename']}`\n"
        f"💾 {size_str}"
    )

    try:
        if file_rec.get("file_type") == "document":
            await query.message.reply_document(
                file_rec["file_id"], caption=caption, parse_mode="Markdown"
            )
        else:
            await query.message.reply_video(
                file_rec["file_id"], caption=caption, parse_mode="Markdown"
            )
    except Exception:
        # Fallback for any file type
        await query.message.reply_document(
            file_rec["file_id"], caption=caption, parse_mode="Markdown"
        )
