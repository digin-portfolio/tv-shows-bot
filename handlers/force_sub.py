from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError
import os

FORCE_SUB_CHANNELS = [
    {"id": "@mychannel1", "name": "Update Channel 1", "invite": "https://t.me/+tOUK3raFwCQwMjE1"},
    {"id": "@mychannel2", "name": "Update Channel 2", "invite": "https://t.me/+QOuWswFJbqBiOTZl"},
]

async def is_subscribed(bot, user_id: int) -> bool:
    for ch in FORCE_SUB_CHANNELS:
        try:
            member = await bot.get_chat_member(ch["id"], user_id)
            if member.status in ("left", "kicked", "banned"):
                return False
        except TelegramError:
            return False
    return True

def build_join_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(f"📢 {ch['name']}", url=ch["invite"])]
        for ch in FORCE_SUB_CHANNELS
    ]
    buttons.append([InlineKeyboardButton("✅ I've Joined — Verify", callback_data="check_sub")])
    return InlineKeyboardMarkup(buttons)

async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if await is_subscribed(context.bot, user_id):
        await query.message.edit_text(
            "✅ *Verified! Now send me a movie or series name to search.*",
            parse_mode="Markdown"
        )
        from database import pop_pending_search
        from handlers.search import perform_search
        pending = pop_pending_search(user_id)
        if pending:
            await perform_search(update, context, query_text=pending, user_id=user_id)
    else:
        await query.answer("❌ You haven't joined all channels yet!", show_alert=True)
