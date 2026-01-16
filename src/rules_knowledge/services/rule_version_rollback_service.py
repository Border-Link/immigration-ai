"""
Rule Version Rollback Service

Handles rolling back to previous rule versions.
"""
import logging
from typing import Optional, Dict, Any
from django.utils import timezone
from django.db import transaction
from rules_knowledge.models.visa_rule_version import VisaRuleVersion
from rules_knowledge.selectors.visa_rule_version_selector import VisaRuleVersionSelector
from rules_knowledge.repositories.visa_rule_version_repository import VisaRuleVersionRepository
from rules_knowledge.services.rule_version_conflict_service import RuleVersionConflictService

logger = logging.getLogger('django')


class RuleVersionRollbackService:
    """Service for rolling back rule versions."""
    
    @staticmethod
    def rollback_to_version(
        current_version_id: str,
        rollback_to_version_id: str,
        rollback_by=None
    ) -> Dict[str, Any]:
        """
        Rollback current version to a previous version.
        
        Args:
            current_version_id: UUID of current rule version to close
            rollback_to_version_id: UUID of previous version to reopen
            rollback_by: User performing the rollback
            
        Returns:
            Dict with rollback results:
            {
                'success': bool,
                'current_version_closed': bool,
                'previous_version_reopened': bool,
                'error': str (if failed)
            }
        """
        try:
            with transaction.atomic():
                # Get versions (selectors raise DoesNotExist; normalize to clean "not found" errors)
                try:
                    current_version = VisaRuleVersionSelector.get_by_id(current_version_id, include_deleted=True)
                except VisaRuleVersion.DoesNotExist:
                    return {'success': False, 'error': f"Current version {current_version_id} not found"}

                try:
                    previous_version = VisaRuleVersionSelector.get_by_id(rollback_to_version_id, include_deleted=True)
                except VisaRuleVersion.DoesNotExist:
                    return {'success': False, 'error': f"Previous version {rollback_to_version_id} not found"}
                
                # Use a single timestamp to avoid boundary overlaps
                now = timezone.now()
                
                # Verify they're for the same visa type
                if current_version.visa_type_id != previous_version.visa_type_id:
                    return {
                        'success': False,
                        'error': "Versions must be for the same visa type"
                    }
                
                # Verify previous version is actually before current
                if previous_version.effective_from >= current_version.effective_from:
                    return {
                        'success': False,
                        'error': "Previous version must have an earlier effective_from date"
                    }
                
                # Close current version
                current_closed = False
                if current_version.is_published and (not current_version.effective_to or current_version.effective_to > now):
                    # Set effective_to to just before "now" so the reopened version can start at "now"
                    VisaRuleVersionRepository.update_rule_version(
                        current_version,
                        updated_by=rollback_by,
                        effective_to=now - timezone.timedelta(microseconds=1)
                    )
                    current_closed = True
                
                # Reopen previous version
                previous_reopened = False
                if previous_version.is_deleted:
                    # Undo soft delete
                    previous_version.is_deleted = False
                    previous_version.deleted_at = None
                    previous_version.save()
                    previous_reopened = True
                
                # If previous version was unpublished, republish it
                if not previous_version.is_published:
                    VisaRuleVersionRepository.publish_rule_version(
                        previous_version,
                        published_by=rollback_by
                    )
                    previous_reopened = True
                
                # Set effective_to to None to make it current
                # Important: avoid overlaps by making the reopened version effective from "now"
                # (this is a rollback action, not historical rewriting of past periods).
                if previous_version.effective_to is not None or previous_version.effective_from != now:
                    VisaRuleVersionRepository.update_rule_version(
                        previous_version,
                        updated_by=rollback_by,
                        effective_from=now,
                        effective_to=None
                    )
                    previous_reopened = True
                
                logger.info(
                    f"Rolled back rule version {current_version_id} to {rollback_to_version_id} "
                    f"by user {rollback_by.id if rollback_by else 'system'}"
                )
                
                return {
                    'success': True,
                    'current_version_closed': current_closed,
                    'previous_version_reopened': previous_reopened,
                    'current_version_id': str(current_version.id),
                    'previous_version_id': str(previous_version.id)
                }
                
        except Exception as e:
            logger.error(f"Error rolling back rule version: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
