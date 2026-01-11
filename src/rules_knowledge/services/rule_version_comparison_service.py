"""
Rule Version Comparison Service

Compares two rule versions to identify differences.
"""
import logging
from typing import Dict, List, Any, Optional
from rules_knowledge.models.visa_rule_version import VisaRuleVersion
from rules_knowledge.selectors.visa_rule_version_selector import VisaRuleVersionSelector
from rules_knowledge.selectors.visa_requirement_selector import VisaRequirementSelector
from rules_knowledge.selectors.visa_document_requirement_selector import VisaDocumentRequirementSelector

logger = logging.getLogger('django')


class RuleVersionComparisonService:
    """Service for comparing rule versions."""
    
    @staticmethod
    def compare_versions(
        version1_id: str,
        version2_id: str
    ) -> Dict[str, Any]:
        """
        Compare two rule versions and return differences.
        
        Args:
            version1_id: UUID of first rule version
            version2_id: UUID of second rule version
            
        Returns:
            Dict with comparison results:
            {
                'version1': {...},
                'version2': {...},
                'requirements': {
                    'added': [...],
                    'removed': [...],
                    'modified': [...],
                    'unchanged': [...]
                },
                'document_requirements': {
                    'added': [...],
                    'removed': [...],
                    'modified': [...],
                    'unchanged': [...]
                },
                'summary': {
                    'requirements_added': int,
                    'requirements_removed': int,
                    'requirements_modified': int,
                    'document_requirements_added': int,
                    'document_requirements_removed': int,
                    'document_requirements_modified': int
                }
            }
        """
        try:
            version1 = VisaRuleVersionSelector.get_by_id(version1_id)
            version2 = VisaRuleVersionSelector.get_by_id(version2_id)
            
            # Get requirements for both versions
            requirements1 = VisaRequirementSelector.get_by_rule_version(version1)
            requirements2 = VisaRequirementSelector.get_by_rule_version(version2)
            
            # Get document requirements for both versions
            doc_requirements1 = VisaDocumentRequirementSelector.get_by_rule_version(version1)
            doc_requirements2 = VisaDocumentRequirementSelector.get_by_rule_version(version2)
            
            # Compare requirements
            req_comparison = RuleVersionComparisonService._compare_requirements(
                requirements1,
                requirements2
            )
            
            # Compare document requirements
            doc_req_comparison = RuleVersionComparisonService._compare_document_requirements(
                doc_requirements1,
                doc_requirements2
            )
            
            return {
                'version1': {
                    'id': str(version1.id),
                    'effective_from': version1.effective_from.isoformat(),
                    'effective_to': version1.effective_to.isoformat() if version1.effective_to else None,
                    'is_published': version1.is_published,
                    'visa_type_name': version1.visa_type.name
                },
                'version2': {
                    'id': str(version2.id),
                    'effective_from': version2.effective_from.isoformat(),
                    'effective_to': version2.effective_to.isoformat() if version2.effective_to else None,
                    'is_published': version2.is_published,
                    'visa_type_name': version2.visa_type.name
                },
                'requirements': req_comparison,
                'document_requirements': doc_req_comparison,
                'summary': {
                    'requirements_added': len(req_comparison['added']),
                    'requirements_removed': len(req_comparison['removed']),
                    'requirements_modified': len(req_comparison['modified']),
                    'document_requirements_added': len(doc_req_comparison['added']),
                    'document_requirements_removed': len(doc_req_comparison['removed']),
                    'document_requirements_modified': len(doc_req_comparison['modified'])
                }
            }
            
        except Exception as e:
            logger.error(f"Error comparing rule versions: {e}", exc_info=True)
            return {
                'error': str(e),
                'version1': None,
                'version2': None,
                'requirements': {'added': [], 'removed': [], 'modified': [], 'unchanged': []},
                'document_requirements': {'added': [], 'removed': [], 'modified': [], 'unchanged': []},
                'summary': {}
            }
    
    @staticmethod
    def _compare_requirements(requirements1, requirements2) -> Dict[str, List[Dict]]:
        """Compare two sets of requirements."""
        req1_dict = {req.requirement_code: req for req in requirements1}
        req2_dict = {req.requirement_code: req for req in requirements2}
        
        added = []
        removed = []
        modified = []
        unchanged = []
        
        # Find added and modified
        for code, req2 in req2_dict.items():
            if code not in req1_dict:
                added.append({
                    'requirement_code': code,
                    'description': req2.description,
                    'rule_type': req2.rule_type,
                    'is_mandatory': req2.is_mandatory
                })
            else:
                req1 = req1_dict[code]
                if RuleVersionComparisonService._requirement_changed(req1, req2):
                    modified.append({
                        'requirement_code': code,
                        'changes': RuleVersionComparisonService._get_requirement_changes(req1, req2)
                    })
                else:
                    unchanged.append({
                        'requirement_code': code,
                        'description': req1.description
                    })
        
        # Find removed
        for code, req1 in req1_dict.items():
            if code not in req2_dict:
                removed.append({
                    'requirement_code': code,
                    'description': req1.description,
                    'rule_type': req1.rule_type
                })
        
        return {
            'added': added,
            'removed': removed,
            'modified': modified,
            'unchanged': unchanged
        }
    
    @staticmethod
    def _compare_document_requirements(doc_req1, doc_req2) -> Dict[str, List[Dict]]:
        """Compare two sets of document requirements."""
        doc_req1_dict = {req.document_type_id: req for req in doc_req1}
        doc_req2_dict = {req.document_type_id: req for req in doc_req2}
        
        added = []
        removed = []
        modified = []
        unchanged = []
        
        # Find added and modified
        for doc_type_id, req2 in doc_req2_dict.items():
            if doc_type_id not in doc_req1_dict:
                added.append({
                    'document_type_id': str(doc_type_id),
                    'document_type_name': req2.document_type.name,
                    'mandatory': req2.mandatory
                })
            else:
                req1 = doc_req1_dict[doc_type_id]
                if req1.mandatory != req2.mandatory or req1.conditional_logic != req2.conditional_logic:
                    modified.append({
                        'document_type_id': str(doc_type_id),
                        'document_type_name': req1.document_type.name,
                        'changes': {
                            'mandatory': {'old': req1.mandatory, 'new': req2.mandatory},
                            'conditional_logic': {'old': req1.conditional_logic, 'new': req2.conditional_logic}
                        }
                    })
                else:
                    unchanged.append({
                        'document_type_id': str(doc_type_id),
                        'document_type_name': req1.document_type.name
                    })
        
        # Find removed
        for doc_type_id, req1 in doc_req1_dict.items():
            if doc_type_id not in doc_req2_dict:
                removed.append({
                    'document_type_id': str(doc_type_id),
                    'document_type_name': req1.document_type.name,
                    'mandatory': req1.mandatory
                })
        
        return {
            'added': added,
            'removed': removed,
            'modified': modified,
            'unchanged': unchanged
        }
    
    @staticmethod
    def _requirement_changed(req1, req2) -> bool:
        """Check if a requirement has changed."""
        return (
            req1.description != req2.description or
            req1.rule_type != req2.rule_type or
            req1.is_mandatory != req2.is_mandatory or
            req1.condition_expression != req2.condition_expression
        )
    
    @staticmethod
    def _get_requirement_changes(req1, req2) -> Dict[str, Dict]:
        """Get detailed changes between two requirements."""
        changes = {}
        
        if req1.description != req2.description:
            changes['description'] = {'old': req1.description, 'new': req2.description}
        
        if req1.rule_type != req2.rule_type:
            changes['rule_type'] = {'old': req1.rule_type, 'new': req2.rule_type}
        
        if req1.is_mandatory != req2.is_mandatory:
            changes['is_mandatory'] = {'old': req1.is_mandatory, 'new': req2.is_mandatory}
        
        if req1.condition_expression != req2.condition_expression:
            changes['condition_expression'] = {'changed': True}  # Don't show full expressions
        
        return changes
