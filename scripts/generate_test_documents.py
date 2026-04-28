#!/usr/bin/env python3
"""
Generate Test Documents for ATLAS Agent 1 (Vision)
Creates 5 invoices + 2 contracts with intentional "traps" for testing
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
from datetime import datetime, timedelta
import random

# Color constants
HEADER_COLOR = colors.HexColor("#1a1a1a")
ACCENT_COLOR = colors.HexColor("#0066cc")
LIGHT_GRAY = colors.HexColor("#f5f5f5")

def create_invoice_with_trap_1():
    """Invoice with incorrect total (TRAP: 1500 + 2500 + 3000 should be 7000, but says 7500)"""
    doc = SimpleDocTemplate("test_documents/INVOICE_001_TRAP_MATH.pdf", pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Header
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HEADER_COLOR,
        spaceAfter=30,
        alignment=1  # Center
    )
    
    elements.append(Paragraph("ACME CORPORATION", title_style))
    elements.append(Paragraph("Invoice #INV-2026-001", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Invoice details
    details = [
        ["Invoice Date:", "April 15, 2026"],
        ["Due Date:", "May 15, 2026"],
        ["Bill To:", "Tech Solutions LLC"],
        ["Amount Due:", "$7,500 USD"],  # TRAP: Should be $7,000
    ]
    
    details_table = Table(details, colWidths=[2*inch, 3*inch])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), LIGHT_GRAY),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    
    elements.append(details_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Line items
    items = [
        ['Description', 'Quantity', 'Unit Price', 'Total'],
        ['Software Development Services', '1', '$1,500.00', '$1,500.00'],
        ['Hardware Installation', '1', '$2,500.00', '$2,500.00'],
        ['Consulting Hours (20 hrs @ $150)', '20', '$150.00', '$3,000.00'],
    ]
    
    items_table = Table(items, colWidths=[2.5*inch, 1*inch, 1.5*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    
    elements.append(items_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Total
    total_style = ParagraphStyle(
        'Total',
        parent=styles['Normal'],
        fontSize=14,
        textColor=HEADER_COLOR,
        alignment=2  # Right
    )
    elements.append(Paragraph("<b>TOTAL: $7,500.00 USD</b>", total_style))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("Payment Terms: Net 30 | Bank Transfer", styles['Normal']))
    
    doc.build(elements)
    print("✅ Created: INVOICE_001_TRAP_MATH.pdf (Math error: should be $7,000)")

def create_invoice_normal():
    """Normal invoice without traps"""
    doc = SimpleDocTemplate("test_documents/INVOICE_002_NORMAL.pdf", pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HEADER_COLOR,
        spaceAfter=30,
        alignment=1
    )
    
    elements.append(Paragraph("TECHVISION INC", title_style))
    elements.append(Paragraph("Invoice #INV-2026-002", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    details = [
        ["Invoice Date:", "April 18, 2026"],
        ["Due Date:", "May 18, 2026"],
        ["Bill To:", "Global Industries Corp"],
        ["Amount Due:", "$5,200 USD"],
    ]
    
    details_table = Table(details, colWidths=[2*inch, 3*inch])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), LIGHT_GRAY),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    
    elements.append(details_table)
    elements.append(Spacer(1, 0.3*inch))
    
    items = [
        ['Description', 'Quantity', 'Unit Price', 'Total'],
        ['Cloud Infrastructure Setup', '1', '$3,000.00', '$3,000.00'],
        ['Security Audit', '1', '$1,500.00', '$1,500.00'],
        ['Training (8 hours)', '8', '$175.00', '$700.00'],
    ]
    
    items_table = Table(items, colWidths=[2.5*inch, 1*inch, 1.5*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(items_table)
    elements.append(Spacer(1, 0.3*inch))
    
    total_style = ParagraphStyle(
        'Total',
        parent=styles['Normal'],
        fontSize=14,
        textColor=HEADER_COLOR,
        alignment=2
    )
    elements.append(Paragraph("<b>TOTAL: $5,200.00 USD</b>", total_style))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("Payment Terms: Net 30 | Credit Card Accepted", styles['Normal']))
    
    doc.build(elements)
    print("✅ Created: INVOICE_002_NORMAL.pdf (Valid invoice)")

def create_invoice_with_trap_2():
    """Invoice with missing vendor information"""
    doc = SimpleDocTemplate("test_documents/INVOICE_003_TRAP_MISSING_INFO.pdf", pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HEADER_COLOR,
        spaceAfter=30,
        alignment=1
    )
    
    elements.append(Paragraph("INVOICE", title_style))
    elements.append(Paragraph("Invoice #INV-2026-003", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # TRAP: Missing vendor name
    details = [
        ["Invoice Date:", "April 20, 2026"],
        ["Due Date:", "May 20, 2026"],
        ["Bill To:", "Unknown Client"],  # TRAP
        ["Amount Due:", "$3,800 USD"],
    ]
    
    details_table = Table(details, colWidths=[2*inch, 3*inch])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), LIGHT_GRAY),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    
    elements.append(details_table)
    elements.append(Spacer(1, 0.3*inch))
    
    items = [
        ['Description', 'Quantity', 'Unit Price', 'Total'],
        ['Professional Services', '1', '$2,500.00', '$2,500.00'],
        ['Materials', '1', '$1,300.00', '$1,300.00'],
    ]
    
    items_table = Table(items, colWidths=[2.5*inch, 1*inch, 1.5*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(items_table)
    elements.append(Spacer(1, 0.3*inch))
    
    total_style = ParagraphStyle(
        'Total',
        parent=styles['Normal'],
        fontSize=14,
        textColor=HEADER_COLOR,
        alignment=2
    )
    elements.append(Paragraph("<b>TOTAL: $3,800.00 USD</b>", total_style))
    
    doc.build(elements)
    print("✅ Created: INVOICE_003_TRAP_MISSING_INFO.pdf (Missing vendor name)")

def create_invoice_with_trap_3():
    """Invoice with unclear amounts (blurry effect simulated)"""
    doc = SimpleDocTemplate("test_documents/INVOICE_004_TRAP_UNCLEAR.pdf", pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HEADER_COLOR,
        spaceAfter=30,
        alignment=1
    )
    
    elements.append(Paragraph("ENTERPRISE SOLUTIONS", title_style))
    elements.append(Paragraph("Invoice #INV-2026-004", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    details = [
        ["Invoice Date:", "April 22, 2026"],
        ["Due Date:", "May 22, 2026"],
        ["Bill To:", "DataCore Systems"],
        ["Amount Due:", "$6,750 USD"],  # TRAP: Unclear if this is correct
    ]
    
    details_table = Table(details, colWidths=[2*inch, 3*inch])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), LIGHT_GRAY),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    
    elements.append(details_table)
    elements.append(Spacer(1, 0.3*inch))
    
    items = [
        ['Description', 'Quantity', 'Unit Price', 'Total'],
        ['API Integration', '1', '$4,000.00', '$4,000.00'],
        ['Support Package (6 months)', '1', '$2,250.00', '$2,250.00'],  # TRAP: Hard to read
    ]
    
    items_table = Table(items, colWidths=[2.5*inch, 1*inch, 1.5*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(items_table)
    elements.append(Spacer(1, 0.3*inch))
    
    total_style = ParagraphStyle(
        'Total',
        parent=styles['Normal'],
        fontSize=14,
        textColor=HEADER_COLOR,
        alignment=2
    )
    elements.append(Paragraph("<b>TOTAL: $6,250.00 USD</b>", total_style))  # TRAP: Doesn't match line items
    
    doc.build(elements)
    print("✅ Created: INVOICE_004_TRAP_UNCLEAR.pdf (Unclear total)")

def create_invoice_normal_2():
    """Another normal invoice"""
    doc = SimpleDocTemplate("test_documents/INVOICE_005_NORMAL.pdf", pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HEADER_COLOR,
        spaceAfter=30,
        alignment=1
    )
    
    elements.append(Paragraph("NEXUS CONSULTING", title_style))
    elements.append(Paragraph("Invoice #INV-2026-005", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    details = [
        ["Invoice Date:", "April 23, 2026"],
        ["Due Date:", "May 23, 2026"],
        ["Bill To:", "Innovation Labs"],
        ["Amount Due:", "$4,500 USD"],
    ]
    
    details_table = Table(details, colWidths=[2*inch, 3*inch])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), LIGHT_GRAY),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    
    elements.append(details_table)
    elements.append(Spacer(1, 0.3*inch))
    
    items = [
        ['Description', 'Quantity', 'Unit Price', 'Total'],
        ['Strategy Workshop', '2', '$1,500.00', '$3,000.00'],
        ['Follow-up Consulting', '5', '$300.00', '$1,500.00'],
    ]
    
    items_table = Table(items, colWidths=[2.5*inch, 1*inch, 1.5*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(items_table)
    elements.append(Spacer(1, 0.3*inch))
    
    total_style = ParagraphStyle(
        'Total',
        parent=styles['Normal'],
        fontSize=14,
        textColor=HEADER_COLOR,
        alignment=2
    )
    elements.append(Paragraph("<b>TOTAL: $4,500.00 USD</b>", total_style))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("Payment Terms: Net 45", styles['Normal']))
    
    doc.build(elements)
    print("✅ Created: INVOICE_005_NORMAL.pdf (Valid invoice)")

def create_contract_with_trap():
    """Contract without expiration date"""
    doc = SimpleDocTemplate("test_documents/CONTRACT_001_TRAP_NO_EXPIRY.pdf", pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=HEADER_COLOR,
        spaceAfter=20,
        alignment=1
    )
    
    elements.append(Paragraph("SERVICE AGREEMENT", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    agreement_text = """
    <b>This Service Agreement ("Agreement") is entered into as of April 25, 2026</b><br/>
    <b>BETWEEN:</b><br/>
    <b>Provider:</b> TechCore Solutions Inc. ("Provider")<br/>
    <b>Client:</b> Global Enterprises LLC ("Client")<br/>
    <br/>
    <b>1. SERVICES</b><br/>
    Provider agrees to provide software development, consulting, and support services 
    as outlined in Exhibit A, attached hereto and incorporated herein by reference.<br/>
    <br/>
    <b>2. COMPENSATION</b><br/>
    Client agrees to pay Provider the sum of $25,000 USD for the services described herein, 
    payable in accordance with the Payment Schedule outlined in Exhibit B.<br/>
    <br/>
    <b>3. TERM</b><br/>
    This Agreement becomes effective as of April 25, 2026. <b>NO EXPIRATION DATE IS SPECIFIED.</b> (TRAP)<br/>
    <br/>
    <b>4. CONFIDENTIALITY</b><br/>
    Both parties agree to maintain strict confidentiality regarding proprietary information 
    shared during the course of this engagement.<br/>
    <br/>
    <b>5. LIABILITY</b><br/>
    Provider's total liability shall not exceed the total fees paid by Client under this Agreement.<br/>
    <br/>
    <b>6. GOVERNING LAW</b><br/>
    This Agreement shall be governed by the laws of the State of Delaware.<br/>
    <br/>
    <b>SIGNATURES:</b><br/>
    <br/>
    Provider: ___________________________     Date: __________<br/>
    <br/>
    Client: ___________________________     Date: __________<br/>
    """
    
    elements.append(Paragraph(agreement_text, styles['Normal']))
    
    doc.build(elements)
    print("✅ Created: CONTRACT_001_TRAP_NO_EXPIRY.pdf (Missing expiration date)")

def create_contract_normal():
    """Normal contract with all required details"""
    doc = SimpleDocTemplate("test_documents/CONTRACT_002_NORMAL.pdf", pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=HEADER_COLOR,
        spaceAfter=20,
        alignment=1
    )
    
    elements.append(Paragraph("MASTER SERVICE AGREEMENT", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    agreement_text = """
    <b>This Master Service Agreement ("Agreement") is entered into as of April 25, 2026</b><br/>
    <b>BETWEEN:</b><br/>
    <b>Service Provider:</b> Digital Innovation Partners ("Provider")<br/>
    <b>Client:</b> Fortune 500 Corp ("Client")<br/>
    <br/>
    <b>1. SCOPE OF SERVICES</b><br/>
    Provider shall deliver cloud infrastructure, DevOps consulting, and 24/7 technical support 
    as detailed in the Statement of Work (SOW) attached as Exhibit A.<br/>
    <br/>
    <b>2. FEES AND PAYMENT TERMS</b><br/>
    Client agrees to pay Provider $50,000 USD annually, billed quarterly at $12,500 per quarter. 
    Payment is due within 30 days of invoice date.<br/>
    <br/>
    <b>3. TERM AND RENEWAL</b><br/>
    <b>Effective Date:</b> May 1, 2026<br/>
    <b>Initial Term:</b> 2 years (until April 30, 2028)<br/>
    <b>Auto-Renewal:</b> Agreement will automatically renew for successive 1-year periods 
    unless either party provides 90 days' written notice of non-renewal.<br/>
    <br/>
    <b>4. CONFIDENTIALITY</b><br/>
    Each party shall protect the other's confidential information with reasonable security measures.<br/>
    <br/>
    <b>5. LIMITATION OF LIABILITY</b><br/>
    Provider's maximum liability is limited to fees paid in the preceding 12 months.<br/>
    <br/>
    <b>6. GOVERNING LAW</b><br/>
    This Agreement is governed by Delaware law and the parties consent to jurisdiction in Delaware courts.<br/>
    <br/>
    <b>7. TERMINATION</b><br/>
    Either party may terminate with 30 days' written notice. Client remains responsible for 
    fees through the end of the current billing period.<br/>
    <br/>
    <b>AUTHORIZED SIGNATURES:</b><br/>
    <br/>
    Provider: ___________________________     Date: __________<br/>
    <br/>
    Client: ___________________________     Date: __________<br/>
    """
    
    elements.append(Paragraph(agreement_text, styles['Normal']))
    
    doc.build(elements)
    print("✅ Created: CONTRACT_002_NORMAL.pdf (Complete contract with expiration)")

def main():
    print("\n" + "="*60)
    print("ATLAS Test Document Generator")
    print("Creating 5 Invoices + 2 Contracts with Intentional Traps")
    print("="*60 + "\n")
    
    try:
        # Generate all documents
        create_invoice_with_trap_1()
        create_invoice_normal()
        create_invoice_with_trap_2()
        create_invoice_with_trap_3()
        create_invoice_normal_2()
        create_contract_with_trap()
        create_contract_normal()
        
        print("\n" + "="*60)
        print("✅ SUCCESS: All documents created in test_documents/")
        print("="*60)
        print("\nTRAP SUMMARY:")
        print("  📄 INVOICE_001: Math error (total should be $7,000, not $7,500)")
        print("  📄 INVOICE_003: Missing vendor name")
        print("  📄 INVOICE_004: Unclear/mismatched totals")
        print("  📄 CONTRACT_001: No expiration date specified")
        print("\n✅ Ready for Agent 1 (Vision Analyzer) testing\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
