from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.rate_limit import enforce_rate_limit
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.schemas.auth import RegisterRequest
from app.schemas.user import TokenResponse, UserResponse
from app.services.user_service import create_user, get_user_by_email


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: RegisterRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    enforce_rate_limit(http_request, "auth_register")

    email = str(request.email).lower()

    if get_user_by_email(db, email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    try:
        return create_user(
            db=db,
            email=email,
            password_hash=hash_password(request.password),
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    http_request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    enforce_rate_limit(http_request, "auth_login")

    email = form_data.username.lower()
    user = get_user_by_email(db, email)

    if user is None or not verify_password(
        form_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(
        access_token=create_access_token(user.id),
        token_type="bearer",
    )
