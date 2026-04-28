"""
Test #8 — External Integrity Gate
Verifies that ATLAS flags a mathematically perfect invoice as CRITICAL
when the vendor is on the fraud blacklist (ghost vendor scenario).
"""
import datetime
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decimal import Decimal
import pytest

from src.schemas import (
    VisionOutput, ReasoningOutput, ReasoningStep,
    ExtractedField,
)
from src.agent_validator import run as validator_run, _check_external_integrity, _db_check_duplicate_id


def make_perfect_invoice(vendor_name: str, doc_id: str = "INV-GHOST-001") -> VisionOutput:
    """Invoice where math is PERFECT — subtotal + tax == total exactly."""
    return VisionOutput(
        document_id=doc_id,
        document_type="invoice",
        pdf_path="test.pdf",
        extracted_fields={
            "subtotal": ExtractedField(value=Decimal("10000.00"), confidence=0.99),
            "tax":      ExtractedField(value=Decimal("1600.00"),  confidence=0.99),
            "total":    ExtractedField(value=Decimal("11600.00"), confidence=0.99),
            "vendor":   ExtractedField(value=vendor_name,         confidence=0.99),
        },
        detected_issues=[],
        confidence=0.97,
        model_used="test",
        processing_time_ms=50,
        timestamp=datetime.datetime.now(),
    )


def make_clean_reasoning(doc_id: str = "INV-GHOST-001") -> ReasoningOutput:
    """Reasoning that says 'No Trap' — the LLM found nothing wrong."""
    return ReasoningOutput(
        document_id=doc_id,
        trap_detected="No Trap",
        trap_id=f"TRAP-{doc_id}-001",
        reasoning_chain=[
            ReasoningStep(step=1, description="Math verified",    evidence="10000+1600=11600", conclusion="Totals match"),
            ReasoningStep(step=2, description="Fields complete",  evidence="All fields present", conclusion="No missing fields"),
            ReasoningStep(step=3, description="Values coherent",  evidence="Tax rate 16% LIVA", conclusion="No inconsistency"),
        ],
        trap_severity="NONE",
        confidence=0.95,
        reasoning_valid=True,
        assumptions=["Standard LIVA 16% applies"],
        model_used="deterministic",
        processing_time_ms=100,
        timestamp=datetime.datetime.now(),
    )


class TestExternalIntegrityGate:

    def test_t8_perfect_math_ghost_vendor_is_critical(self):
        """
        Test #8 — Core assertion:
        A mathematically perfect invoice from a blacklisted vendor MUST be flagged
        as CRITICAL regardless of arithmetic correctness.
        """
        vision = make_perfect_invoice(vendor_name="Fantasma Corp")
        reasoning = make_clean_reasoning()

        result = validator_run(reasoning, vision)

        # Math should still check out
        assert result.validation_result.math_verified is False, \
            "Math should be clean (no error)"

        # But external gate overrides everything
        assert result.validation_result.trap_is_real is True, \
            "Ghost vendor must force trap_is_real=True"
        assert result.validation_result.severity_confirmed == "CRITICAL", \
            f"Ghost vendor must force CRITICAL severity, got {result.validation_result.severity_confirmed}"
        assert result.recommendation == "FLAG", \
            f"Ghost vendor must produce FLAG recommendation, got {result.recommendation}"

        # Verify the integrity violation is traceable in the output
        integrity_issues = [i for i in result.issues_found if "INTEGRITY VIOLATION" in i]
        assert integrity_issues, "Integrity violation must appear in issues_found"
        assert any("blacklist" in a for a in result.adjustments), \
            "Adjustment must document the blacklist hit"

        print(f"\n  [TEST #8 PASS] Ghost vendor '{vision.extracted_fields['vendor'].value}' flagged as CRITICAL")
        print(f"  issues_found: {result.issues_found}")
        print(f"  adjustments:  {result.adjustments}")
        print(f"  recommendation: {result.recommendation}")

    def test_clean_vendor_not_flagged(self):
        """Regression: a legitimate vendor with perfect math must still APPROVE."""
        vision = make_perfect_invoice(vendor_name="Proveedor Legítimo S.A. de C.V.")
        reasoning = make_clean_reasoning()

        result = validator_run(reasoning, vision)

        assert result.validation_result.trap_is_real is False, \
            "Legitimate vendor with perfect math must NOT be flagged"
        assert result.recommendation == "APPROVE", \
            f"Legitimate vendor must get APPROVE, got {result.recommendation}"
        print(f"\n  [REGRESSION PASS] Legitimate vendor approved correctly")

    def test_double_billing_detection(self):
        """A duplicate document ID must be flagged as CRITICAL double billing."""
        vision = make_perfect_invoice(
            vendor_name="Proveedor Legítimo S.A.",
            doc_id="INV-2024-DUPLICATE-001"  # ID ya procesado
        )
        reasoning = make_clean_reasoning(doc_id="INV-2024-DUPLICATE-001")

        result = validator_run(reasoning, vision)

        assert result.validation_result.trap_is_real is True, \
            "Duplicate doc ID must force trap_is_real=True"
        assert result.validation_result.severity_confirmed == "CRITICAL", \
            "Double billing must be CRITICAL"
        assert any("double billing" in i.lower() or "already been processed" in i.lower()
                   for i in result.issues_found), \
            "Double billing detail must appear in issues_found"
        print(f"\n  [DOUBLE BILLING PASS] Duplicate ID detected and flagged as CRITICAL")

    def test_integrity_functions_unit(self):
        """Unit tests for the integrity gate functions."""
        # Blacklisted vendors (case-insensitive)
        assert _check_external_integrity("X", "Fantasma Corp")[0] is True
        assert _check_external_integrity("X", "FANTASMA CORP")[0] is True   # case insensitive
        assert _check_external_integrity("X", "  ghost vendor sa  ")[0] is True  # strip
        assert _check_external_integrity("X", "Proveedor Legítimo")[0] is False

        # Duplicate IDs
        assert _db_check_duplicate_id("INV-2024-DUPLICATE-001") is True
        assert _db_check_duplicate_id("INV-CLEAN-123") is False

        # None vendor (document without vendor field)
        ok, detail = _check_external_integrity("INV-CLEAN", None)
        assert ok is False, "None vendor should not trigger violation"

        print(f"\n  [UNIT TESTS PASS] _check_external_integrity and _db_check_duplicate_id verified")


if __name__ == "__main__":
    suite = TestExternalIntegrityGate()
    suite.test_integrity_functions_unit()
    suite.test_t8_perfect_math_ghost_vendor_is_critical()
    suite.test_clean_vendor_not_flagged()
    suite.test_double_billing_detection()
    print("\n=== TEST #8 COMPLETO: ATLAS — DEFENSA FINANCIERA ENTERPRISE CONFIRMADA ===")
