from dataclasses import dataclass

SUPPORTED_TIMEFRAMES = {"5M", "15M", "1H", "4H"}


@dataclass
class ValidationResult:
    is_valid: bool
    message: str
    normalized_pair: str | None = None
    normalized_timeframe: str | None = None


def validate_pair_timeframe(raw: str) -> ValidationResult:
    parts = raw.strip().upper().split()
    if len(parts) != 2:
        return ValidationResult(
            is_valid=False,
            message="Please send the pair and timeframe like: BTCUSDT 15M.",
        )
    pair, timeframe = parts
    if timeframe not in SUPPORTED_TIMEFRAMES:
        return ValidationResult(
            is_valid=False,
            message=(
                f"Timeframe {timeframe} is not supported. Available: 5M, 15M, 1H, 4H."
            ),
        )
    if len(pair) < 5:
        return ValidationResult(
            is_valid=False,
            message="The trading pair looks too short. Example: BTCUSDT 15M.",
        )
    return ValidationResult(
        is_valid=True,
        message="OK",
        normalized_pair=pair,
        normalized_timeframe=timeframe,
    )
