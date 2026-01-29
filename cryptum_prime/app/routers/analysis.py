from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.db.models import Signal
from app.services.ai_service import AIService
from app.services.validation import validate_pair_timeframe

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/chart")
async def analyze_chart(
    pair_timeframe: str,
    user_id: int | None = None,
    image: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, str | int | None]:
    validation = validate_pair_timeframe(pair_timeframe)
    if not validation.is_valid:
        raise HTTPException(status_code=400, detail=validation.message)

    image_bytes = await image.read()
    ai_service = AIService()
    analysis = await ai_service.analyze_chart(
        image_bytes,
        validation.normalized_pair or "",
        validation.normalized_timeframe or "",
    )

    signal = Signal(
        user_id=user_id or 0,
        pair=validation.normalized_pair or "",
        timeframe=validation.normalized_timeframe or "",
        signal=analysis.signal,
        entry=analysis.entry,
        stop_loss=analysis.stop_loss,
        take_profit=analysis.take_profit,
        confidence=analysis.confidence,
    )
    session.add(signal)
    await session.commit()

    return {
        "signal": analysis.signal,
        "reasoning": analysis.reasoning,
        "entry": analysis.entry,
        "stop_loss": analysis.stop_loss,
        "take_profit": analysis.take_profit,
        "risks": analysis.risks,
        "confidence": analysis.confidence,
    }
