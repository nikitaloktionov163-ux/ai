from dataclasses import dataclass

from app.services.market_data import MarketDataService

ALLOWED_TIMEFRAMES = {"5m", "15m", "30m", "1h", "2h", "4h"}
COMMON_QUOTES = ("USDT", "USDC", "BUSD", "USD", "BTC", "ETH")


@dataclass
class ValidationResult:
    is_valid: bool
    message: str
    error: str | None = None
    normalized_symbol: str | None = None
    normalized_timeframe: str | None = None


def normalize_symbol(raw: str) -> str:
    return raw.strip().upper().replace("/", "").replace(" ", "")


def extract_base_symbol(symbol: str) -> str:
    for quote in COMMON_QUOTES:
        if symbol.endswith(quote) and len(symbol) > len(quote):
            return symbol[: -len(quote)]
    return symbol


async def validate_symbol_timeframe(symbol: str, timeframe: str) -> ValidationResult:
    normalized_symbol = normalize_symbol(symbol)
    normalized_timeframe = timeframe.strip().lower()
    if normalized_timeframe not in ALLOWED_TIMEFRAMES:
        return ValidationResult(
            is_valid=False,
            error="invalid_timeframe",
            message="Timeframe is not supported. Available: 5m, 15m, 30m, 1h, 2h, 4h.",
        )

    service = MarketDataService()
    base_symbol = extract_base_symbol(normalized_symbol)
    try:
        top500 = await service.get_top500_symbols()
    except RuntimeError:
        return ValidationResult(
            is_valid=False,
            error="market_data_unavailable",
            message="Market data is temporarily unavailable. Please try again shortly.",
        )
    if base_symbol not in top500:
        return ValidationResult(
            is_valid=False,
            error="coin_not_in_top500",
            message=(
                "Base coin is not in the top-500 by market cap. "
                "Please try another pair."
            ),
        )

    try:
        exchange_symbols = await service.get_exchange_symbols()
    except RuntimeError:
        return ValidationResult(
            is_valid=False,
            error="market_data_unavailable",
            message="Exchange data is temporarily unavailable. Please try again shortly.",
        )
    if normalized_symbol not in exchange_symbols:
        return ValidationResult(
            is_valid=False,
            error="symbol_not_trading",
            message="This symbol is not trading on Binance. Please try another pair.",
        )

    return ValidationResult(
        is_valid=True,
        message="OK",
        normalized_symbol=normalized_symbol,
        normalized_timeframe=normalized_timeframe,
    )
