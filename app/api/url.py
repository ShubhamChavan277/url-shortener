from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import AnyHttpUrl, BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.rate_limit import enforce_rate_limit
from app.core.security import get_current_user_id
from app.db.session import get_db
from app.services.url_service import (
    create_short_url,
    delete_url,
    get_user_url_by_short_code,
    get_user_urls,
)


router = APIRouter()


class URLCreateRequest(BaseModel):
    original_url: AnyHttpUrl
    expires_at: datetime | None = None


class URLResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_url: AnyHttpUrl
    short_code: str
    user_id: int
    expires_at: datetime | None
    created_at: datetime


@router.post(
    "/api/v1/urls",
    response_model=URLResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_url(
    request: URLCreateRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
) -> URLResponse:
    """Create a shortened URL for the authenticated user."""

    enforce_rate_limit(http_request, "url_create")

    if request.expires_at is not None and request.expires_at <= datetime.now(
        request.expires_at.tzinfo
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expiration time must be in the future.",
        )

    try:
        url = create_short_url(
            db=db,
            original_url=str(request.original_url),
            user_id=current_user_id,
            expires_at=request.expires_at,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create short URL.",
        ) from exc

    return URLResponse.model_validate(url)


@router.get(
    "/api/v1/urls",
    response_model=list[URLResponse],
)
def list_urls(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
) -> list[URLResponse]:
    """List shortened URLs owned by the authenticated user."""
    urls = get_user_urls(db, current_user_id)
    return [URLResponse.model_validate(url) for url in urls]


@router.delete(
    "/api/v1/urls/{short_code}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user_url(
    short_code: str,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
) -> None:
    """Delete a shortened URL owned by the authenticated user."""
    url = get_user_url_by_short_code(db, short_code, current_user_id)

    if url is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found.",
        )

    delete_url(db, url)
