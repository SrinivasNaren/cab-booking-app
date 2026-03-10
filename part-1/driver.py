from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.database import Base


class DriverStatus(str, enum.Enum):
    online = "online"       # Available for rides
    offline = "offline"     # Not available
    on_ride = "on_ride"     # Currently doing a ride


class VehicleType(str, enum.Enum):
    bike = "bike"
    auto = "auto"
    mini = "mini"
    sedan = "sedan"
    suv = "suv"


class Driver(Base):
    __tablename__ = "drivers"

    # ─── Primary Key ─────────────────────────────────────────────────────────
    id = Column(Integer, primary_key=True, index=True)

    # ─── Foreign Key to User ─────────────────────────────────────────────────
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # ─── License & Vehicle Info ───────────────────────────────────────────────
    license_number = Column(String(50), unique=True, nullable=False)
    vehicle_type = Column(Enum(VehicleType), nullable=False)
    vehicle_model = Column(String(100), nullable=False)
    vehicle_plate = Column(String(20), unique=True, nullable=False)
    vehicle_color = Column(String(50), nullable=True)

    # ─── Status & Location ────────────────────────────────────────────────────
    status = Column(Enum(DriverStatus), default=DriverStatus.offline)
    current_latitude = Column(Float, nullable=True)
    current_longitude = Column(Float, nullable=True)

    # ─── Financials ───────────────────────────────────────────────────────────
    total_earnings = Column(Float, default=0.0)
    total_rides = Column(Integer, default=0)

    # ─── Verification ────────────────────────────────────────────────────────
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # ─── Timestamps ───────────────────────────────────────────────────────────
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # ─── Relationships ────────────────────────────────────────────────────────
    user = relationship("User", back_populates="driver_profile")
    rides = relationship("Ride", back_populates="driver", foreign_keys="Ride.driver_id")

    def __repr__(self):
        return f"<Driver id={self.id} plate={self.vehicle_plate} status={self.status}>"
