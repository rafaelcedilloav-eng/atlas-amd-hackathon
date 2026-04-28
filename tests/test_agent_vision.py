#!/usr/bin/env python3
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
