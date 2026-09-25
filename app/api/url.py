from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import AnyHttpUrl, BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.url_service import create_short_url


router = APIRouter()


class URLCreateRequest(BaseModel):
    original_url: AnyHttpUrl


class URLResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_url: AnyHttpUrl
    short_code: str
    created_at: datetime


@router.post(
    "/urls",
    response_model=URLResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_url(
    request: URLCreateRequest,
    db: Session = Depends(get_db),
) -> URLResponse:
    """Create a shortened URL."""

    try:
        url = create_short_url(db, str(request.original_url))
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create short URL.",
        ) from exc

    return URLResponse.model_validate(url)