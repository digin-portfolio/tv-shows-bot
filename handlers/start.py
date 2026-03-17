from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import os, sys

sys.path.insert(0, '/app')

from database import (
    upsert_user,
    set_pending_search,
    set_pending_file,
    get_pending_file,
    get_file_by_id
)

from handlers.force_sub import is_subscribed, build_join_keyboard

BOT_USERNAME = os.environ.get("BOT_USERNAME", "TELEVISION_SHOWSBOT")


WELCOME_TEXT = """
👋 *Welcome to TV Shows Bot!*

I can help you find and download movies & series.

🔍 *How to use:*
Just type the name of any movie or series!

_Example: `One Piece Season 2`_
"""


# ------------------ START HANDLER ------------------
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message

    upsert_user(user.id, user.username or "", user.first_name or "")

    args = context.args

    # 🔥 HANDLE FILE DEEP LINK (MOST IMPORTANT)
    if args:
        data = args[0]

        # ---------------- FILE CLICK ----------------
        if data.startswith("file_"):
            file_id = int(data.split("_")[1])

            # ❌ NOT SUBSCRIBED
            if not await is_subscribed(context.bot, user.id):
                set_pending_file(user.id, file_id)

                keyboard = [
                    [InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/yourchannel1")],
                    [InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/yourchannel2")],
                    [InlineKeyboardButton("✅ Try Again", callback_data="try_again")]
                ]

                await message.reply_text(
                    "🔒 *You must join our channels first!*\n\nAfter joining, click ✅ *Try Again*.",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return

            # ✅ USER IS SUBSCRIBED → SEND FILE
            await send_file_by_id(context, user.id, file_id)
            return

        # ---------------- SEARCH DEEP LINK ----------------
        if data.startswith("search_"):
            query = data.replace("search_", "").replace("_", " ")

            if not await is_subscribed(context.bot, user.id):
                set_pending_search(user.id, query)

                await message.reply_text(
                    f"🔒 *Join our channels first!*\n\n🎬 *Requested:* `{query}`\n\nTap after joining.",
                    parse_mode="Markdown",
                    reply_markup=build_join_keyboard()
                )
                return

            from handlers.search import perform_search
            await perform_search(update, context, query_text=query, user_id=user.id)
            return

    # ---------------- NORMAL START ----------------
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Search Files", switch_inline_query_current_chat="")]
    ])

    await message.reply_text(WELCOME_TEXT, parse_mode="Markdown", reply_markup=keyboard)


# ------------------ TRY AGAIN HANDLER ------------------
async def try_again_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user

    await query.answer()

    # ❌ STILL NOT JOINED
    if not await is_subscribed(context.bot, user.id):
        await query.message.reply_text("❌ You still need to join all channels.")
        return

    # ✅ GET STORED FILE
    file_id = get_pending_file(user.id)

    if not file_id:
        await query.message.reply_text("⚠️ No pending file found.")
        return

    await send_file_by_id(context, user.id, file_id)


# ------------------ SEND FILE ------------------
async def send_file_by_id(context, user_id, file_id):
    file_rec = get_file_by_id(int(file_id))

    if not file_rec:
        await context.bot.send_message(chat_id=user_id, text="❌ File not found.")
        return

    size_str = f"{file_rec['size_mb']:.2f} MB" if file_rec.get("size_mb") else ""

    caption = f"🎬 *{file_rec['title']}*\n📁 `{file_rec['filename']}`\n💾 {size_str}"

    try:
        if file_rec.get("file_type") == "document":
            await context.bot.send_document(
                chat_id=user_id,
                document=file_rec["file_id"],
                caption=caption,
                parse_mode="Markdown"
            )
        else:
            await context.bot.send_video(
                chat_id=user_id,
                video=file_rec["file_id"],
                caption=caption,
                parse_mode="Markdown"
            )
    except Exception:
        await context.bot.send_document(
            chat_id=user_id,
            document=file_rec["file_id"],
            caption=caption,
            parse_mode="Markdown"
        )
