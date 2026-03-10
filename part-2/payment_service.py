import stripe
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.core.config import settings
from app.models.payment import Payment, PaymentStatus
from app.models.ride import Ride, RideStatus

# ── Initialize Stripe ─────────────────────────────────────────────────────────
stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentService:

    # ── Create Payment Intent ─────────────────────────────────────────────────
    @staticmethod
    def create_payment_intent(db: Session, ride_id: int, rider_id: int) -> dict:
        """
        Step 1: Create a Stripe PaymentIntent for a completed ride.
        Returns client_secret to the frontend to complete payment.
        """
        ride = db.query(Ride).filter(Ride.id == ride_id).first()
        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")

        if ride.status != RideStatus.completed:
            raise HTTPException(status_code=400, detail="Ride must be completed before payment")

        if ride.rider_id != rider_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Check if payment already exists
        existing = db.query(Payment).filter(Payment.ride_id == ride_id).first()
        if existing and existing.status == PaymentStatus.completed:
            raise HTTPException(status_code=400, detail="Ride already paid")

        amount_paise = int(ride.final_fare * 100)  # Convert ₹ to paise (Stripe uses smallest unit)

        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_paise,
                currency="inr",
                metadata={
                    "ride_id": str(ride_id),
                    "rider_id": str(rider_id),
                },
                description=f"Cab ride #{ride_id} — {ride.pickup_address} to {ride.drop_address}",
            )

            # Save payment record
            payment = existing or Payment(ride_id=ride_id, rider_id=rider_id, amount=ride.final_fare)
            payment.stripe_payment_intent_id = intent.id
            payment.stripe_client_secret = intent.client_secret
            payment.status = PaymentStatus.processing

            if not existing:
                db.add(payment)
            db.commit()
            db.refresh(payment)

            return {
                "payment_id": payment.id,
                "client_secret": intent.client_secret,
                "amount": ride.final_fare,
                "currency": "inr",
                "ride_id": ride_id,
            }

        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")

    # ── Handle Stripe Webhook ─────────────────────────────────────────────────
    @staticmethod
    def handle_webhook(db: Session, payload: bytes, sig_header: str) -> dict:
        """
        Step 2: Stripe calls this endpoint after payment is processed.
        Verifies the webhook signature and updates payment status in DB.
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

        # ── Payment Succeeded ─────────────────────────────────────────────────
        if event["type"] == "payment_intent.succeeded":
            intent = event["data"]["object"]
            payment = db.query(Payment).filter(
                Payment.stripe_payment_intent_id == intent["id"]
            ).first()

            if payment:
                payment.status = PaymentStatus.completed
                payment.completed_at = datetime.utcnow()

                # Mark ride as paid
                ride = db.query(Ride).filter(Ride.id == payment.ride_id).first()
                if ride:
                    ride.is_paid = True

                db.commit()
                return {"message": "Payment marked as completed", "ride_id": payment.ride_id}

        # ── Payment Failed ────────────────────────────────────────────────────
        elif event["type"] == "payment_intent.payment_failed":
            intent = event["data"]["object"]
            payment = db.query(Payment).filter(
                Payment.stripe_payment_intent_id == intent["id"]
            ).first()

            if payment:
                payment.status = PaymentStatus.failed
                payment.failure_reason = intent.get("last_payment_error", {}).get("message")
                db.commit()

        return {"message": "Webhook received", "type": event["type"]}

    # ── Get Payment Status ────────────────────────────────────────────────────
    @staticmethod
    def get_payment_status(db: Session, ride_id: int, rider_id: int) -> Payment:
        payment = db.query(Payment).filter(Payment.ride_id == ride_id).first()
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        if payment.rider_id != rider_id:
            raise HTTPException(status_code=403, detail="Access denied")
        return payment

    # ── Request Refund ────────────────────────────────────────────────────────
    @staticmethod
    def refund_payment(db: Session, ride_id: int) -> dict:
        """Issue a full refund for a completed payment."""
        payment = db.query(Payment).filter(Payment.ride_id == ride_id).first()
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")

        if payment.status != PaymentStatus.completed:
            raise HTTPException(status_code=400, detail="Only completed payments can be refunded")

        try:
            stripe.Refund.create(payment_intent=payment.stripe_payment_intent_id)
            payment.status = PaymentStatus.refunded
            db.commit()
            return {"message": "Refund issued successfully", "ride_id": ride_id}
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Refund failed: {str(e)}")
