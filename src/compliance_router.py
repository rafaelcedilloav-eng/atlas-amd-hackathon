import re
import logging
from typing import List, Dict, Any, Optional
from src.schemas import ComplianceResult, ComplianceFinding, ExtractedField

logger = logging.getLogger(__name__)

class MexicoComplianceEngine:
    PATTERNS = {
        "rfc": re.compile(r"[A-Z&Ñ]{3,4}[0-9]{6}[A-Z0-9]{3}"),
        "cre_permiso": re.compile(r"CRE/[0-9]{3,4}/[0-9]{4}"),
        "hidrocarburos_keywords": ["gasolina", "diesel", "combustible", "petroleo", "magna", "premium"],
    }

    def analyze(self, raw_text: str, xml_content: Optional[str] = None) -> List[ComplianceFinding]:
        findings = []
        rfcs = self.PATTERNS["rfc"].findall(raw_text)
        
        # Smart Check: Solo exigir RFC si el documento parece mexicano
        mex_keywords = ["mexico", "sat", "cfdi", "hacienda", "comprobante", "peso", "m.n.", "mxn"]
        is_explicitly_mexican = any(kw in raw_text.lower() for kw in mex_keywords)
        
        if not rfcs and is_explicitly_mexican:
            findings.append(ComplianceFinding(rule="RFC_MISSING", severity="HIGH", message="No se detectó RFC válido (México)", confidence=1.0, country="MX", article_ref="CFF Art. 29-A"))
        
        has_fuel = any(kw in raw_text.lower() for kw in self.PATTERNS["hidrocarburos_keywords"])
        if has_fuel and not self.PATTERNS["cre_permiso"].search(raw_text):
            findings.append(ComplianceFinding(rule="HIDROCARBUROS_NO_CRE", severity="HIGH", message="Venta de combustible sin permiso CRE", confidence=0.95, country="MX", article_ref="Ley de Hidrocarburos Art. 84"))
        return findings

class USAComplianceEngine:
    PATTERNS = { "ein": re.compile(r"\b\d{2}-\d{7}\b"), "boi_keywords": ["beneficial ownership", "fincen", "boi report"] }
    def analyze(self, raw_text: str, xml_content: Optional[str] = None) -> List[ComplianceFinding]:
        findings = []
        if not self.PATTERNS["ein"].search(raw_text):
            findings.append(ComplianceFinding(rule="EIN_MISSING", severity="MEDIUM", message="EIN not found (USA)", confidence=0.8, country="US"))
        if any(kw in raw_text.lower() for kw in self.PATTERNS["boi_keywords"]):
            findings.append(ComplianceFinding(rule="CTA_BOI_DETECTED", severity="INFO", message="Mención de cumplimiento CTA/BOI detectada", confidence=0.9, country="US", article_ref="Corporate Transparency Act"))
        return findings

class ChinaComplianceEngine:
    PATTERNS = { "uscc": re.compile(r"\b[0-9A-Z]{18}\b"), "fapiao": re.compile(r"发票|fapiao", re.I) }
    def analyze(self, raw_text: str, xml_content: Optional[str] = None) -> List[ComplianceFinding]:
        findings = []
        if not self.PATTERNS["uscc"].search(raw_text):
            findings.append(ComplianceFinding(rule="USCC_MISSING", severity="HIGH", message="Unified Social Credit Code missing (China)", confidence=0.9, country="CN"))
        if not self.PATTERNS["fapiao"].search(raw_text):
            findings.append(ComplianceFinding(rule="E_FAPIAO_MANDATE", severity="MEDIUM", message="Documento no identificado como e-Fapiao legal", confidence=0.7, country="CN"))
        return findings

class BrazilComplianceEngine:
    PATTERNS = { "cnpj": re.compile(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}"), "pix": re.compile(r"PIX|QR Code", re.I) }
    def analyze(self, raw_text: str, xml_content: Optional[str] = None) -> List[ComplianceFinding]:
        findings = []
        if not self.PATTERNS["cnpj"].search(raw_text):
            findings.append(ComplianceFinding(rule="CNPJ_MISSING", severity="HIGH", message="CNPJ não encontrado (Brasil)", confidence=0.95, country="BR"))
        return findings

class UKComplianceEngine:
    PATTERNS = { "vat": re.compile(r"GB\s*[0-9]{9}"), "mtd": re.compile(r"MTD|Making Tax Digital", re.I) }
    def analyze(self, raw_text: str, xml_content: Optional[str] = None) -> List[ComplianceFinding]:
        findings = []
        if not self.PATTERNS["vat"].search(raw_text):
            findings.append(ComplianceFinding(rule="VAT_GB_MISSING", severity="MEDIUM", message="VAT Registration Number (GB) missing", confidence=0.9, country="UK"))
        return findings

class GermanyComplianceEngine:
    PATTERNS = { "vat": re.compile(r"DE\s*[0-9]{9}"), "zugferd": re.compile(r"ZUGFeRD|XRechnung", re.I) }
    def analyze(self, raw_text: str, xml_content: Optional[str] = None) -> List[ComplianceFinding]:
        findings = []
        if not self.PATTERNS["vat"].search(raw_text):
            findings.append(ComplianceFinding(rule="USTIDNR_MISSING", severity="HIGH", message="USt-IdNr. fehlt (Deutschland)", confidence=0.95, country="DE"))
        return findings

class FranceComplianceEngine:
    PATTERNS = { "siren": re.compile(r"\b\d{9}\b"), "siret": re.compile(r"\b\d{14}\b") }
    def analyze(self, raw_text: str, xml_content: Optional[str] = None) -> List[ComplianceFinding]:
        findings = []
        if not self.PATTERNS["siren"].search(raw_text) and not self.PATTERNS["siret"].search(raw_text):
            findings.append(ComplianceFinding(rule="SIREN_SIRET_MISSING", severity="HIGH", message="SIREN/SIRET non trouvé (France)", confidence=0.9, country="FR"))
        return findings

class IndiaComplianceEngine:
    PATTERNS = { "gstin": re.compile(r"\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}"), "irn": re.compile(r"IRN|Invoice Reference Number", re.I) }
    def analyze(self, raw_text: str, xml_content: Optional[str] = None) -> List[ComplianceFinding]:
        findings = []
        if not self.PATTERNS["gstin"].search(raw_text):
            findings.append(ComplianceFinding(rule="GSTIN_MISSING", severity="CRITICAL", message="GSTIN not found (India)", confidence=1.0, country="IN"))
        return findings

class SpainComplianceEngine:
    PATTERNS = { "nif": re.compile(r"\b[A-HJ-NP-SU-W][0-9]{7}[0-9A-J]\b"), "sii": re.compile(r"SII|Suministro Inmediato", re.I) }
    def analyze(self, raw_text: str, xml_content: Optional[str] = None) -> List[ComplianceFinding]:
        findings = []
        if not self.PATTERNS["nif"].search(raw_text):
            findings.append(ComplianceFinding(rule="NIF_CIF_MISSING", severity="HIGH", message="NIF/CIF no encontrado (España)", confidence=0.9, country="ES"))
        return findings

class JapanComplianceEngine:
    PATTERNS = { "corp_num": re.compile(r"\b\d{13}\b"), "qualified": re.compile(r"適格請求書|Qualified Invoice", re.I) }
    def analyze(self, raw_text: str, xml_content: Optional[str] = None) -> List[ComplianceFinding]:
        findings = []
        if not self.PATTERNS["corp_num"].search(raw_text):
            findings.append(ComplianceFinding(rule="CORP_NUMBER_MISSING", severity="MEDIUM", message="Corporate Number missing (Japan)", confidence=0.8, country="JP"))
        return findings

class CanadaComplianceEngine:
    PATTERNS = { "bn": re.compile(r"\d{9}RT\d{4}"), "dst": re.compile(r"Digital Services Tax|DST", re.I) }
    def analyze(self, raw_text: str, xml_content: Optional[str] = None) -> List[ComplianceFinding]:
        findings = []
        if not self.PATTERNS["bn"].search(raw_text):
            findings.append(ComplianceFinding(rule="BN_GST_MISSING", severity="HIGH", message="Business Number / GST account missing (Canada)", confidence=0.9, country="CA"))
        return findings

def run_compliance_check(raw_text: str, xml_content: Optional[str] = None, extracted_fields: Dict[str, ExtractedField] = None, filename: str = "") -> ComplianceResult:
    """
    Router principal que detecta país y ejecuta el engine correspondiente entre 11 jurisdicciones.
    """
    # Detección de país (Heurística ATLAS v2.0)
    country_detected = "MX"
    text_upper = raw_text.upper()
    
    if any(k in text_upper for k in ["USA", "IRS", "EIN", "UNITED STATES"]): country_detected = "US"
    elif any(k in text_upper for k in ["CHINA", "PRC", "USCC", "FAPIAO"]): country_detected = "CN"
    elif any(k in text_upper for k in ["BRASIL", "BRAZIL", "CNPJ", "NF-E"]): country_detected = "BR"
    elif any(k in text_upper for k in ["UNITED KINGDOM", "HMRC", "VAT REG", "GB"]): country_detected = "UK"
    elif any(k in text_upper for k in ["GERMANY", "DEUTSCHLAND", "UST-IDNR"]): country_detected = "DE"
    elif any(k in text_upper for k in ["FRANCE", "SIREN", "SIRET"]): country_detected = "FR"
    elif any(k in text_upper for k in ["INDIA", "GSTIN", "IRN"]): country_detected = "IN"
    elif any(k in text_upper for k in ["ESPAÑA", "SPAIN", "NIF", "CIF"]): country_detected = "ES"
    elif any(k in text_upper for k in ["JAPAN", "CORPORATE NUMBER", "適格請求書"]): country_detected = "JP"
    elif any(k in text_upper for k in ["CANADA", "BUSINESS NUMBER", "GST/HST"]): country_detected = "CA"
    
    engines = {
        "MX": MexicoComplianceEngine(), "US": USAComplianceEngine(), "CN": ChinaComplianceEngine(),
        "BR": BrazilComplianceEngine(), "UK": UKComplianceEngine(), "DE": GermanyComplianceEngine(),
        "FR": FranceComplianceEngine(), "IN": IndiaComplianceEngine(), "ES": SpainComplianceEngine(),
        "JP": JapanComplianceEngine(), "CA": CanadaComplianceEngine()
    }
    
    engine = engines.get(country_detected, MexicoComplianceEngine())
    findings = engine.analyze(raw_text, xml_content)
    
    cross_border_flags = []
    if "IMPORT" in text_upper or "EXPORT" in text_upper: cross_border_flags.append("INCOTERMS_CHECK_REQUIRED")

    score = max(0.0, 1.0 - (len([f for f in findings if f.severity in ["HIGH", "CRITICAL"]]) * 0.2))
    
    return ComplianceResult(
        country_detected=country_detected,
        country_confidence=0.9,
        findings=findings,
        compliance_score=score,
        raw_extracts={"filename": filename},
        cross_border_flags=cross_border_flags
    )
