#!/usr/bin/env python3
"""ATLAS Explicit Decision Chains"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class DocumentType(str, Enum):
    INVOICE = "invoice"
    CONTRACT = "contract"
    REPORT = "report"
    RECEIPT = "receipt"
    UNKNOWN = "unknown"

class TrapType(str, Enum):
    MATH_ERROR = "math_error"
    MISSING_FIELD = "missing_field"
    INCONSISTENCY = "inconsistency"
    INVALID_FORMAT = "invalid_format"
    AMBIGUOUS_VALUE = "ambiguous_value"

@dataclass
class TrapDetected:
    trap_type: TrapType
    field_name: Optional[str]
    expected_value: Any
    actual_value: Any
    reason: str
    severity: str

@dataclass
class DecisionChainStep:
    step_number: int
    description: str
    condition: bool
    action: str
    result: Any

class InvoiceValidationChain:
    def __init__(self):
        self.steps: List[DecisionChainStep] = []
        self.traps_found: List[TrapDetected] = []
    
    def validate(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Starting invoice validation chain")
        self.steps = []
        self.traps_found = []
        
        step_1 = self._step_check_required_fields(extracted_data)
        self.steps.append(step_1)
        step_2 = self._step_check_math(extracted_data)
        self.steps.append(step_2)
        step_3 = self._step_check_dates(extracted_data)
        self.steps.append(step_3)
        step_4 = self._step_check_suspicious_values(extracted_data)
        self.steps.append(step_4)
        
        is_valid = not any(step.result == False for step in self.steps)
        
        return {
            'is_valid': is_valid,
            'decision_chain': [{'step': s.step_number, 'description': s.description, 'condition': s.condition,
                'action': s.action, 'result': s.result} for s in self.steps],
            'traps_found': [{'type': t.trap_type.value, 'field': t.field_name, 'expected': t.expected_value,
                'actual': t.actual_value, 'reason': t.reason, 'severity': t.severity} for t in self.traps_found],
            'total_steps': len(self.steps), 'total_traps': len(self.traps_found)
        }
    
    def _step_check_required_fields(self, data: Dict) -> DecisionChainStep:
        required = ['invoice_number', 'date', 'vendor_name', 'total']
        missing = [f for f in required if f not in data or data[f].get('value') is None]
        condition = len(missing) == 0
        
        if not condition:
            for field in missing:
                self.traps_found.append(TrapDetected(trap_type=TrapType.MISSING_FIELD, field_name=field,
                    expected_value='[present]', actual_value='[missing]', reason=f"Required field '{field}' is missing",
                    severity='high'))
        
        return DecisionChainStep(step_number=1, description="Check required fields",
            condition=condition, action="REJECT if missing" if not condition else "CONTINUE", result=condition)
    
    def _step_check_math(self, data: Dict) -> DecisionChainStep:
        condition = True
        if 'subtotal' in data and 'tax' in data and 'total' in data:
            subtotal = data['subtotal'].get('value')
            tax = data['tax'].get('value')
            total = data['total'].get('value')
            if all(isinstance(v, (int, float)) for v in [subtotal, tax, total]):
                expected_total = subtotal + tax
                if abs(expected_total - total) > 0.01:
                    condition = False
                    self.traps_found.append(TrapDetected(trap_type=TrapType.MATH_ERROR, field_name='total',
                        expected_value=round(expected_total, 2), actual_value=total,
                        reason=f"Total ({total}) != Subtotal ({subtotal}) + Tax ({tax})", severity='critical'))
        
        return DecisionChainStep(step_number=2, description="Check math: subtotal + tax = total",
            condition=condition, action="FLAG if wrong" if not condition else "CONTINUE", result=condition)
    
    def _step_check_dates(self, data: Dict) -> DecisionChainStep:
        condition = True
        if 'date' in data and 'due_date' in data:
            date_val = data['date'].get('value')
            due_date_val = data['due_date'].get('value')
            if isinstance(date_val, str) and isinstance(due_date_val, str):
                try:
                    if date_val > due_date_val:
                        condition = False
                        self.traps_found.append(TrapDetected(trap_type=TrapType.INCONSISTENCY, field_name='date',
                            expected_value=f"< {due_date_val}", actual_value=date_val,
                            reason=f"Invoice date ({date_val}) is after due date", severity='high'))
                except:
                    pass
        
        return DecisionChainStep(step_number=3, description="Check dates: invoice_date < due_date",
            condition=condition, action="FLAG if inconsistent" if not condition else "CONTINUE", result=condition)
    
    def _step_check_suspicious_values(self, data: Dict) -> DecisionChainStep:
        condition = True
        for field in ['subtotal', 'tax', 'total']:
            if field in data:
                value = data[field].get('value')
                if isinstance(value, (int, float)) and value < 0:
                    condition = False
                    self.traps_found.append(TrapDetected(trap_type=TrapType.INVALID_FORMAT, field_name=field,
                        expected_value='> 0', actual_value=value, reason=f"{field} is negative",
                        severity='medium'))
        
        return DecisionChainStep(step_number=4, description="Check for suspicious values",
            condition=condition, action="FLAG if found" if not condition else "CONTINUE", result=condition)

class ContractValidationChain:
    def __init__(self):
        self.steps: List[DecisionChainStep] = []
        self.traps_found: List[TrapDetected] = []
    
    def validate(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Starting contract validation")
        self.steps = []
        self.traps_found = []
        
        step_1 = self._step_check_expiration(extracted_data)
        self.steps.append(step_1)
        step_2 = self._step_check_parties(extracted_data)
        self.steps.append(step_2)
        step_3 = self._step_check_term_dates(extracted_data)
        self.steps.append(step_3)
        
        is_valid = not any(step.result == False for step in self.steps)
        
        return {
            'is_valid': is_valid,
            'decision_chain': [{'step': s.step_number, 'description': s.description, 'condition': s.condition,
                'action': s.action, 'result': s.result} for s in self.steps],
            'traps_found': [{'type': t.trap_type.value, 'field': t.field_name, 'reason': t.reason,
                'severity': t.severity} for t in self.traps_found],
            'total_steps': len(self.steps), 'total_traps': len(self.traps_found)
        }
    
    def _step_check_expiration(self, data: Dict) -> DecisionChainStep:
        condition = 'end_date' in data and data['end_date'].get('value') is not None
        if not condition:
            self.traps_found.append(TrapDetected(trap_type=TrapType.MISSING_FIELD, field_name='end_date',
                expected_value='[date]', actual_value='[missing]', reason="NO EXPIRATION DATE - CRITICAL",
                severity='critical'))
        return DecisionChainStep(step_number=1, description="Check expiration date exists",
            condition=condition, action="REJECT if missing" if not condition else "CONTINUE", result=condition)
    
    def _step_check_parties(self, data: Dict) -> DecisionChainStep:
        condition = 'parties' in data and data['parties'].get('value')
        if not condition:
            self.traps_found.append(TrapDetected(trap_type=TrapType.MISSING_FIELD, field_name='parties',
                expected_value='[list]', actual_value='[missing]', reason="Contract parties not specified",
                severity='high'))
        return DecisionChainStep(step_number=2, description="Check parties are defined",
            condition=condition, action="FLAG if missing" if not condition else "CONTINUE", result=condition)
    
    def _step_check_term_dates(self, data: Dict) -> DecisionChainStep:
        condition = True
        if 'start_date' in data and 'end_date' in data:
            start = data['start_date'].get('value')
            end = data['end_date'].get('value')
            if isinstance(start, str) and isinstance(end, str):
                try:
                    if start > end:
                        condition = False
                        self.traps_found.append(TrapDetected(trap_type=TrapType.INCONSISTENCY, field_name='dates',
                            expected_value="start < end", actual_value=f"{start} > {end}",
                            reason="Start date after end date", severity='high'))
                except:
                    pass
        return DecisionChainStep(step_number=3, description="Check term dates: start < end",
            condition=condition, action="FLAG if inconsistent" if not condition else "CONTINUE", result=condition)

class DecisionOrchestrator:
    @staticmethod
    def validate_by_type(doc_type: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        if doc_type == DocumentType.INVOICE.value:
            chain = InvoiceValidationChain()
            return chain.validate(extracted_data)
        elif doc_type == DocumentType.CONTRACT.value:
            chain = ContractValidationChain()
            return chain.validate(extracted_data)
        else:
            return {'is_valid': None, 'decision_chain': [], 'traps_found': [],
                'reason': f"Document type '{doc_type}' not supported"}

if __name__ == '__main__':
    test_invoice = {
        'invoice_number': {'value': 'INV-001', 'confidence': 0.95},
        'date': {'value': '2026-04-20', 'confidence': 0.99},
        'vendor_name': {'value': 'ACME Corp', 'confidence': 0.92},
        'total': {'value': 7500, 'confidence': 0.85},
        'subtotal': {'value': 7000, 'confidence': 0.85},
        'tax': {'value': 0, 'confidence': 0.95},
    }
    
    chain = InvoiceValidationChain()
    result = chain.validate(test_invoice)
    
    print("\n" + "="*60)
    print("Invoice Validation Result")
    print("="*60)
    print(f"Valid: {result['is_valid']}")
    print(f"Traps: {result['total_traps']}")
    
    if result['traps_found']:
        print("\nTraps detected:")
        for trap in result['traps_found']:
            print(f"  - [{trap['severity'].upper()}] {trap['reason']}")
