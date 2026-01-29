from reportlab.lib.pagesizes import A4, letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os

def generate_receipt(service_request: dict, customer: dict):
    """Generate PDF receipt for service request"""
    filename = f"receipt_{service_request['request_number']}.pdf"
    filepath = f"static/receipts/{filename}"
    
    os.makedirs("static/receipts", exist_ok=True)
    
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4
    
    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "FIRE EXTINGUISHER SERVICE RECEIPT")
    
    # Company Info
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 80, "Modern Safety Systems")
    c.drawString(50, height - 95, "Phone: +265 999 756 168")
    c.drawString(50, height - 110, "Email: info@modernsafety.mw")
    
    # Receipt Details
    c.drawString(400, height - 50, f"Receipt: #{service_request['request_number']}")
    c.drawString(400, height - 65, f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    
    # Customer Info
    c.drawString(50, height - 150, f"Customer: {customer['full_name']}")
    c.drawString(50, height - 165, f"Phone: {customer['phone']}")
    c.drawString(50, height - 180, f"Address: {service_request['address']}")
    
    # Service Details
    c.drawString(50, height - 220, f"Service: {service_request['service_type'].replace('_', ' ').title()}")
    c.drawString(50, height - 235, f"Extinguisher: {service_request.get('extinguisher_type', 'N/A')}")
    c.drawString(50, height - 250, f"Quantity: {service_request['quantity']}")
    
    if service_request.get('quote_amount'):
        c.drawString(50, height - 280, f"Quote Amount: MK{service_request['quote_amount']:,.2f}")
    
    c.drawString(50, height - 320, "Status: " + service_request['status'].title())
    
    # Footer
    c.drawString(50, height - 370, "Thank you for choosing Modern Safety Systems!")
    
    c.save()
    return filepath

def generate_order_invoice(order_data: dict, customer: dict):
    """Generate PDF invoice for an order"""
    # Create invoices directory if it doesn't exist
    os.makedirs("static/invoices", exist_ok=True)
    
    # Generate filename
    filename = f"invoice_{order_data['order_number']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = f"static/invoices/{filename}"
    
    # Create PDF document
    doc = SimpleDocTemplate(filepath, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=24,
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    # Header style
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12
    )
    
    # Normal style
    normal_style = styles['Normal']
    
    # Add title
    story.append(Paragraph("INVOICE", title_style))
    
    # Company info
    company_info = [
        ["Modern Safety Systems", ""],
        ["P.O. Box 1234", ""],
        ["Lilongwe, Malawi", ""],
        ["Phone: +265 999 756 168", ""],
        ["Email: info@modernsafety.mw", ""],
        ["Website: www.modernsafety.mw", ""]
    ]
    
    # Invoice details
    created_at = order_data['created_at']
    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        except:
            created_at = datetime.now()
    
    invoice_info = [
        ["Invoice Number:", order_data['order_number']],
        ["Invoice Date:", datetime.now().strftime("%d/%m/%Y")],
        ["Order Date:", created_at.strftime("%d/%m/%Y")],
        ["Payment Terms:", "Due on Receipt"]
    ]
    
    # Combine tables side by side
    combined_data = []
    for i in range(max(len(company_info), len(invoice_info))):
        row = []
        if i < len(company_info):
            row.append(company_info[i][0])
            row.append(company_info[i][1])
        else:
            row.extend(["", ""])
        
        if i < len(invoice_info):
            row.append(invoice_info[i][0])
            row.append(invoice_info[i][1])
        else:
            row.extend(["", ""])
        
        combined_data.append(row)
    
    company_invoice_table = Table(combined_data, colWidths=[2*inch, 2*inch, 1.5*inch, 2*inch])
    company_invoice_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(company_invoice_table)
    story.append(Spacer(1, 20))
    
    # Bill To section
    story.append(Paragraph("BILL TO", header_style))
    
    client_info = [
        ["Client Name:", customer['full_name']],
        ["Email:", customer['email']],
        ["Phone:", customer['phone']],
        ["Shipping Address:", order_data.get('shipping_address', 'Not specified')],
        ["Billing Address:", order_data.get('billing_address', order_data.get('shipping_address', 'Not specified'))]
    ]
    
    client_table = Table(client_info, colWidths=[1.5*inch, 6*inch])
    client_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(client_table)
    story.append(Spacer(1, 20))
    
    # Order items table
    story.append(Paragraph("ORDER ITEMS", header_style))
    
    items_data = [["Item", "Description", "Quantity", "Unit Price", "Total"]]
    
    for item in order_data.get('items', []):
        # Truncate description if too long
        description = item.get('product_description', '')
        if len(description) > 50:
            description = description[:50] + '...'
        
        items_data.append([
            item.get('product_name', 'Product'),
            description,
            str(item['quantity']),
            f"MK {item['unit_price']:,.2f}",
            f"MK {item['total_price']:,.2f}"
        ])
    
    items_table = Table(items_data, colWidths=[1.5*inch, 2.5*inch, 0.8*inch, 1.2*inch, 1.2*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),
        ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    
    story.append(items_table)
    story.append(Spacer(1, 20))
    
    # Summary table
    summary_data = [
        ["Subtotal:", f"MK {order_data['subtotal']:,.2f}"],
        ["Tax (16%):", f"MK {order_data.get('tax', 0):,.2f}"],
        ["Shipping Fee:", f"MK {order_data.get('shipping_fee', 0):,.2f}"],
        ["", ""],
        ["TOTAL AMOUNT:", f"MK {order_data['total_amount']:,.2f}"]
    ]
    
    summary_table = Table(summary_data, colWidths=[4*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (1, -1), 14),
        ('LINEABOVE', (0, -1), (1, -1), 1, colors.black),
        ('TOPPADDING', (0, -1), (1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    # Payment information
    payment_info = [
        ["Payment Method:", order_data.get('payment_method', 'Not specified').upper()],
        ["Payment Status:", order_data.get('payment_status', 'pending').upper()],
        ["Order Status:", order_data.get('status', 'pending').upper()]
    ]
    
    if order_data.get('notes'):
        payment_info.append(["Order Notes:", order_data['notes']])
    
    payment_table = Table(payment_info, colWidths=[1.5*inch, 6*inch])
    payment_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(payment_table)
    story.append(Spacer(1, 30))
    
    # Terms and conditions
    terms = [
        "TERMS AND CONDITIONS:",
        "1. All prices are in Malawi Kwacha (MK)",
        "2. Payment is due within 7 days of invoice date",
        "3. Goods remain property of Modern Safety Systems until paid in full",
        "4. Returns accepted within 14 days with original receipt",
        "5. Warranty provided as per manufacturer specifications"
    ]
    
    for term in terms:
        story.append(Paragraph(term, normal_style))
    
    story.append(Spacer(1, 20))
    
    # Thank you message
    story.append(Paragraph("Thank you for your business!", ParagraphStyle(
        'ThankYou',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_CENTER,
        spaceBefore=20
    )))
    
    # Build PDF
    doc.build(story)
    
    return filepath