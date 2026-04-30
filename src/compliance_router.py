"""
ATLAS Compliance Router — 11 Country Engines
Regex + keyword detection. No LLM used for detection, only for explanation.
Inserted between VisionExtractor and ReasoningAgent in the orchestrator.
"""
import re
import logging
from typing import Dict, List, Optional, Tuple

from src.schemas import ComplianceFinding, ComplianceResult

logger = logging.getLogger(__name__)


class ComplianceRouter:
    """Detects the document country and routes to the correct engine."""

    COUNTRY_PATTERNS = {
        "MX": {
            "ids": [re.compile(r"[A-Z&Ñ]{3,4}[0-9]{6}[A-Z0-9]{3}")],
            "keywords": ["cfdi", "sat", "mexico", "méxico", "rfc", "iva 16%", "pesos", "mxn"],
            "formats": [".xml"],
        },
        "US": {
            "ids": [re.compile(r"\b\d{2}-\d{7}\b")],
            "keywords": ["irs", "ein", "usa", "united states", "1099", "w-9", "usd", "fincen", "boi"],
            "formats": [],
        },
        "CN": {
            "ids": [re.compile(r"[0-9A-Z]{18}")],
            "keywords": ["fapiao", "china", "增值税", "发票", "rmb", "yuan", "golden tax"],
            "formats": [".xml"],
        },
        "BR": {
            "ids": [re.compile(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}")],
            "keywords": ["cnpj", "brasil", "brazil", "nf-e", "sped", "icms", "pix", "reais"],
            "formats": [".xml"],
        },
        "GB": {
            "ids": [re.compile(r"GB\d{9}")],
            "keywords": ["hmrc", "uk", "united kingdom", "vat", "mtd", "gbp", "pound"],
            "formats": [],
        },
        "DE": {
            "ids": [re.compile(r"DE\d{9}")],
            "keywords": ["zugferd", "xrechnung", "germany", "deutschland", "ust-idnr", "eur", "gobd"],
            "formats": [".xml"],
        },
        "FR": {
            "ids": [re.compile(r"\b\d{9}\b"), re.compile(r"\b\d{14}\b")],
            "keywords": ["siren", "siret", "france", "francia", "factur-x", "ppf", "eur", "tva"],
            "formats": [".xml"],
        },
        "IN": {
            "ids": [re.compile(r"\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}")],
            "keywords": ["gstin", "india", "gst", "irn", "eway", "rupee", "inr"],
            "formats": [".json"],
        },
        "ES": {
            "ids": [re.compile(r"[A-Z]\d{8}\b|\b\d{8}[A-Z]")],
            "keywords": ["nif", "cif", "spain", "españa", "sii", "aeat", "eur", "iva"],
            "formats": [],
        },
        "JP": {
            "ids": [re.compile(r"\b\d{13}\b")],
            "keywords": ["japan", "japon", "jct", "consumption tax", "適格請求書", "yen", "jpy"],
            "formats": [],
        },
        "CA": {
            "ids": [re.compile(r"\d{9}RC\d{4}")],
            "keywords": ["canada", "cra", "gst/hst", "business number", "peppol", "cad", "dst"],
            "formats": [],
        },
    }

    def detect_country(self, raw_text: str, filename: str = "") -> Tuple[str, float]:
        text_lower = raw_text.lower()
        scores: Dict[str, float] = {}

        for country, patterns in self.COUNTRY_PATTERNS.items():
            score = 0.0
            for id_pattern in patterns["ids"]:
                score += len(id_pattern.findall(raw_text)) * 0.4
            for kw in patterns["keywords"]:
                if kw.lower() in text_lower:
                    score += 0.15
            for fmt in patterns["formats"]:
                if fmt in filename.lower():
                    score += 0.1
            scores[country] = min(score, 1.0)

        if not scores:
            return "UNKNOWN", 0.0
        best = max(scores, key=scores.get)  # type: ignore[arg-type]
        best_score = scores[best]
        if best_score < 0.15:
            return "UNKNOWN", best_score
        return best, best_score


class BaseComplianceEngine:
    def __init__(self, country_code: str):
        self.country_code = country_code
        self.findings: List[ComplianceFinding] = []

    def analyze(self, raw_text: str, xml_content: Optional[str] = None,
                extracted_fields: Optional[Dict] = None) -> ComplianceResult:
        raise NotImplementedError

    def _add(self, rule: str, severity: str, message: str,
             confidence: float, article_ref: Optional[str] = None):
        self.findings.append(ComplianceFinding(
            rule=rule, severity=severity, message=message,
            confidence=confidence, country=self.country_code,
            article_ref=article_ref,
        ))

    def _build(self, raw_extracts: Dict, cross_flags: Optional[List[str]] = None) -> ComplianceResult:
        score = max(0.0, 1.0 - len(self.findings) * 0.15)
        return ComplianceResult(
            country_detected=self.country_code,
            country_confidence=1.0,
            findings=self.findings,
            compliance_score=score,
            raw_extracts=raw_extracts,
            cross_border_flags=cross_flags or [],
        )


class MexicoEngine(BaseComplianceEngine):
    def __init__(self):
        super().__init__("MX")
        self._rfc    = re.compile(r"[A-Z&Ñ]{3,4}[0-9]{6}[A-Z0-9]{3}")
        self._cre    = re.compile(r"CRE/[0-9]{3,4}/[0-9]{4}")
        self._uuid   = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
        self._fuel   = ["gasolina", "diesel", "combustible", "petróleo", "magna", "premium", "gas lp"]
        self._platf  = ["uber", "airbnb", "mercado libre", "amazon", "rappi", "didi"]

    def analyze(self, raw_text: str, xml_content: Optional[str] = None,
                extracted_fields: Optional[Dict] = None) -> ComplianceResult:
        self.findings = []
        t = raw_text.lower()
        extracts: Dict = {}

        rfcs = self._rfc.findall(raw_text)
        extracts["rfcs"] = rfcs
        if not rfcs:
            self._add("RFC_MISSING", "CRITICAL",
                      "No se detectó RFC válido. El SAT requiere RFC para validez fiscal.",
                      1.0, "Art. 29-A CFF")

        has_fuel = any(k in t for k in self._fuel)
        cre_m = self._cre.search(raw_text)
        extracts["cre_permits"] = [cre_m.group()] if cre_m else []
        if has_fuel and not cre_m:
            self._add("HIDROCARBUROS_NO_CRE", "HIGH",
                      "Venta de combustible detectada sin permiso CRE válido.",
                      0.95, "Complemento Hidrocarburos CFDI 4.0")

        uuids = self._uuid.findall(raw_text)
        extracts["cfdi_uuids"] = uuids
        if not uuids and xml_content and "UUID" not in xml_content:
            self._add("CFDI_UUID_MISSING", "HIGH",
                      "No se detectó UUID del CFDI. Cada CFDI debe tener un UUID único del SAT.",
                      0.9, "CFDI 4.0 Spec")

        if any(k in t for k in self._platf) and "retención" not in t and "2.5%" not in t:
            self._add("PLATAFORMA_SIN_RETENCION", "MEDIUM",
                      "Operación de plataforma digital sin retención del 2.5% ISR.",
                      0.8, "Art. 135 LISR reforma 2024")

        if xml_content and extracted_fields:
            xml_total = self._xml_total(xml_content)
            vis_total = self._vis_total(raw_text, extracted_fields)
            if xml_total and vis_total and abs(xml_total - vis_total) > 0.01:
                self._add("XML_VISUAL_MISMATCH", "CRITICAL",
                          f"Discrepancia: XML=${xml_total:.2f} vs Visual=${vis_total:.2f}. El XML es la fuente legal.",
                          1.0, "CFDI 4.0 - XML es fuente de verdad")

        return self._build(extracts)

    def _xml_total(self, xml: str) -> Optional[float]:
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(xml)
            for attr in ["Total", "total", "Importe"]:
                val = root.get(attr) or root.find(f".//{{{''}}}{attr}")
                if val is not None:
                    return float(val.text if hasattr(val, "text") else val)
        except Exception:
            pass
        return None

    def _vis_total(self, raw_text: str, fields: Dict) -> Optional[float]:
        f = fields.get("total_amount") or fields.get("total")
        if f and hasattr(f, "value") and f.value:
            try:
                return float(str(f.value).replace(",", "").replace("$", ""))
            except (ValueError, TypeError):
                pass
        m = re.search(r"Total[\s:]*[$]?\s*([\d,]+\.\d{2})", raw_text, re.IGNORECASE)
        if m:
            return float(m.group(1).replace(",", ""))
        return None


class USAEngine(BaseComplianceEngine):
    def __init__(self):
        super().__init__("US")
        self._ein = re.compile(r"\b\d{2}-\d{7}\b")

    def analyze(self, raw_text: str, xml_content: Optional[str] = None,
                extracted_fields: Optional[Dict] = None) -> ComplianceResult:
        self.findings = []
        t = raw_text.lower()
        extracts: Dict = {}

        if not any(k in t for k in ["fincen", "boi", "beneficial owner", "transparency act"]):
            self._add("CTA_BOI_MISSING", "MEDIUM",
                      "No se detecta evidencia de reporte BOI a FinCEN. Obligatorio desde enero 2024.",
                      0.7, "Corporate Transparency Act 31 USC 5336")

        eins = self._ein.findall(raw_text)
        extracts["eins"] = eins
        if not eins:
            self._add("EIN_MISSING", "HIGH", "No se detectó EIN. Requerido para empresas.",
                      0.9, "IRS Publication 1635")

        amounts = [float(a.replace(",", "")) for a in re.findall(r"\$([\d,]+\.\d{2})", raw_text)]
        large = [a for a in amounts if a > 600]
        if large and "1099-k" not in t and "1099k" not in t:
            self._add("1099K_THRESHOLD", "LOW",
                      f"{len(large)} monto(s) >$600 sin evidencia de reporte 1099-K.",
                      0.6, "IRS 1099-K threshold $600")

        return self._build(extracts)


class ChinaEngine(BaseComplianceEngine):
    def __init__(self):
        super().__init__("CN")

    def analyze(self, raw_text: str, xml_content: Optional[str] = None,
                extracted_fields: Optional[Dict] = None) -> ComplianceResult:
        self.findings = []
        t = raw_text.lower()
        if not xml_content:
            self._add("EFAPIAO_MISSING", "CRITICAL",
                      "No se detectó XML de e-Fapiao. El XML es la única fuente legal en China.",
                      1.0, "Ley de IVA Unificada 2026")

        if any(k in t for k in ["贷款", "利息", "融资", "loan", "interest", "financing"]):
            self._add("INTEREST_DEDUCTION_2026", "INFO",
                      "Factura financiera detectada. Nueva deducción de IVA en intereses aplicable 2026.",
                      0.8, "Art. 21 Ley IVA 2026")

        return self._build({})


class BrazilEngine(BaseComplianceEngine):
    def __init__(self):
        super().__init__("BR")
        self._cnpj = re.compile(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}")

    def analyze(self, raw_text: str, xml_content: Optional[str] = None,
                extracted_fields: Optional[Dict] = None) -> ComplianceResult:
        self.findings = []
        t = raw_text.lower()
        extracts: Dict = {}

        cnpjs = self._cnpj.findall(raw_text)
        extracts["cnpjs"] = cnpjs
        if not cnpjs:
            self._add("CNPJ_MISSING", "CRITICAL",
                      "No se detectó CNPJ válido. Obligatorio para toda factura NF-e.",
                      1.0, "Lei 10.833/2003")

        if "sped" not in t:
            self._add("SPED_NOT_MENTIONED", "MEDIUM",
                      "No se detecta referencia a SPED Fiscal.", 0.7, "SPED Fiscal - RFB")

        return self._build(extracts)


class UKEngine(BaseComplianceEngine):
    def __init__(self):
        super().__init__("GB")
        self._vat = re.compile(r"GB\d{9}")

    def analyze(self, raw_text: str, xml_content: Optional[str] = None,
                extracted_fields: Optional[Dict] = None) -> ComplianceResult:
        self.findings = []
        t = raw_text.lower()
        extracts: Dict = {}

        vats = self._vat.findall(raw_text)
        extracts["vat_numbers"] = vats
        if not vats:
            self._add("VAT_MISSING", "HIGH", "No se detectó VAT Number.", 0.9, "HMRC VAT Registration")

        if "mtd" not in t and "making tax digital" not in t:
            self._add("MTD_NOT_CONFIRMED", "MEDIUM",
                      "No se confirma compatibilidad MTD.", 0.7, "HMRC MTD")

        return self._build(extracts)


class GermanyEngine(BaseComplianceEngine):
    def __init__(self):
        super().__init__("DE")
        self._ust = re.compile(r"DE\d{9}")

    def analyze(self, raw_text: str, xml_content: Optional[str] = None,
                extracted_fields: Optional[Dict] = None) -> ComplianceResult:
        self.findings = []
        t = raw_text.lower()
        extracts: Dict = {}

        if xml_content:
            xml_tax = self._xml_tax(xml_content)
            vis_tax = self._vis_tax(raw_text)
            if xml_tax and vis_tax and abs(xml_tax - vis_tax) > 0.01:
                self._add("XML_PRIMACY_VIOLATION", "CRITICAL",
                          f"XML muestra impuesto {xml_tax} pero PDF visual {vis_tax}. El XML es original.",
                          1.0, "GoBD 2026 - BMF")

        if "zugferd" not in t and "xrechnung" not in t:
            self._add("EINVOICE_FORMAT_MISSING", "MEDIUM",
                      "No se detecta formato ZUGFeRD o XRechnung.", 0.75, "ZUGFeRD 2.2")

        return self._build(extracts)

    def _xml_tax(self, xml: str) -> Optional[float]:
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(xml)
            for tag in ["TaxAmount", "TaxableAmount", "Steuerbetrag"]:
                elem = root.find(f".//*{tag}")
                if elem is not None and elem.text:
                    return float(elem.text)
        except Exception:
            pass
        return None

    def _vis_tax(self, text: str) -> Optional[float]:
        m = re.search(r"(?:MwSt|VAT|USt|Tax)[\s:]*([\d.,]+)\s*%", text, re.IGNORECASE)
        return float(m.group(1).replace(",", ".")) if m else None


class FranceEngine(BaseComplianceEngine):
    def __init__(self):
        super().__init__("FR")
        self._siren = re.compile(r"\b\d{9}\b")
        self._siret = re.compile(r"\b\d{14}\b")

    def analyze(self, raw_text: str, xml_content: Optional[str] = None,
                extracted_fields: Optional[Dict] = None) -> ComplianceResult:
        self.findings = []
        t = raw_text.lower()
        extracts: Dict = {"sirens": self._siren.findall(raw_text), "sirets": self._siret.findall(raw_text)}

        if not extracts["sirens"] and not extracts["sirets"]:
            self._add("SIREN_MISSING", "CRITICAL",
                      "No se detectó SIREN ni SIRET. Obligatorio para ruteo en el PPF.", 1.0, "PPF")

        if "factur-x" not in t and "ubl" not in t:
            self._add("B2B_EINVOICE_MISSING", "HIGH",
                      "No se detecta Factur-X o UBL. Mandato B2B septiembre 2026.",
                      0.85, "Mandato B2B 2026")

        return self._build(extracts)


class IndiaEngine(BaseComplianceEngine):
    def __init__(self):
        super().__init__("IN")
        self._gstin = re.compile(r"\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}")
        self._irn   = re.compile(r"[a-f0-9]{64}")

    def analyze(self, raw_text: str, xml_content: Optional[str] = None,
                extracted_fields: Optional[Dict] = None) -> ComplianceResult:
        self.findings = []
        t = raw_text.lower()
        extracts: Dict = {}

        gstins = self._gstin.findall(raw_text)
        extracts["gstins"] = gstins
        if not gstins:
            self._add("GSTIN_MISSING", "CRITICAL",
                      "No se detectó GSTIN válido.", 1.0, "CGST Act 2017")

        irns = self._irn.findall(raw_text)
        extracts["irns"] = irns
        if not irns:
            self._add("IRN_MISSING", "HIGH",
                      "No se detectó IRN. Obligatorio para empresas >₹10 Crore AATO.",
                      0.9, "Rule 48(4) CGST")

        return self._build(extracts)


class SpainEngine(BaseComplianceEngine):
    def __init__(self):
        super().__init__("ES")
        self._nif = re.compile(r"[A-Z]\d{8}\b|\b\d{8}[A-Z]")

    def analyze(self, raw_text: str, xml_content: Optional[str] = None,
                extracted_fields: Optional[Dict] = None) -> ComplianceResult:
        self.findings = []
        t = raw_text.lower()
        nifs = self._nif.findall(raw_text)
        if not nifs:
            self._add("NIF_MISSING", "HIGH",
                      "No se detectó NIF/CIF válido.", 0.9, "Ley 27/2014 LIS")

        if "sii" not in t and "suministro inmediato" not in t:
            self._add("SII_NOT_CONFIRMED", "MEDIUM",
                      "No se confirma reporte SII.", 0.7, "Orden HAP/1650/2015")

        return self._build({"nifs": nifs})


class JapanEngine(BaseComplianceEngine):
    def __init__(self):
        super().__init__("JP")
        self._corp = re.compile(r"\b\d{13}\b")

    def analyze(self, raw_text: str, xml_content: Optional[str] = None,
                extracted_fields: Optional[Dict] = None) -> ComplianceResult:
        self.findings = []
        t = raw_text.lower()

        if "qualified invoice" not in t and "適格請求書" not in raw_text:
            self._add("QUALIFIED_INVOICE_MISSING", "HIGH",
                      "No se detecta 'Qualified Invoice'. Obligatorio para deducción JCT desde oct 2023.",
                      0.9, "Invoice System - Consumption Tax Act")

        if "10%" not in raw_text and "8%" not in raw_text:
            self._add("JCT_RATE_UNCLEAR", "MEDIUM",
                      "No se detecta tasa JCT (10% estándar / 8% reducido).", 0.7, "Consumption Tax Act")

        return self._build({"corporate_numbers": self._corp.findall(raw_text)})


class CanadaEngine(BaseComplianceEngine):
    def __init__(self):
        super().__init__("CA")
        self._bn = re.compile(r"\d{9}RC\d{4}")

    def analyze(self, raw_text: str, xml_content: Optional[str] = None,
                extracted_fields: Optional[Dict] = None) -> ComplianceResult:
        self.findings = []
        t = raw_text.lower()
        bns = self._bn.findall(raw_text)
        if not bns:
            self._add("BN_MISSING", "HIGH", "No se detectó Business Number.", 0.9, "CRA")

        if any(k in t for k in ["government", "federal", "public sector"]) and "peppol" not in t:
            self._add("PEPPOL_B2G_MISSING", "HIGH",
                      "Contrato B2G federal sin formato PEPPOL BIS Billing 3.0.",
                      0.85, "Treasury Board of Canada")

        if any(k in t for k in ["software", "saas", "streaming", "digital service", "cloud"]):
            if any(k in t for k in ["inc.", "ltd.", "gmbh", "s.a.", "b.v."]):
                self._add("DST_POSSIBLE_OBLIGATION", "INFO",
                          "Empresa extranjera de servicios digitales. Verificar obligación DST 3%.",
                          0.6, "Digital Services Tax Act 2024")

        return self._build({"business_numbers": bns})


_ENGINES = {
    "MX": MexicoEngine, "US": USAEngine,  "CN": ChinaEngine,
    "BR": BrazilEngine, "GB": UKEngine,   "DE": GermanyEngine,
    "FR": FranceEngine, "IN": IndiaEngine, "ES": SpainEngine,
    "JP": JapanEngine,  "CA": CanadaEngine,
}


def run_compliance_check(
    raw_text: str,
    xml_content: Optional[str] = None,
    extracted_fields: Optional[Dict] = None,
    filename: str = "",
) -> ComplianceResult:
    router = ComplianceRouter()
    country, confidence = router.detect_country(raw_text, filename)

    if country == "UNKNOWN" or confidence < 0.15:
        return ComplianceResult(
            country_detected="UNKNOWN",
            country_confidence=confidence,
            findings=[ComplianceFinding(
                rule="COUNTRY_UNDETERMINED", severity="INFO",
                message="No se pudo determinar la jurisdicción. Análisis genérico aplicado.",
                confidence=1.0, country="UNKNOWN",
            )],
            compliance_score=0.5,
            raw_extracts={},
            cross_border_flags=[],
        )

    engine_cls = _ENGINES.get(country)
    if not engine_cls:
        return ComplianceResult(
            country_detected=country, country_confidence=confidence,
            findings=[], compliance_score=0.5, raw_extracts={}, cross_border_flags=[],
        )

    engine = engine_cls()
    result = engine.analyze(raw_text, xml_content, extracted_fields)
    result.country_confidence = confidence

    cross: List[str] = []
    if "incoterms" in raw_text.lower():
        cross.append("CISG/Incoterms detected — verify writing requirements")
    if any(k in raw_text.lower() for k in ["import", "export", "customs", "aduana"]):
        cross.append("Cross-border transaction — verify dual jurisdiction compliance")
    result.cross_border_flags = cross

    return result
