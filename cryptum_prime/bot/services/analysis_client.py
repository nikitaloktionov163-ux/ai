import httpx

from app.core.config import get_settings


class AnalysisClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.public_base_url

    async def analyze_chart(self, image_bytes: bytes, symbol: str, timeframe: str, user_id: int) -> dict:
        async with httpx.AsyncClient() as client:
            files = {"image": ("chart.png", image_bytes, "image/png")}
            response = await client.post(
                f"{self.base_url}/analysis/chart",
                params={"symbol": symbol, "timeframe": timeframe, "user_id": user_id},
                files=files,
                timeout=60,
            )
            if response.status_code >= 400:
                payload = response.json()
                detail = payload.get("detail", {})
                if isinstance(detail, dict):
                    return detail
                return {"error": "request_failed", "message": str(detail)}
            return response.json()
