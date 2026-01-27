from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import os

def generate_receipt(service_request: dict, customer: dict):
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
    c.drawString(50, height - 80, "Fire Safety Solutions")
    c.drawString(50, height - 95, "Phone: +265 999 756 168")
    c.drawString(50, height - 110, "Email: info@firesafety.mw")
    
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
    c.drawString(50, height - 370, "Thank you for choosing Fire Safety Solutions!")
    
    c.save()
    return filepath
