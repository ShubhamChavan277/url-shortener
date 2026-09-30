from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.analytics_service import record_click
from app.services.url_service import get_url_by_short_code


router = APIRouter()


@router.get("/{short_code}")
def redirect_to_original_url(
    short_code: str,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Redirect a short code to its original URL."""
    url = get_url_by_short_code(db, short_code)

    if url is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found.",
        )

    if url.expires_at is not None:
        expiration_time = url.expires_at

        if expiration_time.tzinfo is None:
            expiration_time = expiration_time.replace(tzinfo=timezone.utc)

        if expiration_time <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Short URL has expired.",
            )

    record_click(db, url.id)

    return RedirectResponse(
        url=url.original_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )
