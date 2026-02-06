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
    
    # Add Logo in top-left corner
    logo_path = "src/assets/logo.png"
    if os.path.exists(logo_path):
        try:
            # Add logo in top-left corner (50px from left, 50px from top)
            logo_size = 60  # 60px
            logo_x = 50
            logo_y = height - 50 - logo_size  # 50px from top
            c.drawImage(logo_path, logo_x, logo_y, width=logo_size, height=logo_size, preserveAspectRatio=True)
        except:
            pass  # If logo fails to load, continue without it
    
    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50 + 70, height - 50, "FIRE EXTINGUISHER SERVICE RECEIPT")  # Offset for logo
    
    # Company Info
    c.setFont("Helvetica", 10)
    c.drawString(50 + 70, height - 80, "Modern Safety Systems")
    c.drawString(50 + 70, height - 95, "Phone: +265 999 756 168")
    c.drawString(50 + 70, height - 110, "Email: info@modernsafety.mw")
    
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
    """Generate PDF invoice for an order with logo"""
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
    
    # Create a header with logo and company info
    logo_path = "src/assets/logo.png"
    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=60, height=60)
            logo.hAlign = 'LEFT'
            story.append(logo)
        except:
            pass  # If logo fails to load, continue without it
    
    # Add company info next to logo using a table
    company_data = [
        ["Modern Safety Systems", f"Invoice #{order_data['order_number']}"],
        ["P.O. Box 1234", f"Date: {datetime.now().strftime('%d/%m/%Y')}"],
        ["Lilongwe, Malawi", f"Order Date: {datetime.strptime(order_data['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%d/%m/%Y') if 'created_at' in order_data else datetime.now().strftime('%d/%m/%Y')}"],
        ["Phone: +265 999 756 168", "Payment Terms: Due on Receipt"],
        ["Email: info@modernsafety.mw", ""],
        ["Website: www.modernsafety.mw", ""]
    ]
    
    company_table = Table(company_data, colWidths=[3*inch, 3*inch])
    company_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (0, -1), 0),
        ('RIGHTPADDING', (1, 0), (1, -1), 0),
    ]))
    
    story.append(company_table)
    story.append(Spacer(1, 20))
    
    # Title style
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=20,
        alignment=TA_CENTER,
        spaceAfter=20,
        textColor=colors.HexColor('#1e40af')  # Blue color for title
    )
    
    # Add invoice title
    story.append(Paragraph("INVOICE", title_style))
    
    # Header style
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=8,
        textColor=colors.HexColor('#334155')  # Dark gray
    )
    
    # Normal style
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        textColor=colors.HexColor('#475569')  # Medium gray
    )
    
    # Bill To section
    story.append(Paragraph("BILL TO", header_style))
    
    client_info = [
        ["Client Name:", customer['full_name']],
        ["Email:", customer['email']],
        ["Phone:", customer['phone']],
        ["Shipping Address:", order_data.get('shipping_address', 'Not specified')],
        ["Billing Address:", order_data.get('billing_address', order_data.get('shipping_address', 'Not specified'))]
    ]
    
    client_table = Table(client_info, colWidths=[1.2*inch, 5.8*inch])
    client_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    
    story.append(client_table)
    story.append(Spacer(1, 20))
    
    # Order items table
    story.append(Paragraph("ORDER ITEMS", header_style))
    
    items_data = [["Item", "Description", "Qty", "Unit Price", "Total"]]
    
    for item in order_data.get('items', []):
        # Truncate description if too long
        description = item.get('product_description', item.get('description', ''))
        if len(description) > 50:
            description = description[:50] + '...'
        
        unit_price = item.get('unit_price', item.get('price', 0))
        quantity = item.get('quantity', 1)
        total_price = unit_price * quantity
        
        items_data.append([
            item.get('product_name', item.get('name', 'Product')),
            description,
            str(quantity),
            f"MK {unit_price:,.0f}",
            f"MK {total_price:,.0f}"
        ])
    
    items_table = Table(items_data, colWidths=[1.2*inch, 2.8*inch, 0.6*inch, 1.2*inch, 1.2*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),  # Blue header
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),
        ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),  # Light gray background
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),  # Light gray grid
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f1f5f9')]),  # Alternating rows
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    
    story.append(items_table)
    story.append(Spacer(1, 20))
    
    # Summary table
    subtotal = order_data.get('subtotal', 0)
    tax = order_data.get('tax', 0)
    shipping_fee = order_data.get('shipping_fee', 0)
    total_amount = order_data.get('total_amount', 0)
    
    summary_data = [
        ["Subtotal:", f"MK {subtotal:,.0f}"],
        ["Tax (16%):", f"MK {tax:,.0f}"],
        ["Shipping Fee:", f"MK {shipping_fee:,.0f}"],
        ["", ""],
        ["TOTAL AMOUNT:", f"MK {total_amount:,.0f}"]
    ]
    
    summary_table = Table(summary_data, colWidths=[4*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (1, -2), 10),
        ('FONTSIZE', (0, -1), (1, -1), 12),
        ('TEXTCOLOR', (0, -1), (1, -1), colors.HexColor('#1e40af')),  # Blue for total
        ('LINEABOVE', (0, -1), (1, -1), 1, colors.HexColor('#1e40af')),
        ('TOPPADDING', (0, -1), (1, -1), 8),
        ('BOTTOMPADDING', (0, -1), (1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (1, -2), 4),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    # Payment information
    payment_info = [
        ["Payment Method:", order_data.get('payment_method', 'Not specified').title()],
        ["Payment Status:", order_data.get('payment_status', 'pending').title()],
        ["Order Status:", order_data.get('status', 'pending').title()]
    ]
    
    if order_data.get('notes'):
        payment_info.append(["Order Notes:", order_data['notes']])
    
    payment_table = Table(payment_info, colWidths=[1.2*inch, 5.8*inch])
    payment_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    
    story.append(payment_table)
    story.append(Spacer(1, 30))
    
    # Terms and conditions
    terms_style = ParagraphStyle(
        'Terms',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=4
    )
    
    story.append(Paragraph("TERMS AND CONDITIONS", header_style))
    
    terms = [
        "1. All prices are in Malawi Kwacha (MK)",
        "2. Payment is due within 7 days of invoice date",
        "3. Goods remain property of Modern Safety Systems until paid in full",
        "4. Returns accepted within 14 days with original receipt",
        "5. Warranty provided as per manufacturer specifications",
        "6. Late payments are subject to 2% monthly interest"
    ]
    
    for term in terms:
        story.append(Paragraph(term, terms_style))
    
    story.append(Spacer(1, 20))
    
    # Footer with thank you message
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_CENTER,
        spaceBefore=20,
        textColor=colors.HexColor('#475569')
    )
    
    story.append(Paragraph("Thank you for choosing Modern Safety Systems!", footer_style))
    
    contact_style = ParagraphStyle(
        'Contact',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        spaceBefore=10,
        textColor=colors.HexColor('#64748b')
    )
    
    story.append(Paragraph("For any inquiries, please contact: info@modernsafety.mw | +265 999 756 168", contact_style))
    
    # Build PDF
    doc.build(story)
    
    return filepath