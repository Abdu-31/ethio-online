"""
pdf_generator.py — Generates appointment confirmation PDF
Sent directly to customer when admin marks order as booked.
"""
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# Ethiopian flag colors
GREEN  = colors.HexColor("#078930")
YELLOW = colors.HexColor("#FCDD09")
RED    = colors.HexColor("#DA121A")
DARK   = colors.HexColor("#1a1a2e")
LIGHT  = colors.HexColor("#f5f5f5")

def generate_appointment_pdf(order: dict) -> bytes:
    """Generate appointment confirmation PDF and return as bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontSize=20,
        fontName="Helvetica-Bold",
        textColor=DARK,
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=11,
        fontName="Helvetica",
        textColor=colors.grey,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Normal"],
        fontSize=10,
        fontName="Helvetica-Bold",
        textColor=GREEN,
        spaceAfter=6,
        spaceBefore=12,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        fontName="Helvetica",
        textColor=DARK,
        spaceAfter=4,
    )
    warning_style = ParagraphStyle(
        "Warning",
        parent=styles["Normal"],
        fontSize=9,
        fontName="Helvetica-Oblique",
        textColor=colors.HexColor("#cc0000"),
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        fontName="Helvetica",
        textColor=colors.grey,
        alignment=TA_CENTER,
    )

    story = []

    # ── Ethiopian flag stripe ──────────────────────────────────────────────
    flag_data = [["", "", ""]]
    flag_table = Table(flag_data, colWidths=[5.8*cm, 5.8*cm, 5.8*cm], rowHeights=[0.5*cm])
    flag_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,0), GREEN),
        ("BACKGROUND", (1,0), (1,0), YELLOW),
        ("BACKGROUND", (2,0), (2,0), RED),
        ("LEFTPADDING",  (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING",   (0,0), (-1,-1), 0),
        ("BOTTOMPADDING",(0,0), (-1,-1), 0),
    ]))
    story.append(flag_table)
    story.append(Spacer(1, 0.4*cm))

    # ── Header ─────────────────────────────────────────────────────────────
    story.append(Paragraph("🇪🇹 Ethiopia Passport Service", title_style))
    story.append(Paragraph("Appointment Confirmation / የቀጠሮ ማረጋገጫ / Mirkaneessa Beellama", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=GREEN, spaceAfter=12))

    # ── Appointment details box ────────────────────────────────────────────
    appt_date     = order.get("appointment_date", "To be confirmed")
    appt_time     = order.get("appointment_time", "To be confirmed")
    appt_location = order.get("appointment_location", "To be confirmed")

    appt_data = [
        ["📅  Date",     appt_date],
        ["🕐  Time",     appt_time],
        ["📍  Location", appt_location],
    ]
    appt_table = Table(appt_data, colWidths=[4*cm, 12.7*cm])
    appt_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), LIGHT),
        ("BACKGROUND",    (0,0), (0,-1), colors.HexColor("#e8f5e9")),
        ("FONTNAME",      (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",      (1,0), (1,-1), "Helvetica"),
        ("FONTSIZE",      (0,0), (-1,-1), 11),
        ("TEXTCOLOR",     (0,0), (0,-1), GREEN),
        ("TEXTCOLOR",     (1,0), (1,-1), DARK),
        ("TOPPADDING",    (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("LEFTPADDING",   (0,0), (-1,-1), 12),
        ("GRID",          (0,0), (-1,-1), 0.5, colors.white),
        ("ROUNDEDCORNERS",(0,0), (-1,-1), 4),
    ]))
    story.append(appt_table)
    story.append(Spacer(1, 0.5*cm))

    # ── Customer details ───────────────────────────────────────────────────
    story.append(Paragraph("CUSTOMER INFORMATION", section_style))
    details = [
        ["Full Name",      order.get("name", "")],
        ["Phone Number",   order.get("phone", "")],
        ["City",           order.get("city", "")],
        ["Passport Type",  order.get("passport_type", "")],
        ["Service Type",   order.get("urgency", "")],
        ["Order ID",       f"#{order.get('id', '')}"],
        ["Order Date",     str(order.get("created_at", ""))[:10]],
    ]
    det_table = Table(details, colWidths=[5*cm, 11.7*cm])
    det_table.setStyle(TableStyle([
        ("FONTNAME",      (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",      (1,0), (1,-1), "Helvetica"),
        ("FONTSIZE",      (0,0), (-1,-1), 10),
        ("TEXTCOLOR",     (0,0), (0,-1), colors.HexColor("#444")),
        ("TEXTCOLOR",     (1,0), (1,-1), DARK),
        ("TOPPADDING",    (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("LINEBELOW",     (0,0), (-1,-2), 0.5, colors.HexColor("#eeeeee")),
        ("ROWBACKGROUNDS",(0,0), (-1,-1), [colors.white, LIGHT]),
    ]))
    story.append(det_table)
    story.append(Spacer(1, 0.5*cm))

    # ── Payment confirmation ───────────────────────────────────────────────
    payment_status = order.get("payment_status", "unpaid")
    if payment_status == "paid":
        pay_text = "✅  Total Fee: PAID — 6,000 ETB (Government + Service)"
        pay_color = GREEN
    else:
        pay_text = "⚠️  Total Fee: 6,000 ETB — PENDING PAYMENT"
        pay_color = colors.HexColor("#e67e22")

    pay_style = ParagraphStyle("Pay", parent=styles["Normal"],
        fontSize=11, fontName="Helvetica-Bold",
        textColor=pay_color, alignment=TA_CENTER,
        borderColor=pay_color, borderWidth=1,
        borderPadding=8, backColor=colors.HexColor("#f9f9f9"))
    story.append(Paragraph(pay_text, pay_style))
    story.append(Spacer(1, 0.5*cm))

    # ── Instructions ───────────────────────────────────────────────────────
    story.append(Paragraph("WHAT TO BRING / ምን ማምጣት አለቦት", section_style))
    instructions = [
        "✔  Original National ID Card (Kebele ID or Fayda ID)",
        "✔  2 recent passport-size photos (white background)",
        "✔  Birth certificate (for new passports)",
        "✔  Old passport (for renewals)",
        "✔  Payment receipt confirming service fee paid",
        "✔  This appointment confirmation (printed or on phone)",
    ]
    for item in instructions:
        story.append(Paragraph(item, body_style))

    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph(
        "⚠️  Please arrive 15 minutes before your appointment time.",
        warning_style
    ))
    story.append(Paragraph(
        "⚠️  Late arrivals may lose their slot without refund.",
        warning_style
    ))

    # ── Footer ─────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.8*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        f"Generated by Ethio Online Passport Service Bot  •  {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        footer_style
    ))
    story.append(Paragraph(
        "For support contact us on Telegram. Order ID: #" + str(order.get("id", "")),
        footer_style
    ))

    doc.build(story)
    return buffer.getvalue()
