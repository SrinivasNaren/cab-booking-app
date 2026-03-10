import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional
import os

from app.core.config import settings


class EmailService:

    @staticmethod
    def _create_connection():
        """Create SMTP connection."""
        server = smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT)
        server.starttls()
        server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
        return server

    # ── Send Ride Receipt Email ───────────────────────────────────────────────
    @staticmethod
    def send_receipt_email(
        to_email: str,
        rider_name: str,
        ride_data: dict,
        pdf_path: Optional[str] = None
    ) -> bool:
        """
        Send a ride receipt email with optional PDF attachment.
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🚖 Your Ride Receipt — #{ride_data.get('ride_id', '')}"
            msg["From"] = settings.MAIL_FROM
            msg["To"] = to_email

            # ── HTML Email Body ───────────────────────────────────────────────
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px;">
                <div style="max-width: 600px; margin: auto; background: white;
                            border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">

                    <!-- Header -->
                    <div style="background: #1a1a2e; padding: 30px; text-align: center;">
                        <h1 style="color: white; margin: 0;">🚖 Cab Booking</h1>
                        <p style="color: #aaaaaa; margin: 5px 0 0 0;">Trip Receipt</p>
                    </div>

                    <!-- Body -->
                    <div style="padding: 30px;">
                        <p>Hi <strong>{rider_name}</strong>,</p>
                        <p>Thank you for your ride! Here's your trip summary:</p>

                        <!-- Ride Summary -->
                        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                            <tr style="background: #f0f4ff;">
                                <td style="padding: 10px; font-weight: bold;">Pickup</td>
                                <td style="padding: 10px;">{ride_data.get('pickup_address', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; font-weight: bold;">Drop</td>
                                <td style="padding: 10px;">{ride_data.get('drop_address', 'N/A')}</td>
                            </tr>
                            <tr style="background: #f0f4ff;">
                                <td style="padding: 10px; font-weight: bold;">Distance</td>
                                <td style="padding: 10px;">{ride_data.get('distance_km', 0)} km</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; font-weight: bold;">Duration</td>
                                <td style="padding: 10px;">{ride_data.get('duration_minutes', 0)} mins</td>
                            </tr>
                            <tr style="background: #f0f4ff;">
                                <td style="padding: 10px; font-weight: bold;">Driver</td>
                                <td style="padding: 10px;">{ride_data.get('driver_name', 'N/A')}</td>
                            </tr>
                        </table>

                        <!-- Total Fare -->
                        <div style="background: #1a1a2e; color: white; padding: 20px;
                                    border-radius: 8px; text-align: center; margin: 20px 0;">
                            <p style="margin: 0; font-size: 14px;">Total Amount Paid</p>
                            <h2 style="margin: 5px 0; font-size: 32px;">
                                ₹{ride_data.get('final_fare', 0):.2f}
                            </h2>
                            <p style="margin: 0; color: #aaaaaa; font-size: 12px;">
                                via {ride_data.get('payment_method', 'N/A').upper()}
                            </p>
                        </div>

                        <p style="color: #666; font-size: 13px;">
                            {f"A PDF receipt is attached to this email." if pdf_path else ""}
                        </p>
                    </div>

                    <!-- Footer -->
                    <div style="background: #f4f4f4; padding: 20px; text-align: center;">
                        <p style="color: #999; font-size: 12px; margin: 0;">
                            Questions? Contact support@cabbooking.com
                        </p>
                        <p style="color: #999; font-size: 12px; margin: 5px 0 0 0;">
                            © 2025 Cab Booking App. All rights reserved.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """

            msg.attach(MIMEText(html_body, "html"))

            # ── Attach PDF if provided ────────────────────────────────────────
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename=receipt_ride_{ride_data.get('ride_id')}.pdf"
                    )
                    msg.attach(part)

            server = EmailService._create_connection()
            server.sendmail(settings.MAIL_FROM, to_email, msg.as_string())
            server.quit()
            return True

        except Exception as e:
            print(f"Email sending failed: {e}")
            return False

    # ── Send Welcome Email ────────────────────────────────────────────────────
    @staticmethod
    def send_welcome_email(to_email: str, name: str, role: str) -> bool:
        """Send a welcome email after registration."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "🚖 Welcome to Cab Booking!"
            msg["From"] = settings.MAIL_FROM
            msg["To"] = to_email

            html_body = f"""
            <html><body style="font-family: Arial, sans-serif; padding: 30px;">
                <h2>Welcome, {name}! 🎉</h2>
                <p>Your <strong>{role}</strong> account has been created successfully.</p>
                <p>You can now log in and start {"booking rides" if role == "rider" else "accepting rides"}.</p>
                <br/>
                <p>— The Cab Booking Team</p>
            </body></html>
            """
            msg.attach(MIMEText(html_body, "html"))

            server = EmailService._create_connection()
            server.sendmail(settings.MAIL_FROM, to_email, msg.as_string())
            server.quit()
            return True

        except Exception as e:
            print(f"Welcome email failed: {e}")
            return False
