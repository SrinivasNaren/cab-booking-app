from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime

from app.models.ride import Ride, RideStatus
from app.models.driver import Driver, DriverStatus
from app.models.user import User


class DriverService:

    # ─── Go Online / Offline ─────────────────────────────────────────────────
    @staticmethod
    def update_status(db: Session, user: User, new_status: str) -> Driver:
        driver = db.query(Driver).filter(Driver.user_id == user.id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver profile not found")

        driver.status = DriverStatus(new_status)
        db.commit()
        db.refresh(driver)
        return driver

    # ─── Update Driver Location ───────────────────────────────────────────────
    @staticmethod
    def update_location(db: Session, user: User, latitude: float, longitude: float) -> Driver:
        driver = db.query(Driver).filter(Driver.user_id == user.id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver profile not found")

        driver.current_latitude = latitude
        driver.current_longitude = longitude
        db.commit()
        db.refresh(driver)
        return driver

    # ─── Get Available Ride Requests ──────────────────────────────────────────
    @staticmethod
    def get_available_rides(db: Session, user: User):
        """Get all pending ride requests for the driver to see."""
        driver = db.query(Driver).filter(Driver.user_id == user.id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver profile not found")

        if driver.status != DriverStatus.online:
            raise HTTPException(
                status_code=400,
                detail="You must be online to see ride requests"
            )

        # Return all requested (unassigned) rides
        return (
            db.query(Ride)
            .filter(Ride.status == RideStatus.requested, Ride.driver_id == None)
            .order_by(Ride.created_at.asc())
            .all()
        )

    # ─── Accept a Ride ────────────────────────────────────────────────────────
    @staticmethod
    def accept_ride(db: Session, user: User, ride_id: int) -> Ride:
        driver = db.query(Driver).filter(Driver.user_id == user.id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver profile not found")

        # Check driver is not on another ride
        if driver.status == DriverStatus.on_ride:
            raise HTTPException(status_code=400, detail="You are already on a ride")

        ride = db.query(Ride).filter(Ride.id == ride_id).first()
        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")

        if ride.status != RideStatus.requested:
            raise HTTPException(status_code=400, detail="Ride is no longer available")

        # Assign ride to driver
        ride.driver_id = driver.id
        ride.status = RideStatus.accepted
        ride.accepted_at = datetime.utcnow()

        # Update driver status
        driver.status = DriverStatus.on_ride

        db.commit()
        db.refresh(ride)
        return ride

    # ─── Reject a Ride ────────────────────────────────────────────────────────
    @staticmethod
    def reject_ride(db: Session, user: User, ride_id: int) -> dict:
        """Driver rejects a ride — ride goes back to requested pool."""
        ride = db.query(Ride).filter(Ride.id == ride_id).first()
        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")

        if ride.status != RideStatus.requested:
            raise HTTPException(status_code=400, detail="Ride is not in requested state")

        return {"message": "Ride rejected", "ride_id": ride_id}

    # ─── Start Ride ───────────────────────────────────────────────────────────
    @staticmethod
    def start_ride(db: Session, user: User, ride_id: int) -> Ride:
        driver = db.query(Driver).filter(Driver.user_id == user.id).first()
        ride = db.query(Ride).filter(Ride.id == ride_id, Ride.driver_id == driver.id).first()

        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found or not assigned to you")

        if ride.status != RideStatus.accepted:
            raise HTTPException(status_code=400, detail="Ride must be accepted before starting")

        ride.status = RideStatus.ongoing
        ride.started_at = datetime.utcnow()
        db.commit()
        db.refresh(ride)
        return ride

    # ─── Complete Ride ────────────────────────────────────────────────────────
    @staticmethod
    def complete_ride(db: Session, user: User, ride_id: int) -> Ride:
        driver = db.query(Driver).filter(Driver.user_id == user.id).first()
        ride = db.query(Ride).filter(Ride.id == ride_id, Ride.driver_id == driver.id).first()

        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")

        if ride.status != RideStatus.ongoing:
            raise HTTPException(status_code=400, detail="Ride is not ongoing")

        ride.status = RideStatus.completed
        ride.completed_at = datetime.utcnow()
        ride.final_fare = ride.estimated_fare  # Will be recalculated with real distance later

        # Update driver stats
        driver.status = DriverStatus.online  # Back to available
        driver.total_rides += 1
        driver.total_earnings += ride.final_fare

        db.commit()
        db.refresh(ride)
        return ride

    # ─── Driver Ride History ──────────────────────────────────────────────────
    @staticmethod
    def get_ride_history(db: Session, user: User, skip: int = 0, limit: int = 10):
        driver = db.query(Driver).filter(Driver.user_id == user.id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver profile not found")

        return (
            db.query(Ride)
            .filter(Ride.driver_id == driver.id)
            .order_by(Ride.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    # ─── Driver Earnings ──────────────────────────────────────────────────────
    @staticmethod
    def get_earnings(db: Session, user: User) -> dict:
        driver = db.query(Driver).filter(Driver.user_id == user.id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver profile not found")

        completed_rides = (
            db.query(Ride)
            .filter(Ride.driver_id == driver.id, Ride.status == RideStatus.completed)
            .all()
        )

        return {
            "total_earnings": driver.total_earnings,
            "total_rides": driver.total_rides,
            "average_rating": user.average_rating,
            "completed_rides_count": len(completed_rides),
        }
