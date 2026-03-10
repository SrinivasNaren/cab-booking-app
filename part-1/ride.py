from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.database import Base


class RideStatus(str, enum.Enum):
    requested = "requested"       # Rider has requested a ride
    accepted = "accepted"         # Driver accepted
    driver_arriving = "driver_arriving"  # Driver on the way to pickup
    ongoing = "ongoing"           # Ride in progress
    completed = "completed"       # Ride finished
    cancelled = "cancelled"       # Rider or driver cancelled


class PaymentMethod(str, enum.Enum):
    cash = "cash"
    card = "card"
    wallet = "wallet"


class Ride(Base):
    __tablename__ = "rides"

    # ─── Primary Key ─────────────────────────────────────────────────────────
    id = Column(Integer, primary_key=True, index=True)

    # ─── Foreign Keys ────────────────────────────────────────────────────────
    rider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)

    # ─── Pickup Location ─────────────────────────────────────────────────────
    pickup_address = Column(String(500), nullable=False)
    pickup_latitude = Column(Float, nullable=False)
    pickup_longitude = Column(Float, nullable=False)

    # ─── Drop Location ───────────────────────────────────────────────────────
    drop_address = Column(String(500), nullable=False)
    drop_latitude = Column(Float, nullable=False)
    drop_longitude = Column(Float, nullable=False)

    # ─── Ride Details ────────────────────────────────────────────────────────
    status = Column(Enum(RideStatus), default=RideStatus.requested, nullable=False)
    distance_km = Column(Float, nullable=True)
    duration_minutes = Column(Integer, nullable=True)

    # ─── Fare ────────────────────────────────────────────────────────────────
    estimated_fare = Column(Float, nullable=True)
    final_fare = Column(Float, nullable=True)
    payment_method = Column(Enum(PaymentMethod), default=PaymentMethod.cash)
    is_paid = Column(Boolean, default=False)

    # ─── Cancellation ────────────────────────────────────────────────────────
    cancelled_by = Column(String(20), nullable=True)   # "rider" or "driver"
    cancel_reason = Column(Text, nullable=True)

    # ─── Timestamps ───────────────────────────────────────────────────────────
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # ─── Relationships ────────────────────────────────────────────────────────
    rider = relationship("User", back_populates="rides_as_rider", foreign_keys=[rider_id])
    driver = relationship("Driver", back_populates="rides", foreign_keys=[driver_id])

    def __repr__(self):
        return f"<Ride id={self.id} status={self.status} rider_id={self.rider_id}>"


# Fix missing import
from sqlalchemy import Boolean
