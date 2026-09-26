from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.url_click import URLClick


def record_click(db: Session, url_id: int) -> URLClick:
    """Record a click for a shortened URL."""
    click = URLClick(url_id=url_id)

    db.add(click)
    db.commit()
    db.refresh(click)

    return click


def get_click_count(db: Session, url_id: int) -> int:
    """Return the total number of clicks for a shortened URL."""
    statement = select(func.count()).select_from(URLClick).where(
        URLClick.url_id == url_id
    )

    return db.scalar(statement) or 0
