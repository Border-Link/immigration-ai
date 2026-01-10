"""
Service for matching documents against visa document requirements.
"""
import logging
from typing import Optional, Tuple, Dict, Any
from document_handling.selectors.case_document_selector import CaseDocumentSelector
from immigration_cases.selectors.case_selector import CaseSelector
from rules_knowledge.selectors.visa_rule_version_selector import VisaRuleVersionSelector
from rules_knowledge.selectors.visa_document_requirement_selector import VisaDocumentRequirementSelector
from rules_knowledge.services.rule_engine_service import RuleEngineService

logger = logging.getLogger('django')


class DocumentRequirementMatchingService:
    """Service for matching documents against visa document requirements."""

    @staticmethod
    def match_document_against_requirements(case_document_id: str) -> Tuple[str, Dict[str, Any], Optional[str]]:
        """
        Match a document against visa document requirements.
        
        Args:
            case_document_id: UUID of the case document to match
            
        Returns:
            Tuple of (result, details, error_message)
            - result: 'passed', 'failed', 'warning', or 'pending'
            - details: Dict with matching details
            - error_message: Error message if matching failed
        """
        try:
            # Get case document
            case_document = CaseDocumentSelector.get_by_id(case_document_id)
            if not case_document:
                logger.error(f"Case document {case_document_id} not found")
                return 'failed', {}, 'Case document not found'
            
            # Get case
            case = case_document.case
            if not case:
                logger.error(f"Case not found for document {case_document_id}")
                return 'failed', {}, 'Case not found'
            
            # Get visa type from case
            if not case.visa_type:
                logger.warning(f"Case {case.id} has no visa type")
                return 'pending', {'message': 'Case has no visa type'}, None
            
            # Get current rule version for visa type
            rule_version = VisaRuleVersionSelector.get_current_by_visa_type(case.visa_type)
            if not rule_version:
                logger.warning(f"No active rule version found for visa type {case.visa_type.id}")
                return 'pending', {'message': 'No active rule version found'}, None
            
            # Get document requirements for this rule version
            requirements = VisaDocumentRequirementSelector.get_by_rule_version(rule_version)
            
            if not requirements.exists():
                logger.warning(f"No document requirements found for rule version {rule_version.id}")
                return 'pending', {'message': 'No document requirements found'}, None
            
            # Check if document type matches any requirement
            document_type = case_document.document_type
            if not document_type:
                logger.warning(f"Document {case_document_id} has no document type")
                return 'warning', {
                    'message': 'Document has no document type',
                    'requires_classification': True
                }, None
            
            # Find matching requirement
            matching_requirement = None
            for requirement in requirements:
                if requirement.document_type.id == document_type.id:
                    matching_requirement = requirement
                    break
            
            if not matching_requirement:
                # Document type doesn't match any requirement
                return 'failed', {
                    'message': f'Document type {document_type.name} does not match any requirement for visa type {case.visa_type.name}',
                    'document_type': document_type.name,
                    'visa_type': case.visa_type.name,
                    'required_document_types': [
                        {
                            'id': str(req.document_type.id),
                            'name': req.document_type.name,
                            'code': req.document_type.code,
                            'mandatory': req.mandatory
                        }
                        for req in requirements
                    ]
                }, None
            
            # Check if requirement is mandatory
            is_mandatory = matching_requirement.mandatory
            
            # Check conditional logic if present
            conditional_passed = True
            conditional_details = {}
            if matching_requirement.conditional_logic:
                try:
                    # Evaluate conditional logic against case facts
                    conditional_result = RuleEngineService.evaluate_expression(
                        matching_requirement.conditional_logic,
                        case_facts
                    )
                    
                    # evaluate_expression always returns a dict with 'passed', 'result', 'error', 'missing_facts'
                    conditional_passed = conditional_result.get('passed', False)
                    conditional_details = conditional_result
                    
                    # If there's an error or missing facts, log it but default to passed
                    if conditional_result.get('error') or conditional_result.get('missing_facts'):
                        logger.warning(
                            f"Conditional logic evaluation had issues: "
                            f"error={conditional_result.get('error')}, "
                            f"missing_facts={conditional_result.get('missing_facts')}"
                        )
                        # Default to passed if evaluation has issues
                        conditional_passed = True
                except Exception as e:
                    logger.warning(f"Error evaluating conditional logic: {e}")
                    conditional_passed = True  # Default to passed if evaluation fails
                    conditional_details = {'error': str(e), 'default': True}
            
            # Determine result
            if conditional_passed:
                result = 'passed'
                message = f'Document type {document_type.name} matches requirement for visa type {case.visa_type.name}'
            else:
                result = 'warning'
                message = f'Document type {document_type.name} matches requirement but conditional logic not satisfied'
            
            details = {
                'message': message,
                'document_type': {
                    'id': str(document_type.id),
                    'name': document_type.name,
                    'code': document_type.code
                },
                'visa_type': {
                    'id': str(case.visa_type.id),
                    'name': case.visa_type.name
                },
                'requirement': {
                    'id': str(matching_requirement.id),
                    'mandatory': is_mandatory,
                    'conditional_logic': matching_requirement.conditional_logic
                },
                'conditional_passed': conditional_passed,
                'conditional_details': conditional_details
            }
            
            logger.info(
                f"Document {case_document_id} matched against requirements: "
                f"result={result}, mandatory={is_mandatory}, conditional_passed={conditional_passed}"
            )
            
            return result, details, None
            
        except Exception as e:
            logger.error(f"Error matching document against requirements: {e}", exc_info=True)
            return 'failed', {}, str(e)
