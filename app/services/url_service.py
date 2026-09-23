from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.url import URL
from app.services.short_code import generate_short_code


MAX_CREATION_ATTEMPTS = 5


def create_short_url(db: Session, original_url: str) -> URL:
    """Create and persist a shortened URL."""
    for _ in range(MAX_CREATION_ATTEMPTS):
        short_code = generate_short_code()

        url = URL(
            original_url=original_url,
            short_code=short_code,
        )

        db.add(url)

        try:
            db.commit()
            db.refresh(url)
            return url
        except IntegrityError:
            db.rollback()

    raise RuntimeError("Unable to generate a unique short code.")