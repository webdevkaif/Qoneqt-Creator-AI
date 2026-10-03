from fastapi import APIRouter, HTTPException, Response, Request, status, Depends
from datetime import timedelta
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse, PasswordChange
from app.models.user import User
from app.models.settings import UserSettings
from app.core.security import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, decode_token, get_current_user_id
)
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: UserRegister, response: Response):
    existing = await User.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
    )
    await user.save()

    # Create default settings
    user_settings = UserSettings(user_id=str(user.id))
    await user_settings.save()

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    response.set_cookie(
        "access_token", access_token,
        httponly=True, samesite="lax", secure=False,  # set secure=True in prod
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        "refresh_token", refresh_token,
        httponly=True, samesite="lax", secure=False,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )

    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            is_admin=user.is_admin,
            avatar_url=user.avatar_url,
            created_at=user.created_at,
        )
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, response: Response):
    user = await User.find_one({"email": data.email})
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    response.set_cookie("access_token", access_token, httponly=True, samesite="lax", secure=False,
                        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    response.set_cookie("refresh_token", refresh_token, httponly=True, samesite="lax", secure=False,
                        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400)

    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=str(user.id), email=user.email, username=user.username,
            is_admin=user.is_admin, avatar_url=user.avatar_url, created_at=user.created_at,
        )
    )


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(user_id: str = Depends(get_current_user_id)):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found or session expired")
    return UserResponse(
        id=str(user.id), email=user.email, username=user.username,
        is_admin=user.is_admin, avatar_url=user.avatar_url, created_at=user.created_at,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = await User.get(user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    access_token = create_access_token(user_id)
    response.set_cookie("access_token", access_token, httponly=True, samesite="lax", secure=False,
                        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)

    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=str(user.id), email=user.email, username=user.username,
            is_admin=user.is_admin, avatar_url=user.avatar_url, created_at=user.created_at,
        )
    )


@router.patch("/change-password")
async def change_password(data: PasswordChange, user_id: str = Depends(get_current_user_id)):
    user = await User.get(user_id)
    if not user or not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.hashed_password = hash_password(data.new_password)
    await user.save()
    return {"message": "Password changed successfully"}
