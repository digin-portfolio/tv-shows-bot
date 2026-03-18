from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_file_by_id, upsert_user
from handlers.force_sub import is_subscribed, build_join_keyboard

WELCOME_TEXT = """
👋 *Welcome to TV Shows Bot!*

Send a movie or series name to search.
"""


# ------------------ START HANDLER ------------------
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message

    upsert_user(user.id, user.username or "", user.first_name or "")

    args = context.args

    # 🔥 HANDLE FILE DEEP LINK
    if args and args[0].startswith("file_"):
        file_id = int(args[0].split("_")[1])

        # 🔒 check subscription
        if not await is_subscribed(context.bot, user.id):
            await message.reply_text(
                "🔒 Join channels first, then click again.",
                reply_markup=build_join_keyboard()
            )
            return

        file = get_file_by_id(file_id)

        if not file:
            await message.reply_text("❌ File not found.")
            return

        caption = f"🎬 *{file['title']}*\n💾 {file['size_mb']} MB"

        try:
            if file["file_type"] == "video":
                await message.reply_video(
                    file["file_id"],
                    caption=caption,
                    parse_mode="Markdown"
                )
            else:
                await message.reply_document(
                    file["file_id"],
                    caption=caption,
                    parse_mode="Markdown"
                )
        except:
            await message.reply_document(
                file["file_id"],
                caption=caption,
                parse_mode="Markdown"
            )

        return

    # ------------------ NORMAL START ------------------
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Search", switch_inline_query_current_chat="")]
    ])

    await message.reply_text(
        WELCOME_TEXT,
        parse_mode="Markdown",
        reply_markup=keyboard
    )
