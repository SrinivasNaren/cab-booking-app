from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.services.admin_service import AdminService
from app.core.security import get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


# ── Dashboard Stats ───────────────────────────────────────────────────────────
@router.get("/stats")
def dashboard_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):
    """
    Platform-wide overview.
    Returns: total riders, drivers, rides, active rides, online drivers, revenue.
    """
    return AdminService.get_dashboard_stats(db)


# ── Get All Users ─────────────────────────────────────────────────────────────
@router.get("/users")
def get_all_users(
    role: Optional[str] = Query(None, example="rider"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):
    """
    List all users. Filter by role: rider, driver, admin.
    """
    return AdminService.get_all_users(db, role, skip, limit)


# ── Suspend / Activate User ───────────────────────────────────────────────────
@router.patch("/users/{user_id}/toggle-status")
def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):
    """
    Suspend or re-activate a user account.
    Suspended users cannot log in or use the app.
    """
    return AdminService.toggle_user_status(db, user_id)


# ── Verify Driver ─────────────────────────────────────────────────────────────
@router.patch("/drivers/{user_id}/verify")
def verify_driver(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):
    """
    Mark a driver as verified after document review.
    Unverified drivers should not be allowed to accept rides in production.
    """
    return AdminService.verify_driver(db, user_id)


# ── All Rides ─────────────────────────────────────────────────────────────────
@router.get("/rides")
def get_all_rides(
    status: Optional[str] = Query(None, example="completed"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):
    """
    View all rides on the platform.
    Filter by status: requested, accepted, ongoing, completed, cancelled.
    """
    return AdminService.get_all_rides(db, status, skip, limit)


# ── All Payments ──────────────────────────────────────────────────────────────
@router.get("/payments")
def get_all_payments(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):
    """View all payment transactions on the platform."""
    return AdminService.get_all_payments(db, skip, limit)


# ── Revenue Report ────────────────────────────────────────────────────────────
@router.get("/revenue")
def revenue_report(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):
    """
    Revenue breakdown by payment method.
    Returns: total revenue, transaction count, breakdown by cash/card/wallet.
    """
    return AdminService.get_revenue_report(db)
