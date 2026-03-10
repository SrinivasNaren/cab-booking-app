from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException

from app.models.user import User, UserRole
from app.models.driver import Driver, DriverStatus
from app.models.ride import Ride, RideStatus
from app.models.payment import Payment, PaymentStatus


class AdminService:

    # ── Dashboard Stats ───────────────────────────────────────────────────────
    @staticmethod
    def get_dashboard_stats(db: Session) -> dict:
        """Platform-wide statistics for admin overview."""
        total_users = db.query(User).filter(User.role == UserRole.rider).count()
        total_drivers = db.query(User).filter(User.role == UserRole.driver).count()
        total_rides = db.query(Ride).count()
        completed_rides = db.query(Ride).filter(Ride.status == RideStatus.completed).count()
        active_rides = db.query(Ride).filter(
            Ride.status.in_([RideStatus.accepted, RideStatus.ongoing])
        ).count()
        online_drivers = db.query(Driver).filter(
            Driver.status.in_([DriverStatus.online, DriverStatus.on_ride])
        ).count()

        total_revenue = db.query(func.sum(Payment.amount)).filter(
            Payment.status == PaymentStatus.completed
        ).scalar() or 0

        return {
            "total_riders": total_users,
            "total_drivers": total_drivers,
            "total_rides": total_rides,
            "completed_rides": completed_rides,
            "active_rides": active_rides,
            "online_drivers": online_drivers,
            "total_revenue": round(total_revenue, 2),
        }

    # ── Get All Users ─────────────────────────────────────────────────────────
    @staticmethod
    def get_all_users(db: Session, role: str = None, skip: int = 0, limit: int = 20):
        query = db.query(User)
        if role:
            query = query.filter(User.role == role)
        return query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()

    # ── Suspend / Unsuspend Account ───────────────────────────────────────────
    @staticmethod
    def toggle_user_status(db: Session, user_id: int) -> dict:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.is_active = not user.is_active
        db.commit()

        action = "activated" if user.is_active else "suspended"
        return {"message": f"User {action}", "user_id": user_id, "is_active": user.is_active}

    # ── Get All Rides ─────────────────────────────────────────────────────────
    @staticmethod
    def get_all_rides(db: Session, status: str = None, skip: int = 0, limit: int = 20):
        query = db.query(Ride)
        if status:
            query = query.filter(Ride.status == status)
        return query.order_by(Ride.created_at.desc()).offset(skip).limit(limit).all()

    # ── Get All Transactions ──────────────────────────────────────────────────
    @staticmethod
    def get_all_payments(db: Session, skip: int = 0, limit: int = 20):
        return (
            db.query(Payment)
            .order_by(Payment.created_at.desc())
            .offset(skip).limit(limit).all()
        )

    # ── Verify a Driver ───────────────────────────────────────────────────────
    @staticmethod
    def verify_driver(db: Session, driver_user_id: int) -> dict:
        driver = db.query(Driver).filter(Driver.user_id == driver_user_id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")

        driver.is_verified = True
        db.commit()
        return {"message": "Driver verified successfully", "driver_id": driver.id}

    # ── Revenue Report ────────────────────────────────────────────────────────
    @staticmethod
    def get_revenue_report(db: Session) -> dict:
        """Breakdown of revenue by payment method."""
        completed_payments = db.query(Payment).filter(
            Payment.status == PaymentStatus.completed
        ).all()

        total = sum(p.amount for p in completed_payments)
        by_method = {}
        for p in completed_payments:
            ride = db.query(Ride).filter(Ride.id == p.ride_id).first()
            method = ride.payment_method if ride else "unknown"
            by_method[method] = by_method.get(method, 0) + p.amount

        return {
            "total_revenue": round(total, 2),
            "total_transactions": len(completed_payments),
            "by_payment_method": {k: round(v, 2) for k, v in by_method.items()},
        }
