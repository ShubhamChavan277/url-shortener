import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.analytics_service import record_click
from app.services.url_cache import get_cached_url, set_cached_url
from app.services.url_service import get_url_by_short_code
from app.core.rate_limit import enforce_rate_limit


logger = logging.getLogger(__name__)


router = APIRouter()


@router.get("/{short_code}")
def redirect_to_original_url(
    short_code: str,
    request: Request,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Redirect a short code to its original URL."""

    enforce_rate_limit(request, "url_redirect")

    cached_url = get_cached_url(short_code)

    if cached_url is not None:
        record_click(db, cached_url["id"])

        logger.info(
            "Redirect successful for %s using cache",
            short_code,
        )

        return RedirectResponse(
            url=cached_url["original_url"],
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    url = get_url_by_short_code(db, short_code)

    if url is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found.",
        )

    if url.expires_at is not None:
        expiration_time = url.expires_at

        if expiration_time.tzinfo is None:
            expiration_time = expiration_time.replace(
                tzinfo=timezone.utc
            )

        if expiration_time <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Short URL has expired.",
            )

    set_cached_url(
        short_code=short_code,
        url_id=url.id,
        original_url=url.original_url,
        expires_at=url.expires_at,
    )

    record_click(db, url.id)

    logger.info(
        "Redirect successful for %s after database lookup",
        short_code,
    )

    return RedirectResponse(
        url=url.original_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )
