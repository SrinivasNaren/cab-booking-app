from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.rating_service import RatingService, RateDriverRequest, RateRiderRequest
from app.core.security import get_current_rider, get_current_driver

router = APIRouter(prefix="/ratings", tags=["Ratings & Reviews"])


# ── Rider Rates Driver ────────────────────────────────────────────────────────
@router.post("/ride/{ride_id}/rate-driver")
def rate_driver(
    ride_id: int,
    data: RateDriverRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_rider)
):
    """
    Rider rates the driver after ride completion.
    - Stars: 1 to 5
    - Comment: optional feedback text
    - Can only rate once per ride
    """
    rating = RatingService.rider_rates_driver(db, ride_id, current_user, data)
    return {
        "message": "Driver rated successfully",
        "stars": rating.rider_to_driver_stars,
        "comment": rating.rider_to_driver_comment,
    }


# ── Driver Rates Rider ────────────────────────────────────────────────────────
@router.post("/ride/{ride_id}/rate-rider")
def rate_rider(
    ride_id: int,
    data: RateRiderRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_driver)
):
    """
    Driver rates the rider after ride completion.
    - Stars: 1 to 5
    - Comment: optional feedback text
    - Can only rate once per ride
    """
    rating = RatingService.driver_rates_rider(db, ride_id, current_user, data)
    return {
        "message": "Rider rated successfully",
        "stars": rating.driver_to_rider_stars,
        "comment": rating.driver_to_rider_comment,
    }


# ── Get Rating for a Ride ─────────────────────────────────────────────────────
@router.get("/ride/{ride_id}")
def get_ride_rating(
    ride_id: int,
    db: Session = Depends(get_db),
):
    """Get rating details for a specific ride."""
    rating = RatingService.get_ride_rating(db, ride_id)
    return {
        "ride_id": ride_id,
        "rider_to_driver": {
            "stars": rating.rider_to_driver_stars,
            "comment": rating.rider_to_driver_comment,
            "submitted": rating.rider_rated,
        },
        "driver_to_rider": {
            "stars": rating.driver_to_rider_stars,
            "comment": rating.driver_to_rider_comment,
            "submitted": rating.driver_rated,
        },
    }


# ── Get Driver's Rating History ───────────────────────────────────────────────
@router.get("/driver/{driver_id}")
def get_driver_ratings(
    driver_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, le=50),
    db: Session = Depends(get_db),
):
    """Get all ratings received by a specific driver."""
    ratings = RatingService.get_driver_ratings(db, driver_id, skip, limit)
    return [
        {
            "ride_id": r.ride_id,
            "stars": r.rider_to_driver_stars,
            "comment": r.rider_to_driver_comment,
            "date": r.created_at,
        }
        for r in ratings
    ]
