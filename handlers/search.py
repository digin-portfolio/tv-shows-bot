from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import search_files, set_pending_search
from handlers.force_sub import is_subscribed, build_join_keyboard

MAX_SEARCH_RESULTS = 8

def _build_results_keyboard(results):
    buttons = []
    for r in results:
        ep_tag = ""
        if r.get("season") and r.get("episode"):
            ep_tag = f" S{r['season']:02d}E{r['episode']:02d}"
        size_tag = f" [{r['size_mb']:.0f}MB]" if r.get("size_mb") else ""
        label = f"📥 {r['title']}{ep_tag}{size_tag}"
        db_id = r.get("id")
        buttons.append([InlineKeyboardButton(label, callback_data=f"get_file:{db_id}")])
    return InlineKeyboardMarkup(buttons)

async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip()
    if not text:
        return
    if not await is_subscribed(context.bot, user.id):
        set_pending_search(user.id, text)
        await update.message.reply_text(
            "🔒 *You must join our channels first!*\n\nAfter joining, tap ✅ *I've Joined — Verify*.",
            parse_mode="Markdown",
            reply_markup=build_join_keyboard()
        )
        return
    await perform_search(update, context, query_text=text, user_id=user.id)

async def perform_search(update, context, query_text, user_id):
    msg_obj = update.message or (update.callback_query.message if update.callback_query else None)
    results = search_files(query_text, limit=MAX_SEARCH_RESULTS)
    if not results:
        await msg_obj.reply_text(
            f"❌ *No results for:* `{query_text}`\n\nTry a different keyword.",
            parse_mode="Markdown"
        )
        return
    await msg_obj.reply_text(
        f"🎯 *Found {len(results)} result(s) for:* `{query_text}`\n👇 Tap to get the file:",
        parse_mode="Markdown",
        reply_markup=_build_results_keyboard(results)
    )
