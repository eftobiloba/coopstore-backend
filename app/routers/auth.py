from fastapi import APIRouter, Depends, status, Header
from typing import Any
from app.services.auth import AuthService
from app.db.database import get_db
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from app.schemas.auth import UserOut, Signup

router = APIRouter(tags=["Auth"], prefix="/auth")


@router.post("/signup", status_code=status.HTTP_200_OK, response_model=UserOut)
def signup_user(
    user: Signup,
    db: Any = Depends(get_db)
):
    return AuthService.signup(db, user)


@router.post("/login")
async def user_login(
    user_credentials: OAuth2PasswordRequestForm = Depends(),
    db: Any = Depends(get_db)
):
    return await AuthService.login(db, user_credentials)


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh_access_token(
    refresh_token: str = Header(),
    db: Any = Depends(get_db)
):
    return await AuthService.get_refresh_token(token=refresh_token, db=db)
