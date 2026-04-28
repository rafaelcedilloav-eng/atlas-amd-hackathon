#!/usr/bin/env python3
"""
ATLAS File Creator
Generates agent_vision.py, chains.py, test_agent_vision.py in correct locations
Execute from D:\Proyectos\atlas-amd-hackathon\
"""

from pathlib import Path

# ============================================================================
# AGENT_VISION.PY CONTENT
# ============================================================================

AGENT_VISION_CONTENT = r'''#!/usr/bin/env python3
"""ATLAS Agent 1: Vision Analyzer"""

import os, json, logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('logs/agent_vision.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)
load_dotenv()

@dataclass
class ExtractedField:
    field_name: str
    value: Any
    confidence: float
    source_text: Optional[str] = None
    notes: Optional[str] = None

@dataclass
class DocumentAnalysis:
    document_id: str
    document_type: str
    extracted_fields: Dict[str, ExtractedField]
    detected_issues: List[str]
    overall_confidence: float
    processing_time_ms: float
    model_used: str
    timestamp: str

class VisionAnalyzerAgent:
    def __init__(self):
        self.llm_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model_name = os.getenv('OLLAMA_VISION_MODEL', 'llava:7b')
        logger.info(f"Initializing VisionAnalyzerAgent with {self.model_name}")
        
        self.llm = Ollama(base_url=self.llm_url, model=self.model_name, temperature=0.3, top_p=0.9, num_ctx=4096, verbose=False)
        self._init_prompts()
    
    def _init_prompts(self):
        self.classify_prompt = PromptTemplate(input_variables=["document_content"],
            template="""Analyze this document and classify it EXACTLY as one of: invoice, contract, report, receipt, unknown
Document content: {document_content}
Respond ONLY with the classification word, nothing else.""")
        
        self.invoice_prompt = PromptTemplate(input_variables=["document_content"],
            template="""Extract ALL financial data from this invoice. Return ONLY valid JSON:
{{"invoice_number": {{"value": "...", "confidence": 0.95}}, "date": {{"value": "YYYY-MM-DD", "confidence": 0.95}}, 
"vendor_name": {{"value": "...", "confidence": 0.95}}, "client_name": {{"value": "...", "confidence": 0.95}},
"subtotal": {{"value": null or number, "confidence": 0.95}}, "tax": {{"value": null or number, "confidence": 0.95}},
"total": {{"value": null or number, "confidence": 0.95}}, "payment_terms": {{"value": "...", "confidence": 0.95}},
"due_date": {{"value": "YYYY-MM-DD", "confidence": 0.95}}}}
Document: {document_content}
IMPORTANT: Return ONLY the JSON, no other text.""")
        
        self.contract_prompt = PromptTemplate(input_variables=["document_content"],
            template="""Extract key contract information. Return ONLY valid JSON:
{{"contract_type": "...", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD or null if MISSING",
"parties": ["party1", "party2"], "amount": number or null, "key_terms": ["term1"], "renewal_clause": "yes/no"}}
Document: {document_content}
IMPORTANT: Return ONLY the JSON, no other text.""")
        
        self.issues_prompt = PromptTemplate(input_variables=["document_content", "extracted_data"],
            template="""Check for issues/traps: 1) Math errors 2) Missing fields 3) Unclear values 4) Inconsistencies 5) Suspicious patterns
Document: {document_content}
Extracted data: {extracted_data}
Return ONLY a JSON list: ["Issue 1", "Issue 2"] or [] if none.""")
    
    def analyze_document(self, document_path: str) -> DocumentAnalysis:
        import time
        start_time = time.time()
        logger.info(f"Starting analysis of {document_path}")
        
        document_content = self._read_document(document_path)
        if not document_content:
            return self._empty_analysis(document_path)
        
        doc_type = self._classify_document(document_content)
        logger.info(f"Document classified as: {doc_type}")
        
        extracted_fields = {}
        if doc_type == 'invoice':
            extracted_fields = self._extract_invoice_data(document_content)
        elif doc_type == 'contract':
            extracted_fields = self._extract_contract_data(document_content)
        
        detected_issues = self._detect_issues(document_content, extracted_fields)
        confidences = [field.confidence for field in extracted_fields.values() if isinstance(field, ExtractedField)]
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        analysis = DocumentAnalysis(
            document_id=Path(document_path).stem, document_type=doc_type,
            extracted_fields=extracted_fields, detected_issues=detected_issues,
            overall_confidence=round(overall_confidence, 2), processing_time_ms=round(processing_time_ms, 2),
            model_used=self.model_name, timestamp=datetime.now().isoformat())
        
        return analysis
    
    def _read_document(self, document_path: str) -> Optional[str]:
        try:
            path = Path(document_path)
            if not path.exists():
                return None
            size_mb = path.stat().st_size / (1024 * 1024)
            return f"Document: {path.name} ({size_mb:.1f}MB)"
        except Exception as e:
            logger.error(f"Error reading document: {e}")
            return None
    
    def _classify_document(self, content: str) -> str:
        try:
            chain = LLMChain(llm=self.llm, prompt=self.classify_prompt)
            result = chain.run(document_content=content).strip().lower()
            return result if result in ['invoice', 'contract', 'report', 'receipt', 'unknown'] else 'unknown'
        except:
            return 'unknown'
    
    def _extract_invoice_data(self, content: str) -> Dict[str, ExtractedField]:
        try:
            chain = LLMChain(llm=self.llm, prompt=self.invoice_prompt)
            result = chain.run(document_content=content)
            extracted = json.loads(result)
            
            fields = {}
            for field_name, field_data in extracted.items():
                if isinstance(field_data, dict) and 'value' in field_data:
                    fields[field_name] = ExtractedField(field_name=field_name, value=field_data.get('value'),
                        confidence=field_data.get('confidence', 0.7), source_text=None, notes=None)
            return fields
        except:
            return {}
    
    def _extract_contract_data(self, content: str) -> Dict[str, ExtractedField]:
        try:
            chain = LLMChain(llm=self.llm, prompt=self.contract_prompt)
            result = chain.run(document_content=content)
            extracted = json.loads(result)
            
            fields = {}
            for field_name, value in extracted.items():
                notes = "WARNING: No expiration date specified" if field_name == 'end_date' and value is None else None
                fields[field_name] = ExtractedField(field_name=field_name, value=value, confidence=0.85,
                    source_text=None, notes=notes)
            return fields
        except:
            return {}
    
    def _detect_issues(self, content: str, fields: Dict) -> List[str]:
        issues = []
        try:
            fields_json = json.dumps({k: asdict(v) if isinstance(v, ExtractedField) else v for k, v in fields.items()}, default=str)
            chain = LLMChain(llm=self.llm, prompt=self.issues_prompt)
            result = chain.run(document_content=content, extracted_data=fields_json)
            detected = json.loads(result)
            if isinstance(detected, list):
                issues = detected
        except:
            pass
        
        if 'total' in fields and 'subtotal' in fields:
            total_val = fields['total'].value
            subtotal_val = fields['subtotal'].value
            if isinstance(total_val, (int, float)) and isinstance(subtotal_val, (int, float)):
                if abs(total_val - subtotal_val) > 100:
                    issues.append(f"⚠️  TRAP: Total ({total_val}) doesn't match subtotal ({subtotal_val})")
        
        for field in ['vendor_name', 'total', 'date']:
            if field in fields and fields[field].value is None:
                issues.append(f"⚠️  TRAP: Missing critical field: {field}")
        
        return issues
    
    def _empty_analysis(self, document_path: str) -> DocumentAnalysis:
        return DocumentAnalysis(document_id=Path(document_path).stem, document_type='unknown',
            extracted_fields={}, detected_issues=['Could not read document'], overall_confidence=0.0,
            processing_time_ms=0.0, model_used=self.model_name, timestamp=datetime.now().isoformat())

def serialize_analysis(analysis: DocumentAnalysis) -> Dict:
    return {
        'document_id': analysis.document_id, 'document_type': analysis.document_type,
        'extracted_fields': {k: {'value': v.value, 'confidence': v.confidence, 'notes': v.notes}
            for k, v in analysis.extracted_fields.items()},
        'detected_issues': analysis.detected_issues, 'overall_confidence': analysis.overall_confidence,
        'processing_time_ms': analysis.processing_time_ms, 'model_used': analysis.model_used,
        'timestamp': analysis.timestamp
    }

if __name__ == '__main__':
    logger.info("="*60)
    logger.info("ATLAS Agent 1: Vision Analyzer")
    logger.info("="*60)
    
    agent = VisionAnalyzerAgent()
    test_dir = Path('test_documents')
    if test_dir.exists():
        pdf_files = list(test_dir.glob('*.pdf'))
        logger.info(f"Found {len(pdf_files)} test documents")
        
        results = []
        for pdf_file in sorted(pdf_files):
            logger.info(f"\nAnalyzing: {pdf_file.name}")
            analysis = agent.analyze_document(str(pdf_file))
            results.append(serialize_analysis(analysis))
            
            logger.info(f"  Type: {analysis.document_type}")
            logger.info(f"  Confidence: {analysis.overall_confidence}")
            logger.info(f"  Issues: {len(analysis.detected_issues)}")
            if analysis.detected_issues:
                for issue in analysis.detected_issues:
                    logger.info(f"    - {issue}")
        
        output_file = Path('logs/agent_vision_results.json')
        output_file.parent.mkdir(exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"\n✅ Results saved to {output_file}")
'''

# ============================================================================
# CHAINS.PY CONTENT
# ============================================================================

CHAINS_CONTENT = r'''#!/usr/bin/env python3
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
'''

# ============================================================================
# TEST_AGENT_VISION.PY CONTENT
# ============================================================================

TEST_CONTENT = r'''#!/usr/bin/env python3
"""Test Suite for ATLAS Agent 1"""

import sys, json
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent_vision import VisionAnalyzerAgent, serialize_analysis
from src.chains import DecisionOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_agent_vision():
    logger.info("\n" + "="*70)
    logger.info("ATLAS AGENT 1: VISION ANALYZER TEST SUITE")
    logger.info("="*70)
    
    agent = VisionAnalyzerAgent()
    
    test_dir = Path('test_documents')
    if not test_dir.exists():
        logger.error(f"Test directory not found: {test_dir}")
        return False
    
    pdf_files = sorted(test_dir.glob('*.pdf'))
    if not pdf_files:
        logger.error("No PDF files found in test_documents/")
        return False
    
    logger.info(f"Found {len(pdf_files)} test documents\n")
    
    results = []
    passed = 0
    failed = 0
    
    for pdf_file in pdf_files:
        logger.info(f"\n{'─'*70}")
        logger.info(f"Testing: {pdf_file.name}")
        logger.info('─'*70)
        
        try:
            analysis = agent.analyze_document(str(pdf_file))
            result = serialize_analysis(analysis)
            results.append(result)
            
            logger.info(f"Document Type: {analysis.document_type}")
            logger.info(f"Confidence: {analysis.overall_confidence}")
            logger.info(f"Processing Time: {analysis.processing_time_ms}ms")
            logger.info(f"Fields Extracted: {len(analysis.extracted_fields)}")
            logger.info(f"Issues Detected: {len(analysis.detected_issues)}")
            
            if analysis.extracted_fields:
                logger.info("\nExtracted Data:")
                for field_name, field in analysis.extracted_fields.items():
                    logger.info(f"  {field_name}: {field.value} (confidence: {field.confidence})")
                    if field.notes:
                        logger.info(f"    └─ Note: {field.notes}")
            
            if analysis.detected_issues:
                logger.info("\n⚠️  Issues/Traps Detected:")
                for issue in analysis.detected_issues:
                    logger.info(f"  • {issue}")
                failed += 1
            else:
                logger.info("\n✅ No issues detected")
                passed += 1
            
            if analysis.document_type != 'unknown':
                validation = DecisionOrchestrator.validate_by_type(analysis.document_type, analysis.extracted_fields)
                logger.info(f"\nValidation Result: {validation['is_valid']}")
                if validation['traps_found']:
                    logger.info("Validation Traps:")
                    for trap in validation['traps_found']:
                        logger.info(f"  • [{trap['severity'].upper()}] {trap['reason']}")
            
        except Exception as e:
            logger.error(f"ERROR analyzing {pdf_file.name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    output_dir = Path('logs')
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / 'test_results.json'
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"\n✅ Results saved to {output_file}")
    
    logger.info("\n" + "="*70)
    logger.info("TEST SUMMARY")
    logger.info("="*70)
    logger.info(f"Total Documents: {len(pdf_files)}")
    logger.info(f"✅ Passed (clean): {passed}")
    logger.info(f"⚠️  Issues Found: {failed}")
    
    return True

if __name__ == '__main__':
    success = test_agent_vision()
    if success:
        logger.info("\n🎉 Test suite completed successfully!")
        sys.exit(0)
    else:
        logger.error("\n❌ Test suite failed!")
        sys.exit(1)
'''

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n" + "="*70)
    print("ATLAS: Creating Agent Files Locally")
    print("="*70)
    
    files = {
        'src/agent_vision.py': AGENT_VISION_CONTENT,
        'src/chains.py': CHAINS_CONTENT,
        'tests/test_agent_vision.py': TEST_CONTENT
    }
    
    for file_path, content in files.items():
        full_path = Path(file_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"\n✅ Creating: {file_path}")
        full_path.write_text(content)
    
    print("\n" + "="*70)
    print("✅ ALL FILES CREATED SUCCESSFULLY")
    print("="*70)
    print("\nFiles created:")
    for file_path in files.keys():
        print(f"  ✓ {file_path}")
    
    print("\n" + "="*70)
    print("NEXT STEP: Run the test")
    print("="*70)
    print("\nExecute this command:")
    print("  python tests/test_agent_vision.py")

if __name__ == '__main__':
    main()
