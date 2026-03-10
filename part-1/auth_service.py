from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User, UserRole
from app.models.driver import Driver, VehicleType
from app.schemas.auth import UserRegister, DriverRegister, UserLogin
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token


class AuthService:

    # ─── Register Rider ───────────────────────────────────────────────────────
    @staticmethod
    def register_rider(db: Session, data: UserRegister) -> User:
        # Check if email already exists
        if db.query(User).filter(User.email == data.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Check if phone already exists
        if data.phone and db.query(User).filter(User.phone == data.phone).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered"
            )

        user = User(
            full_name=data.full_name,
            email=data.email,
            phone=data.phone,
            hashed_password=hash_password(data.password),
            role=UserRole.rider,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    # ─── Register Driver ──────────────────────────────────────────────────────
    @staticmethod
    def register_driver(db: Session, data: DriverRegister) -> User:
        # Check duplicates
        if db.query(User).filter(User.email == data.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")

        if db.query(Driver).filter(Driver.license_number == data.license_number).first():
            raise HTTPException(status_code=400, detail="License number already registered")

        if db.query(Driver).filter(Driver.vehicle_plate == data.vehicle_plate).first():
            raise HTTPException(status_code=400, detail="Vehicle plate already registered")

        # Create user account
        user = User(
            full_name=data.full_name,
            email=data.email,
            phone=data.phone,
            hashed_password=hash_password(data.password),
            role=UserRole.driver,
        )
        db.add(user)
        db.flush()  # Get user.id without committing

        # Create driver profile
        driver = Driver(
            user_id=user.id,
            license_number=data.license_number,
            vehicle_type=VehicleType(data.vehicle_type),
            vehicle_model=data.vehicle_model,
            vehicle_plate=data.vehicle_plate,
            vehicle_color=data.vehicle_color,
        )
        db.add(driver)
        db.commit()
        db.refresh(user)
        return user

    # ─── Login ────────────────────────────────────────────────────────────────
    @staticmethod
    def login(db: Session, data: UserLogin) -> dict:
        user = db.query(User).filter(User.email == data.email).first()

        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account has been suspended"
            )

        token_data = {"sub": str(user.id), "role": user.role}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "role": user.role,
            "user_id": user.id,
        }

    # ─── Refresh Token ────────────────────────────────────────────────────────
    @staticmethod
    def refresh_token(db: Session, refresh_token: str) -> dict:
        payload = decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user = db.query(User).filter(User.id == int(payload["sub"])).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")

        token_data = {"sub": str(user.id), "role": user.role}
        return {
            "access_token": create_access_token(token_data),
            "refresh_token": create_refresh_token(token_data),
            "token_type": "bearer",
            "role": user.role,
            "user_id": user.id,
        }
