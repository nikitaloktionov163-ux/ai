import httpx

from app.core.config import get_settings


class APIClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.public_base_url

    async def health(self) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
