from fastapi import APIRouter, Depends, Request, Header
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.services.payment_service import PaymentService
from app.core.security import get_current_rider, get_current_admin

router = APIRouter(prefix="/payments", tags=["Payments (Stripe)"])


# ── Create Payment Intent ─────────────────────────────────────────────────────
@router.post("/create-intent/{ride_id}")
def create_payment_intent(
    ride_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_rider)
):
    """
    Create a Stripe PaymentIntent for a completed ride.

    Flow:
    1. Call this endpoint after ride is completed
    2. Get back client_secret
    3. Use client_secret in frontend with Stripe.js to confirm payment
    4. Stripe calls our webhook after payment succeeds
    """
    return PaymentService.create_payment_intent(db, ride_id, current_user.id)


# ── Stripe Webhook ────────────────────────────────────────────────────────────
@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Stripe calls this endpoint automatically after payment events.
    DO NOT call this manually.

    Events handled:
    - payment_intent.succeeded → marks payment as completed, ride as paid
    - payment_intent.payment_failed → marks payment as failed
    """
    payload = await request.body()
    return PaymentService.handle_webhook(db, payload, stripe_signature)


# ── Get Payment Status ────────────────────────────────────────────────────────
@router.get("/status/{ride_id}")
def get_payment_status(
    ride_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_rider)
):
    """Check the current payment status for a ride."""
    payment = PaymentService.get_payment_status(db, ride_id, current_user.id)
    return {
        "payment_id": payment.id,
        "ride_id": ride_id,
        "amount": payment.amount,
        "status": payment.status,
        "currency": payment.currency,
        "completed_at": payment.completed_at,
    }


# ── Refund (Admin Only) ───────────────────────────────────────────────────────
@router.post("/refund/{ride_id}")
def refund_payment(
    ride_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):
    """
    Issue a full refund for a ride payment. Admin only.
    """
    return PaymentService.refund_payment(db, ride_id)
