from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.handlers.start import show_main_menu
from bot.services.messages import ANALYZE_PROMPT, FAQ_TEXT, SUBSCRIPTION_TEXT


async def menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == "menu_exchange":
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Binance", callback_data="exchange_binance")],
                [InlineKeyboardButton("Bybit", callback_data="exchange_bybit")],
                [InlineKeyboardButton("OKX", callback_data="exchange_okx")],
                [InlineKeyboardButton("KuCoin", callback_data="exchange_kucoin")],
            ]
        )
        await query.edit_message_text("Choose your exchange:", reply_markup=keyboard)
        return

    if action == "menu_analyze":
        context.user_data["awaiting_pair_timeframe"] = True
        await query.edit_message_text(ANALYZE_PROMPT)
        return

    if action == "menu_subscription":
        await query.edit_message_text(SUBSCRIPTION_TEXT)
        return

    if action == "menu_learn":
        await query.edit_message_text("Daily lessons and tips coming soon for PRO/PRIME.")
        return

    if action == "menu_market":
        await query.edit_message_text("Market overview is available for PRIME subscribers.")
        return

    if action == "menu_language":
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("English", callback_data="lang_EN")],
                [InlineKeyboardButton("Русский", callback_data="lang_RU")],
            ]
        )
        await query.edit_message_text("Choose your language:", reply_markup=keyboard)
        return

    if action == "menu_faq":
        await query.edit_message_text(FAQ_TEXT)
        return

    await show_main_menu(update, context)


async def exchange_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    exchange = query.data.replace("exchange_", "")
    context.user_data["exchange"] = exchange.upper()
    await query.edit_message_text(f"Exchange set to {exchange.upper()}.")
