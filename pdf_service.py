import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


class PDFService:

    @staticmethod
    def generate_receipt(ride_data: dict, output_path: str) -> str:
        """
        Generate a professional PDF receipt for a completed ride.

        ride_data keys:
            ride_id, rider_name, rider_email, driver_name,
            vehicle_model, vehicle_plate, pickup_address, drop_address,
            distance_km, duration_minutes, fare_breakdown (dict),
            final_fare, payment_method, payment_status,
            ride_date, ride_start_time, ride_end_time
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=40, leftMargin=40,
                                topMargin=40, bottomMargin=40)

        styles = getSampleStyleSheet()
        story = []

        # ── Custom Styles ─────────────────────────────────────────────────────
        title_style = ParagraphStyle("title", parent=styles["Heading1"],
                                     fontSize=22, textColor=colors.HexColor("#1a1a2e"),
                                     alignment=TA_CENTER, spaceAfter=4)
        subtitle_style = ParagraphStyle("subtitle", parent=styles["Normal"],
                                        fontSize=11, textColor=colors.HexColor("#666666"),
                                        alignment=TA_CENTER, spaceAfter=2)
        section_style = ParagraphStyle("section", parent=styles["Heading2"],
                                       fontSize=12, textColor=colors.HexColor("#16213e"),
                                       spaceBefore=14, spaceAfter=6)
        normal_style = ParagraphStyle("normal", parent=styles["Normal"],
                                      fontSize=10, textColor=colors.HexColor("#333333"))

        # ── Header ────────────────────────────────────────────────────────────
        story.append(Paragraph("🚖 Cab Booking", title_style))
        story.append(Paragraph("Trip Receipt", subtitle_style))
        story.append(Paragraph(f"Receipt #RIDE-{ride_data['ride_id']:05d}", subtitle_style))
        story.append(Spacer(1, 0.1 * inch))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a1a2e")))
        story.append(Spacer(1, 0.15 * inch))

        # ── Ride Info Table ───────────────────────────────────────────────────
        story.append(Paragraph("Ride Details", section_style))
        ride_info = [
            ["Date", ride_data.get("ride_date", "N/A")],
            ["Pickup", ride_data.get("pickup_address", "N/A")],
            ["Drop", ride_data.get("drop_address", "N/A")],
            ["Distance", f"{ride_data.get('distance_km', 0)} km"],
            ["Duration", f"{ride_data.get('duration_minutes', 0)} mins"],
            ["Driver", ride_data.get("driver_name", "N/A")],
            ["Vehicle", f"{ride_data.get('vehicle_model', '')} — {ride_data.get('vehicle_plate', '')}"],
        ]

        ride_table = Table(ride_info, colWidths=[2 * inch, 4.5 * inch])
        ride_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f4ff")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f9f9f9")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(ride_table)

        # ── Fare Breakdown ────────────────────────────────────────────────────
        story.append(Spacer(1, 0.15 * inch))
        story.append(Paragraph("Fare Breakdown", section_style))

        breakdown = ride_data.get("fare_breakdown", {})
        fare_rows = [
            ["Description", "Amount"],
            ["Base Fare", f"₹{breakdown.get('base_fare', 0):.2f}"],
            ["Distance Charge", f"₹{breakdown.get('distance_charge', 0):.2f}"],
            ["Time Charge", f"₹{breakdown.get('time_charge', 0):.2f}"],
        ]

        if breakdown.get("surge_charge"):
            fare_rows.append(["Surge Charge", f"₹{breakdown['surge_charge']:.2f}"])

        fare_rows.append(["", ""])
        fare_rows.append(["TOTAL FARE", f"₹{ride_data.get('final_fare', 0):.2f}"])

        fare_table = Table(fare_rows, colWidths=[4 * inch, 2.5 * inch])
        fare_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("FONTSIZE", (0, -1), (-1, -1), 12),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f9f9f9")]),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8f4fd")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ]))
        story.append(fare_table)

        # ── Payment Info ──────────────────────────────────────────────────────
        story.append(Spacer(1, 0.15 * inch))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")))
        story.append(Spacer(1, 0.1 * inch))

        payment_style = ParagraphStyle("payment", parent=styles["Normal"],
                                       fontSize=10, textColor=colors.HexColor("#555555"),
                                       alignment=TA_CENTER)
        story.append(Paragraph(
            f"Payment Method: <b>{ride_data.get('payment_method', 'N/A').upper()}</b> &nbsp;|&nbsp; "
            f"Status: <b>{ride_data.get('payment_status', 'N/A').upper()}</b>",
            payment_style
        ))

        # ── Footer ────────────────────────────────────────────────────────────
        story.append(Spacer(1, 0.3 * inch))
        footer_style = ParagraphStyle("footer", parent=styles["Normal"],
                                      fontSize=9, textColor=colors.HexColor("#999999"),
                                      alignment=TA_CENTER)
        story.append(Paragraph("Thank you for riding with us! 🚖", footer_style))
        story.append(Paragraph(
            f"Generated on {datetime.now().strftime('%d %B %Y, %I:%M %p')}",
            footer_style
        ))

        doc.build(story)
        return output_path
