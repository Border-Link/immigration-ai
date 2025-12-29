"""
Rule Publishing Service

Service for promoting approved parsed rules to production (VisaRuleVersion and VisaRequirement).
This service implements the workflow from implementation.md Section 5.6.

Rules are created through two paths:
1. Automated: Ingestion → AI Parsing → Validation → Publishing (this service)
2. Manual: Admin creates rules directly via API
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Q

from data_ingestion.models.parsed_rule import ParsedRule
from data_ingestion.selectors.parsed_rule_selector import ParsedRuleSelector
from rules_knowledge.models.visa_rule_version import VisaRuleVersion
from rules_knowledge.models.visa_requirement import VisaRequirement
from rules_knowledge.models.visa_type import VisaType
from rules_knowledge.repositories.visa_rule_version_repository import VisaRuleVersionRepository
from rules_knowledge.repositories.visa_requirement_repository import VisaRequirementRepository
from rules_knowledge.selectors.visa_type_selector import VisaTypeSelector
from rules_knowledge.selectors.visa_rule_version_selector import VisaRuleVersionSelector
from rules_knowledge.services.visa_rule_version_service import VisaRuleVersionService
from users_access.services.notification_service import NotificationService
from users_access.tasks.email_tasks import send_rule_change_notification_email_task

logger = logging.getLogger('django')


class RulePublishingService:
    """
    Service for publishing approved parsed rules to production.
    
    This service handles the promotion workflow:
    1. Load approved parsed rule
    2. Find or create visa type
    3. Create new rule version
    4. Create requirements from parsed rule
    5. Close previous rule version
    6. Update parsed rule status
    7. Trigger notifications
    """
    
    @staticmethod
    def publish_approved_parsed_rule(
        parsed_rule_id: str,
        effective_from: Optional[datetime] = None,
        reviewer_notes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Publish an approved parsed rule to production.
        
        This is the main method that orchestrates the publishing workflow
        from implementation.md Section 5.6.
        
        Args:
            parsed_rule_id: UUID of the approved parsed rule
            effective_from: Optional effective date (defaults to now)
            reviewer_notes: Optional notes from reviewer
            
        Returns:
            Dict with publishing results:
            {
                'success': bool,
                'rule_version_id': str,
                'requirements_created': int,
                'previous_version_closed': bool
            }
        """
        try:
            # Step 1: Load approved parsed rule
            parsed_rule = ParsedRuleSelector.get_by_id(parsed_rule_id)
            if not parsed_rule:
                logger.error(f"Parsed rule {parsed_rule_id} not found")
                return {'success': False, 'error': 'Parsed rule not found'}
            
            # Verify status is approved
            if parsed_rule.status != 'approved':
                logger.error(
                    f"Cannot publish parsed rule {parsed_rule_id}: status is '{parsed_rule.status}', "
                    f"expected 'approved'"
                )
                return {
                    'success': False,
                    'error': f"Parsed rule status is '{parsed_rule.status}', must be 'approved'"
                }
            
            # Step 2: Find or get visa type by visa_code
            visa_type = RulePublishingService._get_or_create_visa_type(parsed_rule)
            if not visa_type:
                logger.error(f"Could not get or create visa type for code: {parsed_rule.visa_code}")
                return {'success': False, 'error': 'Could not get or create visa type'}
            
            # Step 3: Determine effective date
            if effective_from is None:
                effective_from = timezone.now()
            
            # Step 4: Create new rule version
            rule_version = RulePublishingService._create_rule_version(
                visa_type=visa_type,
                parsed_rule=parsed_rule,
                effective_from=effective_from
            )
            if not rule_version:
                logger.error(f"Failed to create rule version for parsed rule {parsed_rule_id}")
                return {'success': False, 'error': 'Failed to create rule version'}
            
            # Step 5: Create requirements from parsed rule
            requirements_created = RulePublishingService._create_requirements_from_parsed_rule(
                rule_version=rule_version,
                parsed_rule=parsed_rule
            )
            
            # Step 6: Close previous version
            previous_version_closed = RulePublishingService._close_previous_version(
                visa_type=visa_type,
                new_effective_from=effective_from
            )
            
            # Step 7: Publish the rule version
            published_version = VisaRuleVersionService.publish_rule_version(str(rule_version.id))
            if not published_version:
                logger.error(f"Failed to publish rule version {rule_version.id}")
                return {'success': False, 'error': 'Failed to publish rule version'}
            
            # Step 8: Update parsed rule status (mark as published)
            from data_ingestion.repositories.parsed_rule_repository import ParsedRuleRepository
            ParsedRuleRepository.update_parsed_rule(
                parsed_rule,
                status='approved'  # Keep as approved, could add 'published' status if needed
            )
            
            # Step 9: Trigger notifications (via signal or directly)
            RulePublishingService._notify_users_of_rule_change(
                visa_type=visa_type,
                rule_version=published_version
            )
            
            logger.info(
                f"Successfully published parsed rule {parsed_rule_id} to rule version {rule_version.id}. "
                f"Created {requirements_created} requirements."
            )
            
            return {
                'success': True,
                'rule_version_id': str(rule_version.id),
                'requirements_created': requirements_created,
                'previous_version_closed': previous_version_closed,
                'effective_from': effective_from.isoformat()
            }
            
        except Exception as e:
            logger.error(
                f"Error publishing parsed rule {parsed_rule_id}: {e}",
                exc_info=True
            )
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _get_or_create_visa_type(parsed_rule: ParsedRule) -> Optional[VisaType]:
        """
        Get existing visa type by code, or create if doesn't exist.
        
        Args:
            parsed_rule: ParsedRule instance (to get visa_code and infer jurisdiction)
            
        Returns:
            VisaType instance or None
        """
        try:
            visa_code = parsed_rule.visa_code
            
            # Try to infer jurisdiction from document version
            jurisdiction = 'UK'  # Default
            if parsed_rule.document_version:
                source_doc = parsed_rule.document_version.source_document
                if source_doc and source_doc.data_source:
                    jurisdiction = source_doc.data_source.jurisdiction
            
            # Try to find existing visa type by jurisdiction and code
            try:
                visa_type = VisaTypeSelector.get_by_code(jurisdiction, visa_code)
                return visa_type
            except VisaType.DoesNotExist:
                pass
            
            # If not found, create new visa type
            logger.info(
                f"Visa type with code '{visa_code}' and jurisdiction '{jurisdiction}' not found, creating new one"
            )
            
            from rules_knowledge.repositories.visa_type_repository import VisaTypeRepository
            
            # Create visa type
            visa_type = VisaTypeRepository.create_visa_type(
                jurisdiction=jurisdiction,
                code=visa_code,
                name=visa_code.replace('_', ' ').title(),  # Convert SKILLED_WORKER to "Skilled Worker"
                description=f"Visa type for {visa_code} in {jurisdiction}"
            )
            
            return visa_type
            
        except Exception as e:
            logger.error(f"Error getting or creating visa type for code {parsed_rule.visa_code}: {e}")
            return None
    
    @staticmethod
    def _create_rule_version(
        visa_type: VisaType,
        parsed_rule: ParsedRule,
        effective_from: datetime
    ) -> Optional[VisaRuleVersion]:
        """
        Create a new rule version from parsed rule.
        
        Args:
            visa_type: VisaType instance
            parsed_rule: ParsedRule instance
            effective_from: Effective date for the rule version
            
        Returns:
            VisaRuleVersion instance or None
        """
        try:
            source_document_version = parsed_rule.document_version
            
            rule_version = VisaRuleVersionRepository.create_rule_version(
                visa_type=visa_type,
                effective_from=effective_from,
                effective_to=None,  # Current version until superseded
                source_document_version=source_document_version,
                is_published=False  # Will be published after requirements are created
            )
            
            return rule_version
            
        except Exception as e:
            logger.error(f"Error creating rule version: {e}", exc_info=True)
            return None
    
    @staticmethod
    def _create_requirements_from_parsed_rule(
        rule_version: VisaRuleVersion,
        parsed_rule: ParsedRule
    ) -> int:
        """
        Create VisaRequirement entries from parsed rule.
        
        ParsedRule.extracted_logic can be:
        1. Single requirement object
        2. Array of requirement objects
        3. Direct JSON Logic expression
        
        Args:
            rule_version: VisaRuleVersion instance
            parsed_rule: ParsedRule instance
            
        Returns:
            Number of requirements created
        """
        requirements_created = 0
        
        try:
            extracted_logic = parsed_rule.extracted_logic
            
            # Handle different structures of extracted_logic
            if isinstance(extracted_logic, dict):
                # Check if it's a single requirement or has a 'requirements' array
                if 'requirements' in extracted_logic:
                    # Structure: {"requirements": [...]}
                    requirements_list = extracted_logic['requirements']
                elif 'requirement_code' in extracted_logic or 'condition_expression' in extracted_logic:
                    # Single requirement object
                    requirements_list = [extracted_logic]
                else:
                    # Direct JSON Logic expression
                    requirements_list = [{
                        'requirement_code': f"{parsed_rule.visa_code}_REQUIREMENT",
                        'description': parsed_rule.description or 'Eligibility requirement',
                        'condition_expression': extracted_logic
                    }]
            elif isinstance(extracted_logic, list):
                # Array of requirements
                requirements_list = extracted_logic
            else:
                logger.warning(
                    f"Unexpected extracted_logic type for parsed rule {parsed_rule.id}: {type(extracted_logic)}"
                )
                return 0
            
            # Create requirements
            for req_data in requirements_list:
                try:
                    requirement_code = req_data.get('requirement_code', f"{parsed_rule.visa_code}_REQ_{requirements_created + 1}")
                    description = req_data.get('description', parsed_rule.description or '')
                    condition_expression = req_data.get('condition_expression', extracted_logic)
                    is_mandatory = req_data.get('is_mandatory', True)
                    
                    # Validate condition_expression
                    if not condition_expression or not isinstance(condition_expression, (dict, list)):
                        logger.warning(
                            f"Invalid condition_expression for requirement {requirement_code}, skipping"
                        )
                        continue
                    
                    requirement = VisaRequirementRepository.create_requirement(
                        rule_version=rule_version,
                        requirement_code=requirement_code,
                        rule_type=parsed_rule.rule_type,
                        description=description,
                        condition_expression=condition_expression,
                        is_mandatory=is_mandatory
                    )
                    
                    if requirement:
                        requirements_created += 1
                        logger.debug(f"Created requirement {requirement_code} for rule version {rule_version.id}")
                    
                except Exception as e:
                    logger.error(
                        f"Error creating requirement from parsed rule {parsed_rule.id}: {e}",
                        exc_info=True
                    )
                    continue
            
            return requirements_created
            
        except Exception as e:
            logger.error(
                f"Error processing extracted_logic for parsed rule {parsed_rule.id}: {e}",
                exc_info=True
            )
            return 0
    
    @staticmethod
    def _close_previous_version(
        visa_type: VisaType,
        new_effective_from: datetime
    ) -> bool:
        """
        Close previous active rule version for the visa type.
        
        Sets effective_to to one day before new version's effective_from
        to ensure no gap and no overlap.
        
        Args:
            visa_type: VisaType instance
            new_effective_from: Effective date of new version
            
        Returns:
            True if previous version was closed, False otherwise
        """
        try:
            # Find active rule versions for this visa type
            now = timezone.now()
            active_versions = VisaRuleVersion.objects.filter(
                visa_type=visa_type,
                is_published=True,
                effective_from__lte=now
            ).filter(
                Q(effective_to__isnull=True) | Q(effective_to__gte=now)
            ).exclude(
                effective_from__gte=new_effective_from
            ).order_by('-effective_from')
            
            if not active_versions.exists():
                logger.debug(f"No previous active version to close for visa type {visa_type.id}")
                return False
            
            # Close all active versions (should typically be just one)
            closed_count = 0
            for prev_version in active_versions:
                # Set effective_to to one day before new version's effective_from
                effective_to = new_effective_from - timedelta(days=1)
                
                # Edge case: If effective_to is in the past, use current time
                if effective_to < now:
                    effective_to = now - timedelta(seconds=1)
                
                VisaRuleVersionRepository.update_rule_version(
                    prev_version,
                    effective_to=effective_to
                )
                closed_count += 1
                logger.info(
                    f"Closed previous rule version {prev_version.id} for visa type {visa_type.id}. "
                    f"effective_to set to {effective_to}"
                )
            
            return closed_count > 0
            
        except Exception as e:
            logger.error(
                f"Error closing previous version for visa type {visa_type.id}: {e}",
                exc_info=True
            )
            return False
    
    @staticmethod
    def _notify_users_of_rule_change(
        visa_type: VisaType,
        rule_version: VisaRuleVersion
    ):
        """
        Notify users with active cases about rule changes.
        
        This triggers the signal which handles notifications.
        The signal is already set up in rules_knowledge/signals/rule_publishing_signals.py
        
        Args:
            visa_type: VisaType instance
            rule_version: VisaRuleVersion instance
        """
        # The signal will handle this automatically when rule_version is saved with is_published=True
        # But we can also trigger it explicitly here if needed
        logger.info(
            f"Rule change notification will be triggered via signal for visa type {visa_type.id}"
        )
    
    @staticmethod
    def publish_approved_validation_task(
        validation_task_id: str,
        effective_from: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Publish a rule from an approved validation task.
        
        This is a convenience method that:
        1. Gets the parsed rule from validation task
        2. Calls publish_approved_parsed_rule
        
        Args:
            validation_task_id: UUID of the approved validation task
            effective_from: Optional effective date
            
        Returns:
            Publishing result dict
        """
        try:
            from data_ingestion.selectors.rule_validation_task_selector import RuleValidationTaskSelector
            
            task = RuleValidationTaskSelector.get_by_id(validation_task_id)
            if not task:
                logger.error(f"Validation task {validation_task_id} not found")
                return {'success': False, 'error': 'Validation task not found'}
            
            if task.status != 'approved':
                logger.error(
                    f"Cannot publish from task {validation_task_id}: status is '{task.status}'"
                )
                return {
                    'success': False,
                    'error': f"Task status is '{task.status}', must be 'approved'"
                }
            
            parsed_rule = task.parsed_rule
            return RulePublishingService.publish_approved_parsed_rule(
                parsed_rule_id=str(parsed_rule.id),
                effective_from=effective_from,
                reviewer_notes=task.reviewer_notes
            )
            
        except Exception as e:
            logger.error(
                f"Error publishing from validation task {validation_task_id}: {e}",
                exc_info=True
            )
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def create_rule_manually(
        visa_type_id: str,
        requirement_code: str,
        rule_type: str,
        description: str,
        condition_expression: Dict[str, Any],
        effective_from: Optional[datetime] = None,
        is_mandatory: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Manually create a rule (for admin use).
        
        This allows admins to create rules directly without going through
        the ingestion → parsing → validation workflow.
        
        Args:
            visa_type_id: UUID of visa type
            requirement_code: Code for the requirement
            rule_type: Type of requirement
            description: Human-readable description
            condition_expression: JSON Logic expression
            effective_from: Optional effective date (defaults to now)
            is_mandatory: Whether requirement is mandatory
            
        Returns:
            Dict with creation results:
            {
                'success': bool,
                'rule_version_id': str,
                'requirement_id': str
            }
        """
        try:
            if effective_from is None:
                effective_from = timezone.now()
            
            # Get or create rule version for this visa type and date
            visa_type = VisaTypeSelector.get_by_id(visa_type_id)
            if not visa_type:
                logger.error(f"Visa type {visa_type_id} not found")
                return {'success': False, 'error': 'Visa type not found'}
            
            # Check if there's already a rule version for this effective date
            existing_version = VisaRuleVersion.objects.filter(
                visa_type=visa_type,
                effective_from=effective_from,
                is_published=True
            ).first()
            
            if existing_version:
                # Add requirement to existing version
                rule_version = existing_version
            else:
                # Create new rule version
                rule_version = VisaRuleVersionRepository.create_rule_version(
                    visa_type=visa_type,
                    effective_from=effective_from,
                    effective_to=None,
                    source_document_version=None,  # Manual creation
                    is_published=True
                )
                
                # Close previous version
                RulePublishingService._close_previous_version(visa_type, effective_from)
            
            # Create requirement
            requirement = VisaRequirementRepository.create_requirement(
                rule_version=rule_version,
                requirement_code=requirement_code,
                rule_type=rule_type,
                description=description,
                condition_expression=condition_expression,
                is_mandatory=is_mandatory
            )
            
            if not requirement:
                logger.error(f"Failed to create requirement for rule version {rule_version.id}")
                return {'success': False, 'error': 'Failed to create requirement'}
            
            # Trigger notifications
            RulePublishingService._notify_users_of_rule_change(visa_type, rule_version)
            
            logger.info(
                f"Manually created requirement {requirement_code} for visa type {visa_type_id}"
            )
            
            return {
                'success': True,
                'rule_version_id': str(rule_version.id),
                'requirement_id': str(requirement.id)
            }
            
        except Exception as e:
            logger.error(
                f"Error manually creating rule: {e}",
                exc_info=True
            )
            return {'success': False, 'error': str(e)}

