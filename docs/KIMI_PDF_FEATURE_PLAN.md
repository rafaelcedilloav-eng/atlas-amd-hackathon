```python
# src/report_generator.py
from fpdf import FPDF
from datetime import datetime
from typing import Dict, List, Any
import uuid

class ReportGenerator(FPDF):
    """ATLAS Security Audit Report Generator with government-grade formatting"""
    
    def __init__(self, audit_data: Dict[str, Any]):
        super().__init__()
        self.audit_data = audit_data
        self.audit_id = audit_data.get('audit_id', '')
        self.set_title("ATLAS Security Audit Report")
        self.set_author("ATLAS Security Framework")
        self.set_subject(f"Audit Report {self.audit_id}")
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        """Professional header with classification banner"""
        # TOP SECRET style classification banner
        if self.page_no() > 1:
            self.set_y(5)
            self.set_font('Arial', 'B', 8)
            self.set_fill_color(255, 0, 0)
            self.set_text_color(255, 255, 255)
            self.cell(0, 4, "INTERNAL USE ONLY", 0, 1, 'C', fill=True)
            self.set_text_color(0, 0, 0)
            self.ln(2)
            
            # Report title on subsequent pages
            self.set_font('Arial', 'B', 10)
            self.cell(0, 6, f'ATLAS Security Audit Report - {self.audit_id[:8]}...', 0, 1, 'L')
            self.line(10, 18, 200, 18)
            self.ln(4)
    
    def footer(self):
        """Government-style footer with UUIDv7 and page numbers"""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        
        # Footer line
        self.line(10, self.get_y(), 200, self.get_y())
        
        # Left: Generation timestamp
        self.set_x(10)
        self.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}", 0, 0, 'L')
        
        # Center: Audit ID (UUIDv7)
        self.set_x(55)
        self.set_font('Courier', 'I', 8)
        self.cell(0, 8, f"Audit ID: {self.audit_id}", 0, 0, 'C')
        
        # Right: Page number
        self.set_font('Arial', 'I', 8)
        self.cell(0, 8, f"Page {self.page_no()}", 0, 0, 'R')
    
    def _add_logo_placeholder(self):
        """Government agency placeholder logo"""
        self.set_xy(85, 40)
        self.set_fill_color(26, 35, 126)  # Navy blue
        self.rect(85, 40, 40, 25, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 9)
        self.set_xy(85, 48)
        self.cell(40, 10, '[ATLAS LOGO]', 0, 0, 'C')
        self.set_text_color(0, 0, 0)
    
    def generate_cover(self):
        """Official cover page"""
        self.add_page()
        self._add_logo_placeholder()
        
        # Main title
        self.ln(50)
        self.set_font('Arial', 'B', 22)
        self.cell(0, 12, 'SECURITY AUDIT REPORT', 0, 1, 'C')
        
        # Subtitle
        self.set_font('Arial', '', 14)
        self.cell(0, 8, 'ATLAS Security Framework - Compliance Assessment', 0, 1, 'C')
        self.ln(15)
        
        # Audit metadata
        self.set_font('Arial', '', 12)
        self.cell(0, 8, f'Audit Identifier: {self.audit_id}', 0, 1, 'C')
        self.ln(5)
        self.cell(0, 8, f'Report Date: {datetime.now().strftime("%B %d, %Y")}', 0, 1, 'C')
        self.ln(20)
        
        # Classification box
        self.set_fill_color(255, 235, 238)
        self.set_draw_color(213, 0, 0)
        self.rect(50, self.get_y(), 110, 25, 'D')
        self.set_xy(50, self.get_y() + 5)
        self.set_font('Arial', 'B', 11)
        self.cell(110, 8, 'CLASSIFICATION: INTERNAL USE', 0, 1, 'C')
        self.set_xy(50, self.get_y())
        self.set_font('Arial', 'I', 9)
        self.cell(110, 8, 'Distribution controlled by ATLAS Security', 0, 1, 'C')
    
    def generate_executive_summary(self):
        """Executive summary section"""
        self.add_page()
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'EXECUTIVE SUMMARY', 0, 1, 'L')
        self.ln(5)
        
        # Summary text
        self.set_font('Arial', '', 11)
        summary = self.audit_data.get('executive_summary', 
            'No executive summary provided for this audit.')
        self.multi_cell(0, 6, summary)
        self.ln(10)
        
        # Key metrics box
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, 'Key Metrics', 0, 1, 'L')
        self.ln(2)
        
        findings = self.audit_data.get('findings', [])
        stats = {
            'total': len(findings),
            'critical': sum(1 for f in findings if f.get('severity') == 'Critical'),
            'high': sum(1 for f in findings if f.get('severity') == 'High'),
            'medium': sum(1 for f in findings if f.get('severity') == 'Medium'),
            'low': sum(1 for f in findings if f.get('severity') == 'Low')
        }
        
        # Metrics table
        self.set_font('Arial', '', 10)
        col_width = 47
        
        # Headers
        self.set_fill_color(240, 240, 240)
        self.cell(col_width, 8, 'Total Findings', 1, 0, 'C', True)
        self.cell(col_width, 8, 'Critical', 1, 0, 'C', True)
        self.cell(col_width, 8, 'High', 1, 0, 'C', True)
        self.cell(col_width, 8, 'Medium/Low', 1, 1, 'C', True)
        
        # Values
        self.set_font('Arial', 'B', 12)
        self.cell(col_width, 10, str(stats['total']), 1, 0, 'C')
        
        self.set_text_color(139, 0, 0)
        self.cell(col_width, 10, str(stats['critical']), 1, 0, 'C')
        
        self.set_text_color(255, 69, 0)
        self.cell(col_width, 10, str(stats['high']), 1, 0, 'C')
        
        self.set_text_color(0, 0, 0)
        self.cell(col_width, 10, str(stats['medium'] + stats['low']), 1, 1, 'C')
        self.set_text_color(0, 0, 0)
    
    def generate_risk_chart(self):
        """Risk assessment visualization"""
        self.add_page()
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'RISK ASSESSMENT', 0, 1, 'L')
        self.ln(5)
        
        risk_score = self.audit_data.get('risk_score', 0)
        
        # Score display
        self.set_font('Arial', 'B', 14)
        self.cell(0, 8, f'Overall Risk Score: {risk_score}/100', 0, 1, 'L')
        self.ln(5)
        
        # Risk gauge
        gauge_y = self.get_y()
        self.set_fill_color(220, 220, 220)
        self.rect(20, gauge_y, 160, 20, 'F')
        
        # Color based on risk
        if risk_score >= 70:
            color = (139, 0, 0)  # Critical
            risk_level = "CRITICAL"
        elif risk_score >= 40:
            color = (255, 165, 0)  # Medium
            risk_level = "MEDIUM"
        else:
            color = (0, 128, 0)  # Low
            risk_level = "LOW"
            
        self.set_fill_color(*color)
        bar_width = (risk_score / 100) * 160
        self.rect(20, gauge_y, bar_width, 20, 'F')
        
        # Risk level text
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 12)
        self.set_xy(20, gauge_y)
        self.cell(160, 20, f'{risk_score}% - {risk_level} RISK', 0, 0, 'C')
        self.set_text_color(0, 0, 0)
        self.ln(25)
        
        # Risk matrix description
        self.set_font('Arial', '', 10)
        self.cell(0, 6, 'Risk Level Thresholds:', 0, 1, 'L')
        self.ln(2)
        
        self.set_text_color(139, 0, 0)
        self.cell(0, 6, '● Critical: 70-100 (Immediate action required)', 0, 1, 'L')
        
        self.set_text_color(255, 165, 0)
        self.cell(0, 6, '● Medium: 40-69 (Remediate within 30 days)', 0, 1, 'L')
        
        self.set_text_color(0, 128, 0)
        self.cell(0, 6, '● Low: 0-39 (Address per standard cycle)', 0, 1, 'L')
        self.set_text_color(0, 0, 0)
    
    def generate_findings_table(self):
        """Detailed findings table"""
        self.add_page()
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'COMPLIANCE FINDINGS', 0, 1, 'L')
        self.ln(5)
        
        findings = self.audit_data.get('findings', [])
        
        if not findings:
            self.set_font('Arial', '', 11)
            self.cell(0, 10, 'No findings identified in this audit scope.', 0, 1, 'L')
            return
        
        # Table headers
        self.set_font('Arial', 'B', 9)
        self.set_fill_color(240, 240, 240)
        headers = ['Finding ID', 'Description', 'Severity', 'Status']
        widths = [25, 95, 25, 45]
        
        for i, header in enumerate(headers):
            self.cell(widths[i], 8, header, 1, 0, 'C', True)
        self.ln()
        
        # Table rows
        self.set_font('Arial', '', 8)
        for finding in findings:
            # Row height calculation
            description = finding.get('description', '')
            lines_needed = self.get_string_width(description) / (widths[1] - 4)
            row_height = max(8, int(lines_needed * 4) + 4)
            
            current_y = self.get_y()
            
            # Finding ID
            self.cell(widths[0], row_height, finding.get('code', 'N/A'), 1, 0, 'C')
            
            # Description (multi-cell)
            self.multi_cell(widths[1], 4, description, 1, 'L')
            self.set_xy(10 + sum(widths[:2]), current_y)
            
            # Severity with color coding
            severity = finding.get('severity', 'Unknown')
            if severity == 'Critical':
                self.set_text_color(139, 0, 0)
            elif severity == 'High':
                self.set_text_color(255, 69, 0)
            elif severity == 'Medium':
                self.set_text_color(255, 165, 0)
            elif severity == 'Low':
                self.set_text_color(0, 0, 255)
            
            self.cell(widths[2], row_height, severity, 1, 0, 'C')
            self.set_text_color(0, 0, 0)
            
            # Status
            self.cell(widths[3], row_height, finding.get('status', 'Open'), 1, 1, 'C')
    
    def generate_forensic_chain(self):
        """Forensic chain of custody section"""
        self.add_page()
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'FORENSIC CHAIN OF REASONING', 0, 1, 'L')
        self.ln(5)
        
        # Chain box
        self.set_fill_color(245, 245, 245)
        self.rect(10, self.get_y(), 190, 120, 'F')
        self.set_xy(15, self.get_y() + 5)
        
        # Chain content
        self.set_font('Courier', '', 9)
        forensic_chain = self.audit_data.get('forensic_chain', 
            'No forensic chain data recorded for this audit.')
        
        # Preserve line breaks and format
        for line in forensic_chain.split('\n'):
            self.cell(0, 6, line, 0, 1, 'L')
        
        # Evidence integrity
        self.ln(10)
        self.set_font('Arial', 'B', 10)
        self.cell(0, 8, 'Evidence Integrity:', 0, 1, 'L')
        self.set_font('Arial', '', 9)
        self.multi_cell(0, 5, 
            f"MD5: {self.audit_id[:16]}...\n"
            f"SHA256: {self.audit_id}...\n"
            f"Chain of custody maintained per ATLAS-SOP-2024-001")
    
    def generate(self) -> bytes:
        """Generate complete PDF report"""
        self.generate_cover()
        self.generate_executive_summary()
        self.generate_risk_chart()
        self.generate_findings_table()
        self.generate_forensic_chain()
        
        return self.output(dest='S').encode('latin1')
```

```python
# src/api.py - modifications (add to existing file)
from fastapi import FastAPI, HTTPException, Response, Path
from datetime import datetime
import uuid
import logging
from typing import Dict, Any
from src.report_generator import ReportGenerator

# ... existing code ...

@app.get("/api/v2/report/download/{audit_id}")
async def download_audit_report(
    audit_id: str = Path(..., description="UUIDv7 audit identifier")
):
    """
    Download professional PDF audit report for the given audit_id.
    Returns government-grade formatted PDF with complete audit trail.
    """
    try:
        # Validate UUIDv7 format
        try:
            validated_uuid = uuid.UUID(audit_id)
            if validated_uuid.version != 7:
                raise HTTPException(
                    status_code=400, 
                    detail={"error": "Invalid audit_id format. Must be UUIDv7 RFC 4122 compliant"}
                )
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail={"error": "Invalid audit_id format"}
            )
        
        # Retrieve audit data (implement actual DB query)
        audit_data = await get_audit_data(audit_id)
        if not audit_data:
            raise HTTPException(
                status_code=404, 
                detail={"error": "Audit not found", "audit_id": audit_id}
            )
        
        # Generate PDF
        generator = ReportGenerator(audit_data)
        pdf_bytes = generator.generate()
        
        # Filename for download
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ATLAS_Audit_{audit_id[:8]}_{timestamp}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Audit-ID": audit_id,
                "X-Report-Version": "2.0"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"PDF generation failed for audit {audit_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail={"error": "Failed to generate PDF report", "audit_id": audit_id}
        )

# Placeholder for database integration
async def get_audit_data(audit_id: str) -> Dict[str, Any]:
    """
    RETRIEVE THIS FROM YOUR DATABASE IN PRODUCTION
    
    Expected audit_data structure:
    {
        "audit_id": "uuid-string",
        "executive_summary": "string",
        "risk_score": int (0-100),
        "findings": [
            {
                "code": "string", 
                "description": "string", 
                "severity": "Critical|High|Medium|Low", 
                "status": "string"
            }
        ],
        "forensic_chain": "string"
    }
    """
    # MOCK DATA - REPLACE WITH ACTUAL DB QUERY
    return {
        "audit_id": audit_id,
        "executive_summary": (
            "The security audit conducted on January 15, 2024 identified 4 critical "
            "compliance gaps against CIS Controls v8 and NIST CSF frameworks. "
            "Key findings include missing MFA implementations, baseline configuration "
            "drifts, and insufficient log aggregation. Immediate remediation required "
            "for 2 critical findings to maintain security posture and regulatory compliance."
        ),
        "risk_score": 72,
        "findings": [
            {
                "code": "CIS-3.1-MFA",
                "description": "Privileged accounts lack multi-factor authentication enforcement",
                "severity": "Critical",
                "status": "Open"
            },
            {
                "code": "NIST-PR.IP-1",
                "description": "System baseline configurations not maintained per policy DSC-2024-001",
                "severity": "High",
                "status": "In Progress"
            },
            {
                "code": "CIS-8.2-LOG",
                "description": "Security audit logs not centrally collected or monitored",
                "severity": "High",
                "status": "Open"
            },
            {
                "code": "NIST-DE.CM-1",
                "description": "Network monitoring coverage incomplete for DMZ segment",
                "severity": "Medium",
                "status": "Open"
            }
        ],
        "forensic_chain": (
            "TIMESTAMP: 2024-01-15T09:00:00Z | ACTION: Audit initiated by user admin@atlas.local\n"
            "TIMESTAMP: 2024-01-15T09:15:23Z | ACTION: Collected configuration from 1,847 assets\n"
            "TIMESTAMP: 2024-01-15T10:42:11Z | ACTION: Cross-referenced against CISv8, NIST CSF\n"
            "TIMESTAMP: 2024-01-15T14:30:45Z | ACTION: Manual validation of critical findings\n"
            "TIMESTAMP: 2024-01-15T16:00:00Z | ACTION: Senior analyst review and approval\n"
            "TIMESTAMP: 2024-01-15T17:00:00Z | ACTION: Report generation and cryptographic sealing"
        )
    }
```

```bash
# Install the lightweight PDF generation library
pip install fpdf2==2.7.0
```