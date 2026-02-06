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
    """Generate PDF receipt for service request with logo"""
    filename = f"receipt_{service_request['request_number']}.pdf"
    filepath = f"static/receipts/{filename}"
    
    os.makedirs("static/receipts", exist_ok=True)
    
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4
    
    # Add Logo in top-left corner
    logo_path = "assets/logo.png"  # Updated path
    if os.path.exists(logo_path):
        try:
            # Add logo in top-left corner (50px from left, 50px from top)
            logo_size = 60  # 60px
            logo_x = 50
            logo_y = height - 50 - logo_size  # 50px from top
            c.drawImage(logo_path, logo_x, logo_y, width=logo_size, height=logo_size, preserveAspectRatio=True)
        except:
            pass  # If logo fails to load, continue without it
    
    # Header with offset for logo
    c.setFont("Helvetica-Bold", 18)
    c.setFillColorRGB(0.231, 0.49, 0.969)  # Blue color #3b82f6
    c.drawString(120, height - 60, "FIRE EXTINGUISHER SERVICE RECEIPT")
    
    # Company Info
    c.setFont("Helvetica-Bold", 11)
    c.setFillColorRGB(0.149, 0.196, 0.219)  # Dark gray #263238
    c.drawString(120, height - 90, "Modern Safety Systems")
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.38, 0.49, 0.545)  # Medium gray #546e7a
    c.drawString(120, height - 105, "Phone: +265 999 756 168")
    c.drawString(120, height - 120, "Email: info@modernsafety.mw")
    
    # Receipt Details
    c.setFont("Helvetica-Bold", 11)
    c.setFillColorRGB(0.149, 0.196, 0.219)
    c.drawString(400, height - 60, f"Receipt: #{service_request['request_number']}")
    c.setFont("Helvetica", 10)
    c.drawString(400, height - 75, f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    
    # Customer Info Section
    c.setFont("Helvetica-Bold", 12)
    c.setFillColorRGB(0.149, 0.196, 0.219)
    c.drawString(50, height - 160, "Customer Information")
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.38, 0.49, 0.545)
    c.drawString(50, height - 180, f"Name: {customer['full_name']}")
    c.drawString(50, height - 195, f"Phone: {customer['phone']}")
    c.drawString(50, height - 210, f"Address: {service_request['address']}")
    
    # Service Details Section
    c.setFont("Helvetica-Bold", 12)
    c.setFillColorRGB(0.149, 0.196, 0.219)
    c.drawString(50, height - 240, "Service Details")
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.38, 0.49, 0.545)
    c.drawString(50, height - 260, f"Service Type: {service_request['service_type'].replace('_', ' ').title()}")
    c.drawString(50, height - 275, f"Extinguisher Type: {service_request.get('extinguisher_type', 'N/A')}")
    c.drawString(50, height - 290, f"Quantity: {service_request['quantity']}")
    
    if service_request.get('quote_amount'):
        c.setFont("Helvetica-Bold", 11)
        c.setFillColorRGB(0.149, 0.196, 0.219)
        c.drawString(50, height - 315, f"Quote Amount: MK{service_request['quote_amount']:,.2f}")
    
    # Status with colored box
    c.setFont("Helvetica-Bold", 11)
    status = service_request['status'].title()
    status_color = {
        'Pending': (0.98, 0.753, 0.176),  # Amber
        'Processing': (0.588, 0.482, 0.969),  # Purple
        'Completed': (0.105, 0.745, 0.541),  # Green
        'Cancelled': (0.957, 0.263, 0.212)  # Red
    }.get(status, (0.616, 0.769, 0.898))  # Default blue
    
    c.setFillColorRGB(*status_color)
    c.roundRect(50, height - 340, 100, 25, 10, fill=1)
    c.setFillColorRGB(0.149, 0.196, 0.219)
    c.drawString(75, height - 330, f"Status: {status}")
    
    # Footer
    c.setFont("Helvetica-Bold", 11)
    c.setFillColorRGB(0.231, 0.49, 0.969)  # Blue color
    c.drawString(50, height - 380, "Thank you for choosing Modern Safety Systems!")
    
    # Contact info footer
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.62, 0.71, 0.78)  # Light gray
    c.drawString(50, height - 400, "For inquiries: info@modernsafety.mw | +265 999 756 168")
    
    c.save()
    return filepath

def generate_order_invoice(order_data: dict, customer: dict):
    """Generate PDF invoice for an order with enhanced styling and logo"""
    # Create invoices directory if it doesn't exist
    os.makedirs("static/invoices", exist_ok=True)
    
    # Generate filename
    filename = f"invoice_{order_data['order_number']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = f"static/invoices/{filename}"
    
    # Create PDF document with more space for logo
    doc = SimpleDocTemplate(filepath, pagesize=A4, 
                          topMargin=0.7*inch, 
                          bottomMargin=0.5*inch,
                          leftMargin=0.5*inch,
                          rightMargin=0.5*inch)
    story = []
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=26,
        alignment=TA_CENTER,
        spaceAfter=20,
        textColor=colors.HexColor('#1e40af'),  # Dark blue
        fontName='Helvetica-Bold'
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=8,
        textColor=colors.HexColor('#334155'),  # Dark gray
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        textColor=colors.HexColor('#475569'),  # Medium gray
        fontName='Helvetica'
    )
    
    bold_style = ParagraphStyle(
        'Bold',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        textColor=colors.HexColor('#1e293b'),  # Very dark gray
        fontName='Helvetica-Bold'
    )
    
    # Logo and header table
    logo_path = "assets/logo.png"  # Updated path
    
    # Create a table with logo and company info
    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=60, height=60)
            logo_table_data = [[logo, "", "", ""]]
            logo_table = Table(logo_table_data, colWidths=[1*inch, 2*inch, 2*inch, 2*inch])
            logo_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(logo_table)
        except:
            pass  # If logo fails to load, continue without it
    
    # Company and invoice info side by side
    created_at = order_data['created_at']
    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        except:
            created_at = datetime.now()
    
    header_data = [
        [Paragraph("<b>Modern Safety Systems</b>", bold_style),
         Paragraph(f"<b>INVOICE #{order_data['order_number']}</b>", bold_style)],
        [Paragraph("P.O. Box 1234", normal_style),
         Paragraph(f"<b>Date:</b> {datetime.now().strftime('%d/%m/%Y')}", normal_style)],
        [Paragraph("Lilongwe, Malawi", normal_style),
         Paragraph(f"<b>Order Date:</b> {created_at.strftime('%d/%m/%Y')}", normal_style)],
        [Paragraph("Phone: +265 999 756 168", normal_style),
         Paragraph("<b>Payment Terms:</b> Due on Receipt", normal_style)],
        [Paragraph("Email: info@modernsafety.mw", normal_style), ""],
        [Paragraph("Website: www.modernsafety.mw", normal_style), ""]
    ]
    
    header_table = Table(header_data, colWidths=[3.5*inch, 3.5*inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 25))
    
    # Bill To section with background
    bill_to_data = [
        [Paragraph("<b>BILL TO</b>", header_style)],
        [Paragraph(f"<b>Client Name:</b> {customer['full_name']}", normal_style)],
        [Paragraph(f"<b>Email:</b> {customer['email']}", normal_style)],
        [Paragraph(f"<b>Phone:</b> {customer['phone']}", normal_style)],
        [Paragraph(f"<b>Shipping Address:</b> {order_data.get('shipping_address', 'Not specified')}", normal_style)],
        [Paragraph(f"<b>Billing Address:</b> {order_data.get('billing_address', order_data.get('shipping_address', 'Not specified'))}", normal_style)]
    ]
    
    bill_to_table = Table(bill_to_data, colWidths=[7*inch])
    bill_to_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),  # Blue header
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),  # Light gray background
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),  # Border
        ('PADDING', (0, 1), (-1, -1), (10, 6)),
        ('LEFTPADDING', (0, 1), (-1, -1), 12),
    ]))
    
    story.append(bill_to_table)
    story.append(Spacer(1, 25))
    
    # Order items table with enhanced styling
    story.append(Paragraph("ORDER ITEMS", header_style))
    
    items_data = [["Item", "Description", "Qty", "Unit Price", "Total"]]
    
    for item in order_data.get('items', []):
        description = item.get('product_description', item.get('description', ''))
        if len(description) > 40:
            description = description[:40] + '...'
        
        unit_price = item.get('unit_price', item.get('price', 0))
        quantity = item.get('quantity', 1)
        total_price = unit_price * quantity
        
        items_data.append([
            Paragraph(item.get('product_name', item.get('name', 'Product')), normal_style),
            Paragraph(description, normal_style),
            Paragraph(str(quantity), normal_style),
            Paragraph(f"MK {unit_price:,.0f}", normal_style),
            Paragraph(f"MK {total_price:,.0f}", normal_style)
        ])
    
    items_table = Table(items_data, colWidths=[1.5*inch, 2.5*inch, 0.6*inch, 1.2*inch, 1.2*inch])
    items_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),  # Dark blue
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        
        # Data rows
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ffffff')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),
        ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),  # Alternating rows
    ]))
    
    story.append(items_table)
    story.append(Spacer(1, 25))
    
    # Summary table with better styling
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
        ('FONTNAME', (0, 0), (1, -2), 'Helvetica'),
        ('FONTNAME', (0, -1), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (1, -2), 11),
        ('FONTSIZE', (0, -1), (1, -1), 14),
        ('TEXTCOLOR', (0, -1), (1, -1), colors.HexColor('#1e40af')),  # Blue for total
        ('LINEABOVE', (0, -1), (1, -1), 2, colors.HexColor('#1e40af')),
        ('TOPPADDING', (0, -1), (1, -1), 12),
        ('BOTTOMPADDING', (0, -1), (1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (1, -2), 8),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 25))
    
    # Payment information with status badges
    payment_status = order_data.get('payment_status', 'pending').upper()
    order_status = order_data.get('status', 'pending').upper()
    
    payment_info_data = [
        [Paragraph("<b>Payment Information</b>", header_style)],
        [Paragraph(f"<b>Payment Method:</b> {order_data.get('payment_method', 'Not specified').title()}", normal_style)],
        [Paragraph(f"<b>Payment Status:</b> <font color='{get_status_color(payment_status)}'>{payment_status}</font>", normal_style)],
        [Paragraph(f"<b>Order Status:</b> <font color='{get_status_color(order_status)}'>{order_status}</font>", normal_style)]
    ]
    
    if order_data.get('notes'):
        payment_info_data.append([Paragraph(f"<b>Order Notes:</b> {order_data['notes']}", normal_style)])
    
    payment_info_table = Table(payment_info_data, colWidths=[7*inch])
    payment_info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),  # Blue header
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),  # Light gray background
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),  # Border
        ('PADDING', (0, 1), (-1, -1), (10, 6)),
        ('LEFTPADDING', (0, 1), (-1, -1), 12),
    ]))
    
    story.append(payment_info_table)
    story.append(Spacer(1, 30))
    
    # Terms and conditions with better styling
    terms_style = ParagraphStyle(
        'Terms',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#64748b'),  # Gray
        spaceAfter=4,
        fontName='Helvetica'
    )
    
    story.append(Paragraph("<b>TERMS AND CONDITIONS</b>", header_style))
    
    terms_box_data = [
        [Paragraph("1. All prices are in Malawi Kwacha (MK)", terms_style)],
        [Paragraph("2. Payment is due within 7 days of invoice date", terms_style)],
        [Paragraph("3. Goods remain property of Modern Safety Systems until paid in full", terms_style)],
        [Paragraph("4. Returns accepted within 14 days with original receipt", terms_style)],
        [Paragraph("5. Warranty provided as per manufacturer specifications", terms_style)],
        [Paragraph("6. Late payments are subject to 2% monthly interest", terms_style)]
    ]
    
    terms_box_table = Table(terms_box_data, colWidths=[7*inch])
    terms_box_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),  # Light gray background
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),  # Border
        ('PADDING', (0, 0), (-1, -1), (12, 8)),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(terms_box_table)
    story.append(Spacer(1, 20))
    
    # Footer with thank you message and logo
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_CENTER,
        spaceBefore=20,
        textColor=colors.HexColor('#1e40af'),  # Blue
        fontName='Helvetica-Bold'
    )
    
    story.append(Paragraph("Thank you for choosing Modern Safety Systems!", footer_style))
    
    contact_style = ParagraphStyle(
        'Contact',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        spaceBefore=10,
        textColor=colors.HexColor('#64748b'),  # Gray
        fontName='Helvetica'
    )
    
    story.append(Paragraph("For any inquiries, please contact: info@modernsafety.mw | +265 999 756 168", contact_style))
    
    # Build PDF
    doc.build(story)
    
    return filepath

def get_status_color(status: str) -> str:
    """Get color for status based on status value"""
    status_lower = status.lower()
    if 'paid' in status_lower or 'completed' in status_lower or 'delivered' in status_lower:
        return '#10b981'  # Green
    elif 'pending' in status_lower or 'processing' in status_lower:
        return '#f59e0b'  # Amber
    elif 'cancelled' in status_lower or 'failed' in status_lower or 'rejected' in status_lower:
        return '#ef4444'  # Red
    elif 'shipped' in status_lower or 'refunded' in status_lower:
        return '#3b82f6'  # Blue
    else:
        return '#6b7280'  # Gray