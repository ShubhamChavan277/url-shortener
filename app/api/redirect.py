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

    record_click(db, url.id)

    return RedirectResponse(url=url.original_url)
