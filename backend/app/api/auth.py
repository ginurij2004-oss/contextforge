from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm
)

from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User

from app.schemas.user import (
    UserCreate,
    UserResponse,
    Token
)

from app.services.auth_service import (
    get_user_by_email,
    create_user,
    authenticate_user
)

from app.core.security import (
    create_access_token,
    decode_access_token
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/token"
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(
    data: UserCreate,
    db: Session = Depends(get_db)
):

    existing_user = get_user_by_email(
        db,
        data.email.lower()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    return create_user(
        db,
        data.email,
        data.password
    )


@router.post(
    "/token",
    response_model=Token
)
def login(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends()
    ],
    db: Session = Depends(get_db)
):

    user = authenticate_user(
        db,
        form_data.username,
        form_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )

    token = create_access_token(
        user.id
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@router.get(
    "/me",
    response_model=UserResponse
)
def get_current_user(
    token: Annotated[
        str,
        Depends(oauth2_scheme)
    ],
    db: Session = Depends(get_db)
):

    user_id = decode_access_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )

    try:
        user_id = int(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user = db.get(
        User,
        user_id
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user