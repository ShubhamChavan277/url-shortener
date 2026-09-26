from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.analytics_service import get_click_count
from app.services.url_service import get_url_by_short_code


router = APIRouter()


class AnalyticsResponse(BaseModel):
    short_code: str
    click_count: int


@router.get(
    "/urls/{short_code}/analytics",
    response_model=AnalyticsResponse,
)
def get_url_analytics(
    short_code: str,
    db: Session = Depends(get_db),
) -> AnalyticsResponse:
    """Return basic click analytics for a shortened URL."""
    url = get_url_by_short_code(db, short_code)

    if url is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found.",
        )

    click_count = get_click_count(db, url.id)

    return AnalyticsResponse(
        short_code=url.short_code,
        click_count=click_count,
    )
