"""
ATLAS Report Generator v3.0 FINAL
Generador de reportes PDF de grado gubernamental para AMD MI300X Clusters.
Optimizado por Kimi-K2 + Qwen Logic Joint Audit.
"""
from fpdf import FPDF
from datetime import datetime
from typing import Dict, List, Any
import os

class AtlasReportGenerator(FPDF):
    """Generador de reportes con trazabilidad UUIDv7 y branding ATLAS"""
    
    def __init__(self, audit_data: Dict[str, Any]):
        super().__init__()
        self.audit_data = audit_data
        self.audit_id = audit_data.get('document_id', 'Unknown')
        self.set_title(f"ATLAS_Audit_{self.audit_id[:8]}")
        self.set_author("ATLAS Framework v3.0")
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        # Banner de clasificación superior (AMD Red)
        self.set_fill_color(237, 28, 36) 
        self.rect(0, 0, 210, 8, 'F')
        self.set_xy(0, 1)
        self.set_font('Arial', 'B', 7)
        self.set_text_color(255, 255, 255)
        self.cell(210, 6, "CONFIDENTIAL // INTERNAL FORENSICS // AMD MI300X CLUSTER", 0, 1, 'C')
        self.set_text_color(0, 0, 0)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.line(10, self.get_y(), 200, self.get_y())
        self.cell(0, 10, f"ATLAS Forensic Traceability ID: {self.audit_id}", 0, 0, 'L')
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, 'R')

    def generate(self) -> bytes:
        self.add_page()
        
        # Logo placeholder
        self.set_fill_color(0, 0, 0)
        self.rect(10, 15, 30, 10, 'F')
        self.set_xy(10, 15)
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 10)
        self.cell(30, 10, "ATLAS", 0, 1, 'C')
        self.set_text_color(0, 0, 0)
        
        # Título Principal
        self.ln(10)
        self.set_font('Arial', 'B', 22)
        self.cell(0, 15, "FINANCIAL FORENSICS REPORT", 0, 1, 'L')
        self.set_font('Arial', '', 12)
        self.cell(0, 8, f"ATLAS Intel Framework v3.0.0", 0, 1, 'L')
        self.ln(5)
        
        # Metadatos del Reporte
        self.set_fill_color(245, 245, 245)
        self.set_font('Arial', 'B', 9)
        self.cell(40, 8, "Audit UUIDv7:", 1, 0, 'L', True)
        self.set_font('Arial', '', 9)
        self.cell(0, 8, self.audit_id, 1, 1, 'L')
        
        self.set_font('Arial', 'B', 9)
        self.cell(40, 8, "Execution Date:", 1, 0, 'L', True)
        self.set_font('Arial', '', 9)
        self.cell(0, 8, datetime.now().isoformat(), 1, 1, 'L')
        
        self.set_font('Arial', 'B', 9)
        self.cell(40, 8, "GPU Infrastructure:", 1, 0, 'L', True)
        self.set_font('Arial', '', 9)
        self.cell(0, 8, "AMD MI300X (8-GPU Config)", 1, 1, 'L')
        
        self.ln(10)
        
        # Resumen Ejecutivo
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, "1. EXECUTIVE SUMMARY", 0, 1, 'L')
        self.line(10, self.get_y(), 60, self.get_y())
        self.ln(2)
        
        self.set_font('Arial', '', 10)
        explanation = self.audit_data.get('explanation', {})
        summary = explanation.get('summary', "No executive summary available for this audit.")
        self.multi_cell(0, 5, summary)
        self.ln(5)
        
        # Hallazgos Forenses
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, "2. COMPLIANCE & RISK ANALYSIS", 0, 1, 'L')
        self.line(10, self.get_y(), 80, self.get_y())
        self.ln(5)
        
        compliance = self.audit_data.get('compliance', {})
        findings = compliance.get('findings', [])
        
        if not findings:
            self.set_font('Arial', 'I', 10)
            self.cell(0, 10, "No compliance violations or fiscal risks detected.", 0, 1, 'L')
        else:
            self.set_font('Arial', 'B', 9)
            self.set_fill_color(230, 230, 230)
            self.cell(30, 8, "Country", 1, 0, 'C', True)
            self.cell(110, 8, "Finding Description", 1, 0, 'C', True)
            self.cell(25, 8, "Severity", 1, 0, 'C', True)
            self.cell(25, 8, "Status", 1, 1, 'C', True)
            
            self.set_font('Arial', '', 8)
            for f in findings:
                self.cell(30, 8, compliance.get('country_detected', 'N/A'), 1, 0, 'C')
                self.cell(110, 8, f.get('description', 'N/A')[:65], 1, 0, 'L')
                self.cell(25, 8, f.get('severity', 'N/A'), 1, 0, 'C')
                self.cell(25, 8, "FLAGGED", 1, 1, 'C')
        
        self.ln(10)
        
        # Razonamiento (CoT)
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, "3. FORENSIC REASONING CHAIN (CoT)", 0, 1, 'L')
        self.line(10, self.get_y(), 90, self.get_y())
        self.ln(5)
        
        reasoning = self.audit_data.get('reasoning', {})
        chain_steps = reasoning.get('reasoning_chain', [])
        
        self.set_font('Courier', '', 8)
        self.set_fill_color(250, 250, 250)
        
        chain_text = ""
        for i, step in enumerate(chain_steps):
            chain_text += f"STEP {i+1} [{step.get('agent', 'AI')}]: {step.get('thought', '')}\n"
        
        if not chain_text:
            chain_text = "No reasoning chain recorded for this audit."
            
        self.multi_cell(0, 4, chain_text, 1, 'L', True)
        
        return self.output(dest='S').encode('latin1')
