from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.auth import (
    UserRegister, DriverRegister, UserLogin,
    Token, TokenRefresh, UserResponse, UserUpdate
)
from app.services.auth_service import AuthService
from app.core.security import get_current_active_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ─── Register Rider ───────────────────────────────────────────────────────────
@router.post("/register/rider", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_rider(data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new rider account.
    - Role is automatically set to 'rider'
    - Password is encrypted with BCrypt
    """
    user = AuthService.register_rider(db, data)
    return user


# ─── Register Driver ──────────────────────────────────────────────────────────
@router.post("/register/driver", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_driver(data: DriverRegister, db: Session = Depends(get_db)):
    """
    Register a new driver account.
    - Creates both a User and a Driver profile
    - Requires vehicle and license information
    """
    user = AuthService.register_driver(db, data)
    return user


# ─── Login ────────────────────────────────────────────────────────────────────
@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    """
    Login with email and password.
    - Returns JWT access token + refresh token
    - Access token expires in 30 minutes
    - Refresh token expires in 7 days
    """
    return AuthService.login(db, data)


# ─── Refresh Token ────────────────────────────────────────────────────────────
@router.post("/refresh", response_model=Token)
def refresh_token(data: TokenRefresh, db: Session = Depends(get_db)):
    """
    Get a new access token using refresh token.
    Use this when access token expires.
    """
    return AuthService.refresh_token(db, data.refresh_token)


# ─── Get Current User Profile ─────────────────────────────────────────────────
@router.get("/me", response_model=UserResponse)
def get_profile(current_user=Depends(get_current_active_user)):
    """Get the currently logged-in user's profile."""
    return current_user


# ─── Update Profile ───────────────────────────────────────────────────────────
@router.patch("/me", response_model=UserResponse)
def update_profile(
    data: UserUpdate,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update the current user's profile information."""
    if data.full_name:
        current_user.full_name = data.full_name
    if data.phone:
        current_user.phone = data.phone
    if data.profile_picture:
        current_user.profile_picture = data.profile_picture

    db.commit()
    db.refresh(current_user)
    return current_user
