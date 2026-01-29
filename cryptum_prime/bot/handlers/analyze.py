from telegram import Update
from telegram.ext import ContextTypes

from app.services.validation import validate_pair_timeframe
from bot.services.analysis_client import AnalysisClient
from bot.services.messages import ANALYZE_PROMPT


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.photo:
        return
    photo = update.message.photo[-1]
    file = await photo.get_file()
    image_bytes = await file.download_as_bytearray()
    context.user_data["chart_image"] = bytes(image_bytes)
    context.user_data["awaiting_pair_timeframe"] = True
    await update.message.reply_text(
        "Chart received. Now send the pair and timeframe like: BTCUSDT 15M."
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    if not context.user_data.get("awaiting_pair_timeframe"):
        return

    validation = validate_pair_timeframe(update.message.text)
    if not validation.is_valid:
        await update.message.reply_text(validation.message)
        return

    if not context.user_data.get("chart_image"):
        await update.message.reply_text(ANALYZE_PROMPT)
        return

    await update.message.reply_text(
        "Analysis queued. This may take a few seconds while we review the chart."
    )

    context.user_data["awaiting_pair_timeframe"] = False

    client = AnalysisClient()
    try:
        response = await client.analyze_chart(
            context.user_data["chart_image"],
            validation.normalized_pair or "",
            validation.normalized_timeframe or "",
            update.effective_user.id if update.effective_user else 0,
        )
    except Exception:
        await update.message.reply_text(
            \"We could not complete the analysis right now. Please try again shortly.\"
        )
        return

    await update.message.reply_text(
        \"🧠 Signal: {signal}\\n\"
        \"📊 Technical reasoning: {reasoning}\\n\"
        \"🎯 Entry / SL / TP: {entry} / {stop_loss} / {take_profit}\\n\"
        \"⚠️ Risks: {risks}\\n\"
        \"📉 Confidence: {confidence}%\".format(
            signal=response.get(\"signal\", \"NO TRADE\"),
            reasoning=response.get(\"reasoning\", \"\"),
            entry=response.get(\"entry\", \"N/A\"),
            stop_loss=response.get(\"stop_loss\", \"N/A\"),
            take_profit=response.get(\"take_profit\", \"N/A\"),
            risks=response.get(\"risks\", \"\"),
            confidence=response.get(\"confidence\", \"N/A\"),
        )
    )
