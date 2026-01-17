import logging
from typing import Optional
from main_system.utils.cache_utils import cache_result, invalidate_cache
from data_ingestion.models.rule_validation_task import RuleValidationTask
from data_ingestion.repositories.rule_validation_task_repository import RuleValidationTaskRepository
from data_ingestion.selectors.rule_validation_task_selector import RuleValidationTaskSelector

logger = logging.getLogger('django')

def namespace(*args, **kwargs) -> str:
    return "rule_validation_tasks"


class RuleValidationTaskService:
    """Service for RuleValidationTask business logic."""

    @staticmethod
    @cache_result(timeout=120, keys=[], namespace=namespace, user_scope="global")
    def get_all():
        """Get all validation tasks."""
        try:
            return RuleValidationTaskSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all validation tasks: {e}")
            return RuleValidationTaskSelector.get_none()

    @staticmethod
    @cache_result(timeout=120, keys=['status'], namespace=namespace, user_scope="global")
    def get_by_status(status: str):
        """Get validation tasks by status."""
        try:
            return RuleValidationTaskSelector.get_by_status(status)
        except Exception as e:
            logger.error(f"Error fetching validation tasks by status {status}: {e}")
            return RuleValidationTaskSelector.get_none()

    @staticmethod
    @cache_result(timeout=120, keys=['reviewer_id'], namespace=namespace, user_scope="global")
    def get_by_reviewer(reviewer_id: str):
        """Get validation tasks assigned to a reviewer."""
        try:
            from users_access.selectors.user_selector import UserSelector
            reviewer = UserSelector.get_by_id(reviewer_id)
            if not reviewer:
                return RuleValidationTaskSelector.get_none()
            return RuleValidationTaskSelector.get_by_reviewer(reviewer)
        except Exception as e:
            logger.error(f"Error fetching validation tasks for reviewer {reviewer_id}: {e}")
            return RuleValidationTaskSelector.get_none()

    @staticmethod
    @cache_result(timeout=60, keys=[], namespace=namespace, user_scope="global")
    def get_pending():
        """Get all pending validation tasks."""
        try:
            return RuleValidationTaskSelector.get_pending()
        except Exception as e:
            logger.error(f"Error fetching pending validation tasks: {e}")
            return RuleValidationTaskSelector.get_none()

    @staticmethod
    @cache_result(timeout=300, keys=['task_id'], namespace=namespace, user_scope="global")
    def get_by_id(task_id: str) -> Optional[RuleValidationTask]:
        """Get validation task by ID."""
        try:
            task = RuleValidationTaskSelector.get_by_id(task_id)
            if not task:
                logger.error(f"Validation task {task_id} not found")
                return None
            return task
        except Exception as e:
            logger.error(f"Error fetching validation task {task_id}: {e}")
            return None

    @staticmethod
    @invalidate_cache(namespace, predicate=lambda t: t is not None)
    def assign_reviewer(task_id: str, reviewer_id: str, version: int = None) -> Optional[RuleValidationTask]:
        """Assign a reviewer to a validation task."""
        try:
            task = RuleValidationTaskSelector.get_by_id(task_id)
            if not task:
                logger.error(f"Validation task {task_id} not found")
                return None
            from users_access.selectors.user_selector import UserSelector
            reviewer = UserSelector.get_by_id(reviewer_id)
            if not reviewer:
                logger.error(f"Reviewer {reviewer_id} not found")
                return None
            return RuleValidationTaskRepository.assign_reviewer(
                task,
                reviewer,
                version=version if version is not None else getattr(task, "version", None),
            )
        except Exception as e:
            logger.error(f"Error assigning reviewer to task {task_id}: {e}")
            return None

    @staticmethod
    @invalidate_cache(namespace, predicate=lambda t: t is not None)
    def update_task(task_id: str, **fields) -> Optional[RuleValidationTask]:
        """Update validation task fields."""
        try:
            task = RuleValidationTaskSelector.get_by_id(task_id)
            if not task:
                logger.error(f"Validation task {task_id} not found")
                return None
            expected_version = fields.pop("version", None)
            return RuleValidationTaskRepository.update_validation_task(
                task,
                version=expected_version if expected_version is not None else getattr(task, "version", None),
                **fields
            )
        except Exception as e:
            logger.error(f"Error updating validation task {task_id}: {e}")
            return None

    @staticmethod
    @invalidate_cache(namespace, predicate=lambda t: t is not None)
    def approve_task(task_id: str, reviewer_notes: str = None, auto_publish: bool = True, version: int = None) -> Optional[RuleValidationTask]:
        """
        Approve a validation task.
        
        Args:
            task_id: UUID of the validation task
            reviewer_notes: Optional notes from reviewer
            auto_publish: Whether to automatically publish the rule after approval (default: True)
            
        Returns:
            Updated RuleValidationTask or None
        """
        try:
            task = RuleValidationTaskSelector.get_by_id(task_id)
            if not task:
                logger.error(f"Validation task {task_id} not found")
                return None
            
            update_fields = {'status': 'approved'}
            if reviewer_notes:
                update_fields['reviewer_notes'] = reviewer_notes
            
            updated_task = RuleValidationTaskRepository.update_validation_task(
                task,
                version=version if version is not None else getattr(task, "version", None),
                **update_fields
            )
            
            # Update parsed rule status to approved
            if updated_task and updated_task.parsed_rule:
                # Use service to ensure cache invalidation happens.
                from data_ingestion.services.parsed_rule_service import ParsedRuleService
                ParsedRuleService.update_status(str(updated_task.parsed_rule.id), status="approved")
            
            # Auto-publish if enabled
            if auto_publish and updated_task:
                try:
                    from rules_knowledge.services.rule_publishing_service import RulePublishingService
                    publish_result = RulePublishingService.publish_approved_validation_task(
                        validation_task_id=task_id
                    )
                    if publish_result.get('success'):
                        logger.info(
                            f"Auto-published rule from validation task {task_id}. "
                            f"Rule version: {publish_result.get('rule_version_id')}"
                        )
                    else:
                        logger.warning(
                            f"Auto-publish failed for validation task {task_id}: "
                            f"{publish_result.get('error')}"
                        )
                except Exception as e:
                    logger.error(
                        f"Error auto-publishing rule from validation task {task_id}: {e}",
                        exc_info=True
                    )
                    # Don't fail the approval if publishing fails
            
            return updated_task
        except Exception as e:
            logger.error(f"Error approving validation task {task_id}: {e}")
            return None

    @staticmethod
    @invalidate_cache(namespace, predicate=lambda t: t is not None)
    def reject_task(task_id: str, reviewer_notes: str = None, version: int = None) -> Optional[RuleValidationTask]:
        """Reject a validation task."""
        try:
            task = RuleValidationTaskSelector.get_by_id(task_id)
            if not task:
                logger.error(f"Validation task {task_id} not found")
                return None
            update_fields = {'status': 'rejected'}
            if reviewer_notes:
                update_fields['reviewer_notes'] = reviewer_notes
            return RuleValidationTaskRepository.update_validation_task(
                task,
                version=version if version is not None else getattr(task, "version", None),
                **update_fields
            )
        except Exception as e:
            logger.error(f"Error rejecting validation task {task_id}: {e}")
            return None

    @staticmethod
    @invalidate_cache(namespace, predicate=bool)
    def delete_validation_task(task_id: str) -> bool:
        """Delete a validation task."""
        try:
            task = RuleValidationTaskSelector.get_by_id(task_id)
            if not task:
                logger.error(f"Validation task {task_id} not found")
                return False
            RuleValidationTaskRepository.delete_validation_task(task, version=getattr(task, "version", None))
            return True
        except Exception as e:
            logger.error(f"Error deleting validation task {task_id}: {e}")
            return False

    @staticmethod
    def get_by_filters(status: str = None, assigned_to: str = None, date_from=None, date_to=None, sla_overdue: bool = None):
        """Get validation tasks with filters."""
        try:
            return RuleValidationTaskSelector.get_by_filters(
                status=status,
                assigned_to_id=assigned_to,
                date_from=date_from,
                date_to=date_to,
                sla_overdue=sla_overdue
            )
        except Exception as e:
            logger.error(f"Error fetching filtered validation tasks: {e}")
            return RuleValidationTaskSelector.get_none()

    @staticmethod
    @cache_result(timeout=120, keys=[], namespace=namespace, user_scope="global")
    def get_statistics():
        """Get validation task statistics."""
        try:
            return RuleValidationTaskSelector.get_statistics()
        except Exception as e:
            logger.error(f"Error getting validation task statistics: {e}")
            return {}
