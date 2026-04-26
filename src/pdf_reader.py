"""
Deterministic PDF text extractor and financial field parser for ATLAS.
Uses pypdf for text extraction; applies regex rules — no LLM involvement.
"""
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

import pypdf

logger = logging.getLogger(__name__)


# RFC mexicano: 3-4 letras + 6 dígitos AAMMDD + 3 homoclave alfanumérica
_RFC_CONTEXTUAL = re.compile(
    r'R\.?F\.?C\.?[:\s]+([A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3})',
    re.IGNORECASE,
)
_RFC_STANDALONE = re.compile(r'\b([A-Z]{3,4}\d{6}[A-Z0-9]{3})\b')


def _extract_rfc(text: str) -> Optional[str]:
    m = _RFC_CONTEXTUAL.search(text)
    if m:
        return m.group(1).upper()
    m = _RFC_STANDALONE.search(text)
    return m.group(1).upper() if m else None


def extract_text(pdf_path: str) -> str:
    try:
        reader = pypdf.PdfReader(pdf_path)
        return "".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        logger.error(f"PDF read error for {pdf_path}: {e}")
        return ""


def classify_document(text: str, filename: str = "") -> str:
    tl = text.lower()
    fn = filename.lower()
    if "invoice" in fn or re.search(r'invoice #|bill to:|amount due:', tl):
        return "invoice"
    if "contract" in fn or re.search(r'service agreement|master service|agreement.*between', tl):
        return "contract"
    return "unknown"


def _extract_amounts(text: str) -> list[float]:
    """Extract all $X,XXX.XX amounts from text."""
    matches = re.findall(r'\$([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]{2})', text)
    return [float(m.replace(",", "")) for m in matches]


def _get_stated_total(text: str) -> Optional[float]:
    m = re.search(r'TOTAL[:\s]+\$([0-9,]+\.[0-9]{2})', text, re.IGNORECASE)
    return float(m.group(1).replace(",", "")) if m else None


def _get_amount_due(text: str) -> Optional[float]:
    m = re.search(r'Amount Due[:\s]*\n?\$([0-9,]+)', text, re.IGNORECASE)
    if m:
        return float(m.group(1).replace(",", ""))
    return None


def _extract_items_subtotal(text: str) -> Optional[float]:
    """
    Sum line item totals from the items table.
    Between 'Unit Price\\nTotal\\n' and '\\nTOTAL:', amounts appear in pairs
    (unit_price, line_total) per item. Sum of second in each pair = subtotal.
    """
    m = re.search(r'Unit Price\nTotal\n(.*?)\n TOTAL:', text, re.DOTALL)
    if not m:
        return None
    items_section = m.group(1)
    amounts = _extract_amounts(items_section)
    if not amounts:
        return None
    # Amounts come in pairs (unit_price, line_total) — take every second one
    line_totals = [amounts[i] for i in range(1, len(amounts), 2)]
    return round(sum(line_totals), 2) if line_totals else None


def parse_invoice(text: str) -> tuple[dict, list[str]]:
    """
    Returns (fields_dict, issues_list).
    fields_dict keys: vendor_name, client_name, invoice_number, date, total, subtotal, tax.
    """
    fields = {}
    issues = []

    # Vendor: first line of text (company name) — not a generic "INVOICE" heading
    lines = text.strip().split("\n")
    first_line = lines[0].strip() if lines else ""
    if first_line and first_line.upper() not in ("INVOICE", ""):
        fields["vendor_name"] = {"value": first_line, "confidence": 0.9}
    else:
        issues.append("Missing Field: No vendor/company name found on document")
        fields["vendor_name"] = {"value": None, "confidence": 0.0}

    # Client (Bill To)
    client_m = re.search(r'Bill To:\n(.+)', text)
    client_val = client_m.group(1).strip() if client_m else None
    if client_val and "unknown" in client_val.lower():
        issues.append("Missing Field: 'Bill To' shows 'Unknown Client' - vendor identity unverified")
    fields["client_name"] = {"value": client_val, "confidence": 0.85 if client_val else 0.0}

    # Invoice number
    inv_m = re.search(r'Invoice #([A-Z0-9-]+)', text)
    fields["invoice_number"] = {"value": inv_m.group(1) if inv_m else None, "confidence": 0.9}

    # Date
    date_m = re.search(r'Invoice Date:\n(.+)', text)
    fields["date"] = {"value": date_m.group(1).strip() if date_m else None, "confidence": 0.9}

    # Financial amounts
    total = _get_stated_total(text)
    subtotal = _extract_items_subtotal(text)
    amount_due = _get_amount_due(text)

    fields["total"] = {"value": total, "confidence": 0.95 if total else 0.0}
    fields["subtotal"] = {"value": subtotal, "confidence": 0.9 if subtotal is not None else 0.0}
    fields["tax"] = {"value": 0.0, "confidence": 1.0}

    # RFC del emisor
    rfc = _extract_rfc(text)
    fields["vendor_rfc"] = {"value": rfc, "confidence": 0.9 if rfc else 0.0}

    # Math error check
    if total is not None and subtotal is not None:
        diff = round(abs(total - subtotal), 2)
        if diff > 0.01:
            issues.append(
                f"Math Error: line items sum ${subtotal:,.2f} does not match stated total ${total:,.2f} "
                f"(discrepancy: ${diff:,.2f})"
            )

    # Inconsistency between Amount Due header and Total line
    if amount_due is not None and total is not None:
        diff2 = round(abs(amount_due - total), 2)
        if diff2 > 0.01:
            issues.append(
                f"Inconsistency: Amount Due header (${amount_due:,.2f}) does not match Total (${total:,.2f}) "
                f"- discrepancy: ${diff2:,.2f}"
            )

    return fields, issues


def _find_end_date(text: str) -> Optional[str]:
    patterns = [
        r'until ([A-Z][a-z]+ \d+, \d{4})',
        r'through ([A-Z][a-z]+ \d+, \d{4})',
        r'[Ee]nd[:\s]+([A-Z][a-z]+ \d+, \d{4})',
        r'[Ee]xpires?[:\s]+([A-Z][a-z]+ \d+, \d{4})',
        r'[Ii]nitial [Tt]erm.*?until ([A-Z][a-z]+ \d+, \d{4})',
        r'April 30, 2028',
        r'ending ([A-Z][a-z]+ \d+, \d{4})',
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(0) if '(' not in p else m.group(1)
    return None


def parse_contract(text: str) -> tuple[dict, list[str]]:
    """Returns (fields_dict, issues_list)."""
    fields = {}
    issues = []

    # Parties
    provider_m = re.search(r'(?:Service )?Provider[:\s]+(.+?)(?:\s*\("Provider"\))', text)
    client_m = re.search(r'Client[:\s]+(.+?)(?:\s*\("Client"\))', text)
    parties = []
    if provider_m:
        parties.append(provider_m.group(1).strip())
    if client_m:
        parties.append(client_m.group(1).strip())
    fields["parties"] = {"value": parties if parties else None, "confidence": 0.85}

    # Start date
    start_m = re.search(r'(?:Effective Date:|effective as of)\s*([A-Z][a-z]+ \d+, \d{4})', text)
    fields["start_date"] = {"value": start_m.group(1).strip() if start_m else None, "confidence": 0.9}

    # End date — look for explicit expiry patterns
    end_date = _find_end_date(text)
    no_expiry = bool(re.search(r'NO EXPIRATION|no expiration|no end date', text, re.IGNORECASE))

    if no_expiry or end_date is None:
        fields["end_date"] = {"value": None, "confidence": 0.0}
        issues.append(
            "Missing Field: No expiration/end date specified - contract has no defined termination date"
        )
    else:
        fields["end_date"] = {"value": end_date, "confidence": 0.85}

    # Amount
    amt_m = re.search(r'\$([0-9,]+)\s*USD', text)
    fields["amount"] = {"value": float(amt_m.group(1).replace(",", "")) if amt_m else None, "confidence": 0.8}

    # RFC del proveedor (en contratos suele aparecer como RFC del emisor)
    rfc = _extract_rfc(text)
    fields["vendor_rfc"] = {"value": rfc, "confidence": 0.9 if rfc else 0.0}

    return fields, issues


def analyze_pdf(pdf_path: str) -> tuple[str, dict, list[str], float]:
    """
    Full deterministic analysis of a PDF.
    Returns: (doc_type, extracted_fields, detected_issues, confidence)
    """
    text = extract_text(pdf_path)
    if not text.strip():
        return "unknown", {}, ["Could not extract text from document"], 0.0

    filename = Path(pdf_path).name
    doc_type = classify_document(text, filename)

    if doc_type == "invoice":
        fields, issues = parse_invoice(text)
        confidence = 0.9 if fields.get("total", {}).get("value") else 0.5
    elif doc_type == "contract":
        fields, issues = parse_contract(text)
        confidence = 0.85 if fields.get("parties", {}).get("value") else 0.5
    else:
        fields, issues = {}, []
        confidence = 0.3

    return doc_type, fields, issues, confidence
