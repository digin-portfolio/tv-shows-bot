"""
handlers/force_sub.py
Checks whether a user has joined all required channels before serving files.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from config import FORCE_SUB_CHANNELS


async def is_subscribed(bot, user_id: int) -> bool:
    """Return True only if user is a member of ALL force-sub channels."""
    for ch in FORCE_SUB_CHANNELS:
        try:
            member = await bot.get_chat_member(ch["id"], user_id)
            if member.status in ("left", "kicked", "banned"):
                return False
        except TelegramError:
            # Can't check → assume not subscribed (safe default)
            return False
    return True


def build_join_keyboard(pending_callback: str | None = None) -> InlineKeyboardMarkup:
    """Build inline keyboard with join buttons + a verify button."""
    buttons = [
        [InlineKeyboardButton(
            f"📢 {ch['name']}",
            url=ch["invite"]
        )]
        for ch in FORCE_SUB_CHANNELS
    ]
    buttons.append([InlineKeyboardButton("✅ I've Joined — Verify", callback_data="check_sub")])
    return InlineKeyboardMarkup(buttons)


async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Called when user taps the 'I've Joined' button."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if await is_subscribed(context.bot, user_id):
        await query.message.edit_text(
            "✅ *Subscription verified!*\n\nNow send me the movie/series name to search.",
            parse_mode="Markdown"
        )
        # If there was a pending search stored, re-trigger it
        from database import pop_pending_search
        from handlers.search import perform_search
        pending = pop_pending_search(user_id)
        if pending:
            await perform_search(update, context, query_text=pending, user_id=user_id)
    else:
        await query.answer(
            "❌ You haven't joined all channels yet. Please join and try again.",
            show_alert=True
        )
