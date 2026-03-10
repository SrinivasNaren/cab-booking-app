from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.schemas.ride import (
    BookRideRequest, FareEstimateRequest, FareEstimateResponse,
    CancelRideRequest, RideResponse
)
from app.services.ride_service import RideService
from app.core.security import get_current_rider, get_current_active_user

router = APIRouter(prefix="/rides", tags=["Ride Booking"])


# ─── Estimate Fare (No Auth Required) ────────────────────────────────────────
@router.post("/estimate", response_model=FareEstimateResponse)
def estimate_fare(data: FareEstimateRequest):
    """
    Get fare estimate before booking a ride.
    No authentication required.
    Returns: distance, duration, estimated fare, and breakdown.
    """
    return RideService.estimate_fare(data)


# ─── Book a Ride ──────────────────────────────────────────────────────────────
@router.post("/book", response_model=RideResponse, status_code=201)
def book_ride(
    data: BookRideRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_rider)
):
    """
    Book a new ride.
    - Only riders can book
    - Cannot book if already have an active ride
    - Fare is auto-calculated based on distance
    """
    return RideService.book_ride(db, current_user, data)


# ─── Get Ride by ID ───────────────────────────────────────────────────────────
@router.get("/{ride_id}", response_model=RideResponse)
def get_ride(
    ride_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """
    Get details of a specific ride.
    - Rider can only see their own rides
    - Driver can only see rides assigned to them
    - Admin can see all rides
    """
    return RideService.get_ride(db, ride_id, current_user)


# ─── Cancel a Ride ────────────────────────────────────────────────────────────
@router.post("/{ride_id}/cancel", response_model=RideResponse)
def cancel_ride(
    ride_id: int,
    data: CancelRideRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_rider)
):
    """
    Cancel a ride.
    - Only the rider who booked can cancel
    - Cannot cancel completed or already cancelled rides
    """
    return RideService.cancel_ride(db, ride_id, current_user, data)


# ─── Rider's Ride History ─────────────────────────────────────────────────────
@router.get("/history/me", response_model=List[RideResponse])
def my_ride_history(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, le=50),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_rider)
):
    """
    Get the current rider's ride history.
    - Paginated: use skip and limit params
    - Sorted by most recent first
    """
    return RideService.get_rider_history(db, current_user.id, skip, limit)
