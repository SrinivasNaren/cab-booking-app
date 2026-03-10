import math
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.ride import Ride, RideStatus, PaymentMethod
from app.models.driver import Driver, DriverStatus
from app.models.user import User
from app.schemas.ride import BookRideRequest, FareEstimateRequest, CancelRideRequest


# ─── Fare Configuration ───────────────────────────────────────────────────────
FARE_CONFIG = {
    "bike":  {"base": 15,  "per_km": 7,   "per_min": 0.5},
    "auto":  {"base": 25,  "per_km": 12,  "per_min": 1.0},
    "mini":  {"base": 40,  "per_km": 15,  "per_min": 1.5},
    "sedan": {"base": 60,  "per_km": 18,  "per_min": 2.0},
    "suv":   {"base": 100, "per_km": 25,  "per_min": 2.5},
}


class RideService:

    # ─── Distance Calculation (Haversine Formula) ─────────────────────────────
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two coordinates in kilometers.
        Uses the Haversine formula.
        """
        R = 6371  # Earth's radius in km
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        return round(R * c, 2)

    # ─── Fare Calculation ─────────────────────────────────────────────────────
    @staticmethod
    def calculate_fare(distance_km: float, vehicle_type: str) -> dict:
        """Calculate fare breakdown for a ride."""
        config = FARE_CONFIG.get(vehicle_type, FARE_CONFIG["sedan"])
        duration_minutes = int(distance_km * 3)  # Rough estimate: 3 min per km

        base_fare = config["base"]
        distance_charge = round(distance_km * config["per_km"], 2)
        time_charge = round(duration_minutes * config["per_min"], 2)
        total_fare = round(base_fare + distance_charge + time_charge, 2)

        return {
            "base_fare": base_fare,
            "distance_charge": distance_charge,
            "time_charge": time_charge,
            "total_fare": total_fare,
            "duration_minutes": duration_minutes,
        }

    # ─── Estimate Fare (Before Booking) ──────────────────────────────────────
    @staticmethod
    def estimate_fare(data: FareEstimateRequest) -> dict:
        distance = RideService.calculate_distance(
            data.pickup_latitude, data.pickup_longitude,
            data.drop_latitude, data.drop_longitude,
        )
        fare_breakdown = RideService.calculate_fare(distance, data.vehicle_type)

        return {
            "distance_km": distance,
            "duration_minutes": fare_breakdown["duration_minutes"],
            "estimated_fare": fare_breakdown["total_fare"],
            "vehicle_type": data.vehicle_type,
            "breakdown": {
                "base_fare": fare_breakdown["base_fare"],
                "distance_charge": fare_breakdown["distance_charge"],
                "time_charge": fare_breakdown["time_charge"],
            },
        }

    # ─── Book a Ride ──────────────────────────────────────────────────────────
    @staticmethod
    def book_ride(db: Session, rider: User, data: BookRideRequest) -> Ride:
        # Check rider doesn't already have an active ride
        active_ride = db.query(Ride).filter(
            Ride.rider_id == rider.id,
            Ride.status.in_([RideStatus.requested, RideStatus.accepted, RideStatus.ongoing])
        ).first()

        if active_ride:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already have an active ride"
            )

        # Calculate distance and fare
        distance = RideService.calculate_distance(
            data.pickup_latitude, data.pickup_longitude,
            data.drop_latitude, data.drop_longitude
        )
        fare_data = RideService.calculate_fare(distance, data.vehicle_type)

        # Create the ride
        ride = Ride(
            rider_id=rider.id,
            pickup_address=data.pickup_address,
            pickup_latitude=data.pickup_latitude,
            pickup_longitude=data.pickup_longitude,
            drop_address=data.drop_address,
            drop_latitude=data.drop_latitude,
            drop_longitude=data.drop_longitude,
            distance_km=distance,
            duration_minutes=fare_data["duration_minutes"],
            estimated_fare=fare_data["total_fare"],
            payment_method=PaymentMethod(data.payment_method),
            status=RideStatus.requested,
        )
        db.add(ride)
        db.commit()
        db.refresh(ride)
        return ride

    # ─── Get Ride by ID ───────────────────────────────────────────────────────
    @staticmethod
    def get_ride(db: Session, ride_id: int, user: User) -> Ride:
        ride = db.query(Ride).filter(Ride.id == ride_id).first()
        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")

        # Only rider, assigned driver, or admin can view ride
        driver_profile = user.driver_profile
        driver_id = driver_profile.id if driver_profile else None

        if user.role != "admin" and ride.rider_id != user.id and ride.driver_id != driver_id:
            raise HTTPException(status_code=403, detail="Access denied")

        return ride

    # ─── Cancel Ride ─────────────────────────────────────────────────────────
    @staticmethod
    def cancel_ride(db: Session, ride_id: int, user: User, data: CancelRideRequest) -> Ride:
        ride = db.query(Ride).filter(Ride.id == ride_id).first()
        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")

        if ride.status in [RideStatus.completed, RideStatus.cancelled]:
            raise HTTPException(status_code=400, detail="Ride already completed or cancelled")

        if ride.rider_id != user.id:
            raise HTTPException(status_code=403, detail="You can only cancel your own rides")

        ride.status = RideStatus.cancelled
        ride.cancelled_by = "rider"
        ride.cancel_reason = data.reason
        db.commit()
        db.refresh(ride)
        return ride

    # ─── Get Rider's Ride History ─────────────────────────────────────────────
    @staticmethod
    def get_rider_history(db: Session, rider_id: int, skip: int = 0, limit: int = 10):
        return (
            db.query(Ride)
            .filter(Ride.rider_id == rider_id)
            .order_by(Ride.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
