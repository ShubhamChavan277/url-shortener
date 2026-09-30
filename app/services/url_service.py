from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.url import URL
from app.models.url_click import URLClick
from app.services.short_code import generate_short_code


MAX_CREATION_ATTEMPTS = 5


def create_short_url(
    db: Session,
    original_url: str,
    user_id: int,
    expires_at: datetime | None = None,
) -> URL:
    """Create and persist a shortened URL owned by a user."""
    for _ in range(MAX_CREATION_ATTEMPTS):
        short_code = generate_short_code()

        url = URL(
            original_url=original_url,
            short_code=short_code,
            user_id=user_id,
            expires_at=expires_at,
        )

        db.add(url)

        try:
            db.commit()
            db.refresh(url)
            return url
        except IntegrityError:
            db.rollback()

    raise RuntimeError("Unable to generate a unique short code.")


def get_url_by_short_code(
    db: Session,
    short_code: str,
) -> URL | None:
    """Retrieve a URL record by its short code."""
    statement = select(URL).where(URL.short_code == short_code)
    return db.scalar(statement)


def get_user_urls(
    db: Session,
    user_id: int,
) -> list[URL]:
    """Retrieve URLs owned by a user."""
    statement = (
        select(URL)
        .where(URL.user_id == user_id)
        .order_by(URL.created_at.desc())
    )
    return list(db.scalars(statement).all())


def get_user_url_by_short_code(
    db: Session,
    short_code: str,
    user_id: int,
) -> URL | None:
    """Retrieve a URL only when it belongs to the given user."""
    statement = select(URL).where(
        URL.short_code == short_code,
        URL.user_id == user_id,
    )
    return db.scalar(statement)


def delete_url(
    db: Session,
    url: URL,
) -> None:
    """Delete a URL and its associated click records."""
    db.execute(delete(URLClick).where(URLClick.url_id == url.id))
    db.delete(url)
    db.commit()
