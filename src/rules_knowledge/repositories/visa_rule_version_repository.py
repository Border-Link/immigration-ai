from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from rules_knowledge.models.visa_rule_version import VisaRuleVersion
from rules_knowledge.models.visa_type import VisaType
from rules_knowledge.services.rule_version_conflict_service import RuleVersionConflictService
from rules_knowledge.helpers.metrics import track_version_conflict


class VisaRuleVersionRepository:
    """Repository for VisaRuleVersion write operations."""

    @staticmethod
    def create_rule_version(
        visa_type: VisaType,
        effective_from,
        effective_to=None,
        source_document_version=None,
        is_published: bool = False,
        created_by=None,
        check_conflicts: bool = True
    ):
        """Create a new rule version with conflict detection."""
        # Check for conflicts if enabled
        if check_conflicts:
            can_create, conflicts = RuleVersionConflictService.can_create_version(
                str(visa_type.id),
                effective_from,
                effective_to,
                allow_overlap_with_unpublished=not is_published
            )
            
            if not can_create and conflicts:
                conflict_details = ', '.join([f"{c['conflict_type']} with version {c['rule_version_id']}" for c in conflicts])
                raise ValidationError(
                    f"Cannot create rule version: conflicts detected. {conflict_details}"
                )
        
        # Validate effective date range
        if effective_to and effective_to < effective_from:
            raise ValidationError("effective_to must be after effective_from")
        
        # Validate past effective dates for published rules
        if is_published and effective_from < timezone.now() - timezone.timedelta(days=1):
            # Allow but log warning - may be intentional for historical rules
            import logging
            logger = logging.getLogger('django')
            logger.warning(
                f"Creating published rule version with past effective_from: {effective_from}"
            )
        
        with transaction.atomic():
            # Set effective_to on previous current version if exists
            if effective_to is None:
                previous_versions = VisaRuleVersion.objects.filter(
                    visa_type=visa_type,
                    effective_to__isnull=True,
                    is_deleted=False
                )
                for prev_version in previous_versions:
                    prev_version.effective_to = effective_from
                    prev_version.save()
            
            rule_version = VisaRuleVersion.objects.create(
                visa_type=visa_type,
                effective_from=effective_from,
                effective_to=effective_to,
                source_document_version=source_document_version,
                is_published=is_published,
                created_by=created_by
            )
            rule_version.full_clean()
            rule_version.save()
            return rule_version

    @staticmethod
    def update_rule_version(rule_version, updated_by=None, expected_version=None, **fields):
        """
        Update rule version fields with validation and optimistic locking.
        
        Args:
            rule_version: VisaRuleVersion instance to update
            updated_by: User performing the update
            expected_version: Expected version number for optimistic locking (None to skip check)
            **fields: Fields to update
            
        Returns:
            Updated VisaRuleVersion instance
            
        Raises:
            ValidationError: If version conflict detected or validation fails
        """
        with transaction.atomic():
            # Optimistic locking: Check version if expected_version provided
            if expected_version is not None:
                # Reload from database with select_for_update to lock the row
                current = VisaRuleVersion.objects.select_for_update().get(id=rule_version.id)
                if current.version != expected_version:
                    # Track version conflict metric
                    track_version_conflict('update')
                    raise ValidationError(
                        f"Version conflict: Rule version was modified by another user. "
                        f"Expected version {expected_version}, but current version is {current.version}. "
                        f"Please refresh and try again."
                    )
                # Use the locked instance
                rule_version = current
            
            # Validate effective date range if being updated
            effective_from = fields.get('effective_from', rule_version.effective_from)
            effective_to = fields.get('effective_to', rule_version.effective_to)
            
            if effective_to and effective_to < effective_from:
                raise ValidationError("effective_to must be after effective_from")
            
            # Check for conflicts if effective dates are being changed
            if 'effective_from' in fields or 'effective_to' in fields:
                can_create, conflicts = RuleVersionConflictService.can_create_version(
                    str(rule_version.visa_type.id),
                    effective_from,
                    effective_to,
                    allow_overlap_with_unpublished=True  # Allow overlap with self
                )
                
                # Filter out self from conflicts
                conflicts = [c for c in conflicts if c['rule_version_id'] != str(rule_version.id)]
                
                if conflicts:
                    conflict_details = ', '.join([f"{c['conflict_type']} with version {c['rule_version_id']}" for c in conflicts])
                    raise ValidationError(
                        f"Cannot update rule version: conflicts detected. {conflict_details}"
                    )
            
            # Set updated_by if provided
            if updated_by:
                fields['updated_by'] = updated_by
            
            # Update fields
            for key, value in fields.items():
                if hasattr(rule_version, key):
                    setattr(rule_version, key, value)
            
            # Increment version (integer) after any optimistic-lock checks.
            # Note: expected_version path uses select_for_update above, which prevents concurrent writes.
            rule_version.version = int(rule_version.version) + 1
            rule_version.full_clean()
            rule_version.save()
            
            # Reload to get the updated version number
            rule_version.refresh_from_db()
            return rule_version

    @staticmethod
    def publish_rule_version(rule_version, published_by=None, expected_version=None):
        """
        Publish a rule version with optimistic locking support.
        
        Args:
            rule_version: VisaRuleVersion instance to publish
            published_by: User performing the publish
            expected_version: Expected version number for optimistic locking (None to skip check)
            
        Returns:
            Published VisaRuleVersion instance
            
        Raises:
            ValidationError: If version conflict detected
        """
        with transaction.atomic():
            # Optimistic locking: Check version if expected_version provided
            if expected_version is not None:
                current = VisaRuleVersion.objects.select_for_update().get(id=rule_version.id)
                if current.version != expected_version:
                    # Track version conflict metric
                    track_version_conflict('publish')
                    raise ValidationError(
                        f"Version conflict: Rule version was modified by another user. "
                        f"Expected version {expected_version}, but current version is {current.version}. "
                        f"Please refresh and try again."
                    )
                rule_version = current
            
            rule_version.is_published = True
            rule_version.published_at = timezone.now()
            if published_by:
                rule_version.published_by = published_by
            
            # Increment version (integer) after any optimistic-lock checks.
            rule_version.version = int(rule_version.version) + 1
            rule_version.full_clean()
            rule_version.save()
            
            # Reload to get the updated version number
            rule_version.refresh_from_db()
            return rule_version

    @staticmethod
    def delete_rule_version(rule_version, check_references: bool = True):
        """
        Soft delete a rule version with reference checking.
        
        Args:
            rule_version: VisaRuleVersion instance
            check_references: If True, check for references before deleting
        """
        with transaction.atomic():
            # Check for references if enabled
            if check_references:
                # Check eligibility results
                from ai_decisions.selectors.eligibility_result_selector import EligibilityResultSelector
                eligibility_results = EligibilityResultSelector.get_by_rule_version(str(rule_version.id))
                if eligibility_results.exists():
                    raise ValidationError(
                        f"Cannot delete rule version {rule_version.id}: "
                        f"referenced by {eligibility_results.count()} eligibility results"
                    )
            
            # Soft delete
            rule_version.is_deleted = True
            rule_version.deleted_at = timezone.now()
            rule_version.save()
