from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.database import Base


class UserRole(str, enum.Enum):
    rider = "rider"
    driver = "driver"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    # ─── Primary Key ─────────────────────────────────────────────────────────
    id = Column(Integer, primary_key=True, index=True)

    # ─── Personal Info ────────────────────────────────────────────────────────
    full_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), unique=True, nullable=True)
    profile_picture = Column(String(500), nullable=True)

    # ─── Auth ─────────────────────────────────────────────────────────────────
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.rider, nullable=False)

    # ─── Status ───────────────────────────────────────────────────────────────
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # ─── Ratings ──────────────────────────────────────────────────────────────
    average_rating = Column(Float, default=0.0)
    total_ratings = Column(Integer, default=0)

    # ─── Timestamps ───────────────────────────────────────────────────────────
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # ─── Relationships ────────────────────────────────────────────────────────
    rides_as_rider = relationship(
        "Ride", back_populates="rider", foreign_keys="Ride.rider_id"
    )
    driver_profile = relationship(
        "Driver", back_populates="user", uselist=False
    )

    def __repr__(self):
        return f"<User id={self.id} email={self.email} role={self.role}>"
