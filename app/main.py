from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.redirect import router as redirect_router
from app.api.url import router as url_router
from app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.include_router(health_router)
app.include_router(url_router)
app.include_router(redirect_router)