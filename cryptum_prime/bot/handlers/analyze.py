from dataclasses import dataclass

from telegram import Update
from telegram.ext import ContextTypes

from bot.services.analysis_client import AnalysisClient
from bot.services.messages import ANALYZE_PROMPT

ALLOWED_TIMEFRAMES = {"5m", "15m", "30m", "1h", "2h", "4h"}


@dataclass
class ParsedPairTimeframe:
    is_valid: bool
    message: str
    symbol: str | None = None
    timeframe: str | None = None


def parse_pair_timeframe(raw: str) -> ParsedPairTimeframe:
    parts = [part for part in raw.strip().replace("\n", " ").split(" ") if part]
    if len(parts) < 2:
        return ParsedPairTimeframe(
            is_valid=False,
            message=(
                "Please send the pair and timeframe, for example: SOLUSDT 5m or ETHUSDT 4h. "
                "You can also write: SOL 5m."
            ),
        )
    timeframe = parts[-1].lower()
    if timeframe not in ALLOWED_TIMEFRAMES:
        return ParsedPairTimeframe(
            is_valid=False,
            message=(
                f"Timeframe {timeframe} is not supported. "
                "Available: 5m, 15m, 30m, 1h, 2h, 4h."
            ),
        )
    symbol_parts = parts[:-1]
    base = ""
    quote = ""
    if len(symbol_parts) == 1:
        token = symbol_parts[0].replace(" ", "")
        if "/" in token:
            base, quote = (x for x in token.split("/", 1))
        else:
            base = token
    elif len(symbol_parts) == 2:
        base, quote = symbol_parts
    else:
        return ParsedPairTimeframe(
            is_valid=False,
            message=(
                "Please send the pair and timeframe in one of these formats: "
                "SOLUSDT 5m, SOL/USDT 5m, SOL USDT 5m, or SOL 5m."
            ),
        )
    base = base.strip().upper()
    quote = quote.strip().upper() if quote else "USDT"
    if not base:
        return ParsedPairTimeframe(
            is_valid=False,
            message="The trading pair looks empty. Example: SOLUSDT 5m.",
        )
    symbol = f"{base}{quote}"
    return ParsedPairTimeframe(
        is_valid=True,
        message="OK",
        symbol=symbol,
        timeframe=timeframe,
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.photo:
        return
    photo = update.message.photo[-1]
    file = await photo.get_file()
    image_bytes = await file.download_as_bytearray()
    context.user_data["chart_image"] = bytes(image_bytes)
    context.user_data["awaiting_pair_timeframe"] = True
    await update.message.reply_text(
        "Chart received. Now send the pair and timeframe, for example: SOLUSDT 5m or ETHUSDT 4h. "
        "You can also write: SOL 5m."
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    if not context.user_data.get("awaiting_pair_timeframe"):
        return

    parsed = parse_pair_timeframe(update.message.text)
    if not parsed.is_valid:
        await update.message.reply_text(parsed.message)
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
            parsed.symbol or "",
            parsed.timeframe or "",
            update.effective_user.id if update.effective_user else 0,
        )
    except Exception:
        await update.message.reply_text(
            "We could not complete the analysis right now. Please try again shortly."
        )
        return

    if response.get("error"):
        await update.message.reply_text(response.get("message", "Request failed."))
        return

    await update.message.reply_text(
        "🧠 Signal: {signal}\n"
        "📊 Technical reasoning: {reasoning}\n"
        "🎯 Entry / SL / TP: {entry} / {stop_loss} / {take_profit}\n"
        "⚠️ Risks: {risks}\n"
        "📉 Confidence: {confidence}%".format(
            signal=response.get("signal", "NO TRADE"),
            reasoning=response.get("reasoning", ""),
            entry=response.get("entry", "N/A"),
            stop_loss=response.get("stop_loss", "N/A"),
            take_profit=response.get("take_profit", "N/A"),
            risks=response.get("risks", ""),
            confidence=response.get("confidence", "N/A"),
        )
    )
