from fastapi import FastAPI

from app.api import analytics, auth, health, redirect, url
from app.core.config import settings
from app.core.logging import configure_logging


configure_logging()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(url.router)
app.include_router(analytics.router)
app.include_router(redirect.router)
