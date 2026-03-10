from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.db.database import get_db
from app.schemas.ride import RideResponse
from app.services.driver_service import DriverService
from app.core.security import get_current_driver

router = APIRouter(prefix="/driver", tags=["Driver Dashboard"])


# ─── Request Schemas ──────────────────────────────────────────────────────────
class StatusUpdate(BaseModel):
    status: str  # online / offline


class LocationUpdate(BaseModel):
    latitude: float
    longitude: float


# ─── Go Online / Offline ─────────────────────────────────────────────────────
@router.patch("/status")
def update_status(
    data: StatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_driver)
):
    """
    Toggle driver availability.
    - 'online'  → Driver is available and can receive rides
    - 'offline' → Driver is not available
    Only allowed values: online, offline
    """
    if data.status not in ["online", "offline"]:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Status must be 'online' or 'offline'")

    driver = DriverService.update_status(db, current_user, data.status)
    return {"message": f"Status updated to {driver.status}", "status": driver.status}


# ─── Update Location ──────────────────────────────────────────────────────────
@router.patch("/location")
def update_location(
    data: LocationUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_driver)
):
    """
    Update driver's current GPS location.
    Called periodically by the driver app to keep location fresh.
    """
    driver = DriverService.update_location(db, current_user, data.latitude, data.longitude)
    return {
        "message": "Location updated",
        "latitude": driver.current_latitude,
        "longitude": driver.current_longitude,
    }


# ─── View Available Ride Requests ─────────────────────────────────────────────
@router.get("/rides/available", response_model=List[RideResponse])
def get_available_rides(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_driver)
):
    """
    View all pending ride requests.
    - Driver must be online to see rides
    - Returns rides that are not yet assigned to any driver
    """
    return DriverService.get_available_rides(db, current_user)


# ─── Accept a Ride ────────────────────────────────────────────────────────────
@router.post("/rides/{ride_id}/accept", response_model=RideResponse)
def accept_ride(
    ride_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_driver)
):
    """
    Accept a ride request.
    - Driver must not already be on another ride
    - Ride must still be in 'requested' status
    - Driver status will change to 'on_ride'
    """
    return DriverService.accept_ride(db, current_user, ride_id)


# ─── Reject a Ride ────────────────────────────────────────────────────────────
@router.post("/rides/{ride_id}/reject")
def reject_ride(
    ride_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_driver)
):
    """
    Reject a ride request.
    - Ride stays in 'requested' pool for other drivers
    """
    return DriverService.reject_ride(db, current_user, ride_id)


# ─── Start Ride ───────────────────────────────────────────────────────────────
@router.post("/rides/{ride_id}/start", response_model=RideResponse)
def start_ride(
    ride_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_driver)
):
    """
    Mark the ride as started.
    - Driver must have accepted the ride first
    - Status changes from 'accepted' to 'ongoing'
    """
    return DriverService.start_ride(db, current_user, ride_id)


# ─── Complete Ride ────────────────────────────────────────────────────────────
@router.post("/rides/{ride_id}/complete", response_model=RideResponse)
def complete_ride(
    ride_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_driver)
):
    """
    Mark the ride as completed.
    - Status changes from 'ongoing' to 'completed'
    - Final fare is calculated
    - Driver earnings are updated
    - Driver status returns to 'online'
    """
    return DriverService.complete_ride(db, current_user, ride_id)


# ─── Driver Ride History ──────────────────────────────────────────────────────
@router.get("/rides/history", response_model=List[RideResponse])
def ride_history(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, le=50),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_driver)
):
    """
    View driver's past completed rides.
    Paginated — use skip and limit.
    """
    return DriverService.get_ride_history(db, current_user, skip, limit)


# ─── Driver Earnings ──────────────────────────────────────────────────────────
@router.get("/earnings")
def get_earnings(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_driver)
):
    """
    View earnings summary.
    Returns: total earnings, total rides, average rating, completed ride count.
    """
    return DriverService.get_earnings(db, current_user)
