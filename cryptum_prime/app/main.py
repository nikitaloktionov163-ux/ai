from fastapi import FastAPI

from app.core.config import get_settings
from app.routers import analysis, health, payments

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.include_router(health.router)
app.include_router(analysis.router)
app.include_router(payments.router)
