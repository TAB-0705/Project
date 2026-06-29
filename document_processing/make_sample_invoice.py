"""Generate a realistic sample invoice PDF for testing and demo purposes."""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def build(path="sample_invoice.pdf"):
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=18 * mm, bottomMargin=18 * mm)
    styles = getSampleStyleSheet()
    story = []

    title = ParagraphStyle("title", parent=styles["Title"], fontSize=26,
                           textColor=colors.HexColor("#1a3d6e"), spaceAfter=2)
    story.append(Paragraph("NORTHWIND TRADING CO.", title))
    story.append(Paragraph("221B Market Street, Springfield, IL 62704",
                           styles["Normal"]))
    story.append(Paragraph("Email: billing@northwind.example  |  Phone: +1 (217) 555-0142",
                           styles["Normal"]))
    story.append(Spacer(1, 10))

    inv_head = ParagraphStyle("inv", parent=styles["Heading1"], fontSize=20,
                              textColor=colors.HexColor("#b23b3b"))
    story.append(Paragraph("INVOICE", inv_head))
    story.append(Spacer(1, 4))

    meta = Table([
        ["Invoice Number:", "INV-2026-00871", "Invoice Date:", "12 June 2026"],
        ["Account No:", "AC-55320", "Due Date:", "12 July 2026"],
    ], colWidths=[32 * mm, 45 * mm, 28 * mm, 45 * mm])
    meta.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(meta)
    story.append(Spacer(1, 10))

    addr = Table([
        ["Bill To:", "Ship To:"],
        ["Acme Robotics Inc.\n45 Innovation Way\nAustin, TX 73301\nattn: Dana Mills",
         "Acme Robotics Warehouse\n900 Logistics Blvd\nAustin, TX 73302"],
    ], colWidths=[88 * mm, 88 * mm])
    addr.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 1), (-1, 1), 4),
    ]))
    story.append(addr)
    story.append(Spacer(1, 14))

    data = [["#", "Description", "Qty", "Unit Price", "Amount"],
            ["1", "CNC Servo Motor (Model SX-200)", "4", "$320.00", "$1,280.00"],
            ["2", "Aluminium Mounting Bracket", "12", "$18.50", "$222.00"],
            ["3", "Industrial Wiring Harness 5m", "6", "$47.25", "$283.50"],
            ["4", "On-site Calibration Service", "2", "$150.00", "$300.00"]]
    items = Table(data, colWidths=[12 * mm, 86 * mm, 18 * mm, 30 * mm, 30 * mm])
    items.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3d6e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#888888")),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f2f5fa")]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(items)
    story.append(Spacer(1, 10))

    totals = Table([
        ["Subtotal:", "$2,085.50"],
        ["Tax (GST 8%):", "$166.84"],
        ["Grand Total:", "$2,252.34"],
    ], colWidths=[40 * mm, 36 * mm], hAlign="RIGHT")
    totals.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, -1), (-1, -1), colors.HexColor("#b23b3b")),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(totals)
    story.append(Spacer(1, 16))
    story.append(Paragraph("Payment due within 30 days. Make cheques payable to "
                           "Northwind Trading Co. Thank you for your business!",
                           styles["Italic"]))
    doc.build(story)
    print("wrote", path)


if __name__ == "__main__":
    build()
