from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from app.db.database import get_db
from app.models.ride import Ride, RideStatus
from app.models.payment import Payment
from app.services.pdf_service import PDFService
from app.services.email_service import EmailService
from app.core.security import get_current_active_user

router = APIRouter(prefix="/receipts", tags=["Receipts & History"])

RECEIPTS_DIR = "receipts"


def build_ride_data(ride: Ride, payment: Payment) -> dict:
    """Helper to assemble ride_data dict for PDF/email."""
    fare_breakdown = {
        "base_fare": 0,
        "distance_charge": 0,
        "time_charge": 0,
    }
    # Rough breakdown from final fare
    if ride.final_fare:
        fare_breakdown["base_fare"] = 50
        fare_breakdown["distance_charge"] = round((ride.final_fare - 50) * 0.7, 2)
        fare_breakdown["time_charge"] = round((ride.final_fare - 50) * 0.3, 2)

    driver_name = "N/A"
    vehicle_model = "N/A"
    vehicle_plate = "N/A"

    if ride.driver:
        driver_name = ride.driver.user.full_name
        vehicle_model = ride.driver.vehicle_model
        vehicle_plate = ride.driver.vehicle_plate

    return {
        "ride_id": ride.id,
        "rider_name": ride.rider.full_name,
        "rider_email": ride.rider.email,
        "driver_name": driver_name,
        "vehicle_model": vehicle_model,
        "vehicle_plate": vehicle_plate,
        "pickup_address": ride.pickup_address,
        "drop_address": ride.drop_address,
        "distance_km": ride.distance_km or 0,
        "duration_minutes": ride.duration_minutes or 0,
        "fare_breakdown": fare_breakdown,
        "final_fare": ride.final_fare or 0,
        "payment_method": ride.payment_method,
        "payment_status": payment.status if payment else "pending",
        "ride_date": ride.completed_at.strftime("%d %B %Y") if ride.completed_at else "N/A",
    }


# ── Download PDF Receipt ──────────────────────────────────────────────────────
@router.get("/download/{ride_id}")
def download_receipt(
    ride_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """
    Generate and download a PDF receipt for a completed ride.
    - Rider can download their own receipts
    - Admin can download any receipt
    """
    ride = db.query(Ride).filter(Ride.id == ride_id).first()
    if not ride:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Ride not found")

    if ride.status != RideStatus.completed:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Receipt only available for completed rides")

    if current_user.role != "admin" and ride.rider_id != current_user.id:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Access denied")

    payment = db.query(Payment).filter(Payment.ride_id == ride_id).first()
    ride_data = build_ride_data(ride, payment)

    pdf_path = f"{RECEIPTS_DIR}/receipt_ride_{ride_id}.pdf"
    PDFService.generate_receipt(ride_data, pdf_path)

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"receipt_ride_{ride_id}.pdf"
    )


# ── Email Receipt ─────────────────────────────────────────────────────────────
@router.post("/email/{ride_id}")
def email_receipt(
    ride_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """
    Generate PDF receipt and email it to the rider.
    Runs in the background so the API response is instant.
    """
    ride = db.query(Ride).filter(Ride.id == ride_id).first()
    if not ride:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Ride not found")

    if current_user.role != "admin" and ride.rider_id != current_user.id:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Access denied")

    payment = db.query(Payment).filter(Payment.ride_id == ride_id).first()
    ride_data = build_ride_data(ride, payment)

    def send_email_task():
        pdf_path = f"{RECEIPTS_DIR}/receipt_ride_{ride_id}.pdf"
        PDFService.generate_receipt(ride_data, pdf_path)
        EmailService.send_receipt_email(
            to_email=ride.rider.email,
            rider_name=ride.rider.full_name,
            ride_data=ride_data,
            pdf_path=pdf_path
        )

    background_tasks.add_task(send_email_task)
    return {"message": f"Receipt will be emailed to {ride.rider.email}"}
