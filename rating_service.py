from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional

from app.models.rating import Rating
from app.models.ride import Ride, RideStatus
from app.models.driver import Driver
from app.models.user import User


# ── Schemas ───────────────────────────────────────────────────────────────────
class RateDriverRequest(BaseModel):
    stars: float
    comment: Optional[str] = None

class RateRiderRequest(BaseModel):
    stars: float
    comment: Optional[str] = None


class RatingService:

    # ── Create Rating Entry (after ride completes) ────────────────────────────
    @staticmethod
    def create_rating_entry(db: Session, ride_id: int):
        """
        Automatically called when a ride is completed.
        Creates an empty rating record for both parties to fill.
        """
        ride = db.query(Ride).filter(Ride.id == ride_id).first()
        if not ride or not ride.driver_id:
            return

        existing = db.query(Rating).filter(Rating.ride_id == ride_id).first()
        if existing:
            return

        rating = Rating(
            ride_id=ride_id,
            rider_id=ride.rider_id,
            driver_id=ride.driver_id,
        )
        db.add(rating)
        db.commit()

    # ── Rider Rates Driver ────────────────────────────────────────────────────
    @staticmethod
    def rider_rates_driver(db: Session, ride_id: int, rider: User, data: RateDriverRequest) -> Rating:
        if not (1 <= data.stars <= 5):
            raise HTTPException(status_code=400, detail="Stars must be between 1 and 5")

        rating = db.query(Rating).filter(Rating.ride_id == ride_id).first()
        if not rating:
            raise HTTPException(status_code=404, detail="Rating record not found")

        if rating.rider_id != rider.id:
            raise HTTPException(status_code=403, detail="Access denied")

        if rating.rider_rated:
            raise HTTPException(status_code=400, detail="You have already rated this ride")

        rating.rider_to_driver_stars = data.stars
        rating.rider_to_driver_comment = data.comment
        rating.rider_rated = True
        db.commit()

        # ── Update driver's average rating ────────────────────────────────────
        RatingService._update_driver_avg_rating(db, rating.driver_id)

        db.refresh(rating)
        return rating

    # ── Driver Rates Rider ────────────────────────────────────────────────────
    @staticmethod
    def driver_rates_rider(db: Session, ride_id: int, driver_user: User, data: RateRiderRequest) -> Rating:
        if not (1 <= data.stars <= 5):
            raise HTTPException(status_code=400, detail="Stars must be between 1 and 5")

        driver = db.query(Driver).filter(Driver.user_id == driver_user.id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")

        rating = db.query(Rating).filter(Rating.ride_id == ride_id).first()
        if not rating:
            raise HTTPException(status_code=404, detail="Rating record not found")

        if rating.driver_id != driver.id:
            raise HTTPException(status_code=403, detail="Access denied")

        if rating.driver_rated:
            raise HTTPException(status_code=400, detail="You have already rated this ride")

        rating.driver_to_rider_stars = data.stars
        rating.driver_to_rider_comment = data.comment
        rating.driver_rated = True
        db.commit()

        # ── Update rider's average rating ─────────────────────────────────────
        RatingService._update_rider_avg_rating(db, rating.rider_id)

        db.refresh(rating)
        return rating

    # ── Recalculate Driver Average Rating ────────────────────────────────────
    @staticmethod
    def _update_driver_avg_rating(db: Session, driver_id: int):
        result = db.query(
            func.avg(Rating.rider_to_driver_stars),
            func.count(Rating.id)
        ).filter(
            Rating.driver_id == driver_id,
            Rating.rider_to_driver_stars.isnot(None)
        ).first()

        avg, count = result
        driver = db.query(Driver).filter(Driver.id == driver_id).first()
        if driver:
            driver.user.average_rating = round(float(avg or 0), 2)
            driver.user.total_ratings = count or 0
            db.commit()

    # ── Recalculate Rider Average Rating ─────────────────────────────────────
    @staticmethod
    def _update_rider_avg_rating(db: Session, rider_id: int):
        result = db.query(
            func.avg(Rating.driver_to_rider_stars),
            func.count(Rating.id)
        ).filter(
            Rating.rider_id == rider_id,
            Rating.driver_to_rider_stars.isnot(None)
        ).first()

        avg, count = result
        rider = db.query(User).filter(User.id == rider_id).first()
        if rider:
            rider.average_rating = round(float(avg or 0), 2)
            rider.total_ratings = count or 0
            db.commit()

    # ── Get Rating for a Ride ─────────────────────────────────────────────────
    @staticmethod
    def get_ride_rating(db: Session, ride_id: int) -> Rating:
        rating = db.query(Rating).filter(Rating.ride_id == ride_id).first()
        if not rating:
            raise HTTPException(status_code=404, detail="Rating not found for this ride")
        return rating

    # ── Get Driver's All Ratings ──────────────────────────────────────────────
    @staticmethod
    def get_driver_ratings(db: Session, driver_id: int, skip: int = 0, limit: int = 10):
        return (
            db.query(Rating)
            .filter(Rating.driver_id == driver_id, Rating.rider_to_driver_stars.isnot(None))
            .order_by(Rating.created_at.desc())
            .offset(skip).limit(limit).all()
        )
