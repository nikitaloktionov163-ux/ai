from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from app.core.config import get_settings
from bot.services.messages import LANGUAGE_PROMPT, MAIN_MENU_TEXT, WELCOME_MESSAGE

settings = get_settings()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    context.user_data["language"] = "EN"
    await update.message.reply_text(WELCOME_MESSAGE)

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("English", callback_data="lang_EN")],
            [InlineKeyboardButton("Русский", callback_data="lang_RU")],
        ]
    )
    await update.message.reply_text(LANGUAGE_PROMPT, reply_markup=keyboard)


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    language = query.data.replace("lang_", "")
    context.user_data["language"] = language

    await query.edit_message_text(f"Language set to {language}.")
    await show_main_menu(update, context)


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🏦 Choose exchange", callback_data="menu_exchange")],
            [InlineKeyboardButton("📊 Analyze chart", callback_data="menu_analyze")],
            [InlineKeyboardButton("💳 Subscription", callback_data="menu_subscription")],
            [InlineKeyboardButton("🎓 Learn trading", callback_data="menu_learn")],
            [InlineKeyboardButton("📈 Market Overview", callback_data="menu_market")],
            [InlineKeyboardButton("🌍 Change language", callback_data="menu_language")],
            [InlineKeyboardButton("❓ FAQ / Support", callback_data="menu_faq")],
        ]
    )
    if update.callback_query:
        await update.callback_query.message.reply_text(MAIN_MENU_TEXT, reply_markup=keyboard)
    else:
        await update.message.reply_text(MAIN_MENU_TEXT, reply_markup=keyboard)
