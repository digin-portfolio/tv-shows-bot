from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import search_files, set_pending_search
from handlers.force_sub import is_subscribed, build_join_keyboard

MAX_SEARCH_RESULTS = 8
BOT_USERNAME = "TELEVISION_SHOWSBOT"  # بدون @


# ------------------ NORMALIZE ------------------
def clean_query(text: str) -> str:
    text = text.strip().lower()

    # remove @botusername if used in group
    if text.startswith("@"):
        parts = text.split(" ", 1)
        if len(parts) > 1:
            text = parts[1]
        else:
            return ""

    # replace separators
    text = text.replace(".", " ").replace("_", " ").replace("-", " ")

    return text.strip()


# ------------------ BUTTONS ------------------
def _build_results_keyboard(results):
    buttons = []

    for r in results:
        ep_tag = ""
        if r.get("season") and r.get("episode"):
            ep_tag = f" S{r['season']:02d}E{r['episode']:02d}"

        size_tag = f" [{r['size_mb']:.0f}MB]" if r.get("size_mb") else ""
        label = f"📥 {r['title']}{ep_tag}{size_tag}"

        db_id = r.get("id")

        buttons.append([
            InlineKeyboardButton(
                label,
                url=f"https://t.me/{BOT_USERNAME}?start=file_{db_id}"
            )
        ])

    return InlineKeyboardMarkup(buttons)


# ------------------ SEARCH HANDLER ------------------
async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message

    if not message or not message.text:
        return

    text = clean_query(message.text)

    if not text:
        return

    # 🔒 subscription check
    if not await is_subscribed(context.bot, user.id):
        set_pending_search(user.id, text)

        await message.reply_text(
            "🔒 *You must join our channels first!*\n\nAfter joining, tap ✅ *I've Joined — Verify*.",
            parse_mode="Markdown",
            reply_markup=build_join_keyboard()
        )
        return

    await perform_search(update, context, text, user.id)


# ------------------ PERFORM SEARCH ------------------
async def perform_search(update, context, query_text, user_id):
    msg = update.effective_message

    results = search_files(query_text, limit=MAX_SEARCH_RESULTS)

    if not results:
        await msg.reply_text(
            f"❌ *No results for:* `{query_text}`\n\nTry a different keyword.",
            parse_mode="Markdown"
        )
        return

    await msg.reply_text(
        f"🎯 *Found {len(results)} result(s) for:* `{query_text}`\n👇 Tap to get the file:",
        parse_mode="Markdown",
        reply_markup=_build_results_keyboard(results)
    )
