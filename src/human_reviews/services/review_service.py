import logging
import time
from typing import Optional
from django.utils import timezone
from main_system.utils.cache_utils import cache_result
from human_reviews.models.review import Review
from human_reviews.repositories.review_repository import ReviewRepository
from human_reviews.selectors.review_selector import ReviewSelector
from immigration_cases.selectors.case_selector import CaseSelector
from users_access.selectors.user_selector import UserSelector
from users_access.services.user_service import UserService
from compliance.services.audit_log_service import AuditLogService
from human_reviews.helpers.metrics import (
    track_review_creation,
    track_review_assignment,
    track_review_status_transition,
    track_review_version_conflict
)

logger = logging.getLogger('django')


class ReviewService:
    """Service for Review business logic."""

    @staticmethod
    def create_review(case_id: str, reviewer_id: str = None, auto_assign: bool = True,
                     assignment_strategy: str = 'round_robin'):
        """
        Create a new review.
        
        Requires: Case must have a completed payment before reviews can be created.
        
        Args:
            case_id: Case ID
            reviewer_id: Optional reviewer ID (if provided, auto_assign is ignored)
            auto_assign: Whether to automatically assign a reviewer
            assignment_strategy: 'round_robin' or 'workload'
        """
        from django.core.exceptions import ValidationError
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            case = CaseSelector.get_by_id(case_id)
            if not case:
                logger.error(f"Case {case_id} not found when creating review")
                return None
            
            # Validate payment requirement
            is_valid, error = PaymentValidator.validate_case_has_payment(case, operation_name="review creation")
            if not is_valid:
                logger.warning(f"Review creation blocked for case {case_id}: {error}")
                raise ValidationError(error)
            
            reviewer = None
            if reviewer_id:
                reviewer = UserSelector.get_by_id(reviewer_id)
                # Verify reviewer has reviewer role AND is staff or admin
                if reviewer.role != 'reviewer':
                    logger.error(f"User {reviewer_id} does not have reviewer role")
                    return None
                if not (reviewer.is_staff or reviewer.is_superuser):
                    logger.error(f"User {reviewer_id} is not staff or admin")
                    return None
            elif auto_assign:
                # Auto-assign reviewer based on strategy
                if assignment_strategy == 'workload':
                    reviewer = UserSelector.get_reviewer_by_workload()
                else:
                    reviewer = UserSelector.get_reviewer_round_robin()
                
                if reviewer:
                    # Update last_assigned_at for round-robin tracking
                    UserService.update_user_last_assigned_at(reviewer)
            
            review = ReviewRepository.create_review(case=case, reviewer=reviewer)
            
            # Track metrics
            assignment_type = 'manual' if reviewer_id else ('round_robin' if assignment_strategy == 'round_robin' else 'workload')
            track_review_creation(assignment_type=assignment_type)
            if reviewer:
                track_review_assignment(assignment_strategy=assignment_strategy)
            
            # Log audit event
            try:
                AuditLogService.create_audit_log(
                    level='INFO',
                    logger_name='human_reviews',
                    message=f"Review created for case {case_id}",
                    func_name='create_review',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return review
        except Exception as e:
            logger.error(f"Error creating review: {e}")
            return None

    @staticmethod
    @cache_result(timeout=300, keys=[])  # 5 minutes - review list changes frequently
    def get_all():
        """Get all reviews."""
        try:
            return ReviewSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all reviews: {e}")
            return Review.objects.none()

    @staticmethod
    @cache_result(timeout=300, keys=['case_id'])  # 5 minutes - cache reviews by case
    def get_by_case(case_id: str):
        """Get reviews by case."""
        try:
            case = CaseSelector.get_by_id(case_id)
            return ReviewSelector.get_by_case(case)
        except Exception as e:
            logger.error(f"Error fetching reviews for case {case_id}: {e}")
            return Review.objects.none()

    @staticmethod
    @cache_result(timeout=300, keys=['status'])  # 5 minutes - cache reviews by status
    def get_by_status(status: str):
        """Get reviews by status."""
        try:
            return ReviewSelector.get_by_status(status)
        except Exception as e:
            logger.error(f"Error fetching reviews by status {status}: {e}")
            return Review.objects.none()

    @staticmethod
    @cache_result(timeout=300, keys=['reviewer_id'])  # 5 minutes - cache reviews by reviewer
    def get_by_reviewer(reviewer_id: str):
        """Get reviews by reviewer."""
        try:
            reviewer = UserSelector.get_by_id(reviewer_id)
            return ReviewSelector.get_by_reviewer(reviewer)
        except Exception as e:
            logger.error(f"Error fetching reviews for reviewer {reviewer_id}: {e}")
            return Review.objects.none()

    @staticmethod
    @cache_result(timeout=180, keys=['reviewer_id'])  # 3 minutes - pending reviews change frequently
    def get_pending_by_reviewer(reviewer_id: str):
        """Get pending/in_progress reviews by reviewer."""
        try:
            reviewer = UserSelector.get_by_id(reviewer_id)
            return ReviewSelector.get_pending_by_reviewer(reviewer)
        except Exception as e:
            logger.error(f"Error fetching pending reviews for reviewer {reviewer_id}: {e}")
            return Review.objects.none()

    @staticmethod
    @cache_result(timeout=180, keys=[])  # 3 minutes - pending reviews change frequently
    def get_pending():
        """Get all pending reviews (not assigned)."""
        try:
            return ReviewSelector.get_pending()
        except Exception as e:
            logger.error(f"Error fetching pending reviews: {e}")
            return Review.objects.none()

    @staticmethod
    @cache_result(timeout=600, keys=['review_id'])  # 10 minutes - cache review by ID
    def get_by_id(review_id: str) -> Optional[Review]:
        """Get review by ID."""
        try:
            return ReviewSelector.get_by_id(review_id)
        except Review.DoesNotExist:
            logger.error(f"Review {review_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching review {review_id}: {e}")
            return None

    @staticmethod
    def assign_reviewer(review_id: str, reviewer_id: str = None, assignment_strategy: str = 'round_robin', assigned_by_id: str = None) -> Optional[Review]:
        """
        Assign a reviewer to a review.
        
        Requires: Case must have a completed payment before reviewers can be assigned.
        """
        from django.core.exceptions import ValidationError
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            review = ReviewSelector.get_by_id(review_id)
            if not review:
                logger.error(f"Review {review_id} not found")
                return None
            
            # Validate payment requirement
            is_valid, error = PaymentValidator.validate_case_has_payment(review.case, operation_name="review assignment")
            if not is_valid:
                logger.warning(f"Review assignment blocked for case {review.case.id}: {error}")
                raise ValidationError(error)
            
            assigned_by = None
            if assigned_by_id:
                assigned_by = UserSelector.get_by_id(assigned_by_id)
            
            if reviewer_id:
                reviewer = UserSelector.get_by_id(reviewer_id)
                # Verify reviewer has reviewer role AND is staff or admin
                if reviewer.role != 'reviewer':
                    logger.error(f"User {reviewer_id} does not have reviewer role")
                    return None
                if not (reviewer.is_staff or reviewer.is_superuser):
                    logger.error(f"User {reviewer_id} is not staff or admin")
                    return None
            else:
                # Auto-assign based on strategy
                if assignment_strategy == 'workload':
                    reviewer = UserSelector.get_reviewer_by_workload()
                else:
                    reviewer = UserSelector.get_reviewer_round_robin()
                
                if not reviewer:
                    logger.error("No available reviewers found")
                    return None
                
                # Update last_assigned_at for round-robin tracking
                UserService.update_user_last_assigned_at(reviewer)
            
            updated_review = ReviewRepository.assign_reviewer(
                review,
                reviewer,
                changed_by=assigned_by,
                reason=f"Review assigned to {reviewer.email if reviewer else 'None'}"
            )
            
            # Log audit event
            try:
                AuditLogService.create_audit_log(
                    level='INFO',
                    logger_name='human_reviews',
                    message=f"Review {review_id} assigned to {reviewer.email if reviewer else 'None'}",
                    func_name='assign_reviewer',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return updated_review
        except Review.DoesNotExist:
            logger.error(f"Review {review_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error assigning reviewer to review {review_id}: {e}")
            return None

    @staticmethod
    def complete_review(review_id: str, completed_by_id: str = None, reason: str = None) -> Optional[Review]:
        """
        Complete a review.
        
        Requires: Case must have a completed payment before reviews can be completed.
        """
        from django.core.exceptions import ValidationError
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            review = ReviewSelector.get_by_id(review_id)
            if not review:
                logger.error(f"Review {review_id} not found")
                return None
            
            # Validate payment requirement
            is_valid, error = PaymentValidator.validate_case_has_payment(review.case, operation_name="review completion")
            if not is_valid:
                logger.warning(f"Review completion blocked for case {review.case.id}: {error}")
                raise ValidationError(error)
            
            completed_by = None
            if completed_by_id:
                completed_by = UserSelector.get_by_id(completed_by_id)
            
            updated_review = ReviewRepository.complete_review(
                review,
                changed_by=completed_by,
                reason=reason
            )
            
            # Log audit event
            try:
                AuditLogService.create_audit_log(
                    level='INFO',
                    logger_name='human_reviews',
                    message=f"Review {review_id} completed for case {review.case.id}",
                    func_name='complete_review',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return updated_review
        except Review.DoesNotExist:
            logger.error(f"Review {review_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error completing review {review_id}: {e}")
            return None

    @staticmethod
    def cancel_review(review_id: str, cancelled_by_id: str = None, reason: str = None) -> Optional[Review]:
        """
        Cancel a review.
        
        Requires: Case must have a completed payment before reviews can be cancelled.
        """
        from django.core.exceptions import ValidationError
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            review = ReviewSelector.get_by_id(review_id)
            if not review:
                logger.error(f"Review {review_id} not found")
                return None
            
            # Validate payment requirement
            is_valid, error = PaymentValidator.validate_case_has_payment(review.case, operation_name="review cancellation")
            if not is_valid:
                logger.warning(f"Review cancellation blocked for case {review.case.id}: {error}")
                raise ValidationError(error)
            
            cancelled_by = None
            if cancelled_by_id:
                cancelled_by = UserSelector.get_by_id(cancelled_by_id)
            
            updated_review = ReviewRepository.cancel_review(
                review,
                changed_by=cancelled_by,
                reason=reason
            )
            
            # Log audit event
            try:
                AuditLogService.create_audit_log(
                    level='WARNING',
                    logger_name='human_reviews',
                    message=f"Review {review_id} cancelled for case {review.case.id}",
                    func_name='cancel_review',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return updated_review
        except Review.DoesNotExist:
            logger.error(f"Review {review_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error cancelling review {review_id}: {e}")
            return None

    @staticmethod
    def update_review(review_id: str, updated_by_id: str = None, reason: str = None, version: int = None, **fields) -> Optional[Review]:
        """
        Update review fields.
        
        Requires: Case must have a completed payment before reviews can be updated.
        """
        from django.core.exceptions import ValidationError
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            review = ReviewSelector.get_by_id(review_id)
            if not review:
                logger.error(f"Review {review_id} not found")
                return None
            
            # Validate payment requirement
            is_valid, error = PaymentValidator.validate_case_has_payment(review.case, operation_name="review update")
            if not is_valid:
                logger.warning(f"Review update blocked for case {review.case.id}: {error}")
                raise ValidationError(error)
            previous_status = review.status
            
            updated_by = None
            if updated_by_id:
                updated_by = UserSelector.get_by_id(updated_by_id)
            
            updated_review = ReviewRepository.update_review(
                review,
                version=version,
                changed_by=updated_by,
                reason=reason,
                **fields
            )
            
            # Track status transition if status changed
            if 'status' in fields and fields['status'] != previous_status:
                track_review_status_transition(
                    from_status=previous_status,
                    to_status=fields['status']
                )
            
            return updated_review
        except Review.DoesNotExist:
            logger.error(f"Review {review_id} not found")
            return None
        except ValidationError as e:
            # Check if it's a version conflict
            if 'version' in str(e).lower() or 'modified by another user' in str(e):
                track_review_version_conflict(operation='update')
            logger.error(f"Validation error updating review {review_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error updating review {review_id}: {e}")
            return None

    @staticmethod
    def delete_review(review_id: str, deleted_by_id: str = None) -> bool:
        """
        Delete a review.
        
        Requires: Case must have a completed payment before reviews can be deleted.
        This prevents abuse and ensures only paid cases can manage their reviews.
        """
        from django.core.exceptions import ValidationError
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            review = ReviewSelector.get_by_id(review_id)
            if not review:
                logger.error(f"Review {review_id} not found")
                return False
            
            # Validate payment requirement
            is_valid, error = PaymentValidator.validate_case_has_payment(review.case, operation_name="review deletion")
            if not is_valid:
                logger.warning(f"Review deletion blocked for case {review.case.id}: {error}")
                raise ValidationError(error)
            ReviewRepository.delete_review(review)
            
            # Log audit event
            try:
                AuditLogService.create_audit_log(
                    level='WARNING',
                    logger_name='human_reviews',
                    message=f"Review {review_id} deleted",
                    func_name='delete_review',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return True
        except Review.DoesNotExist:
            logger.error(f"Review {review_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting review {review_id}: {e}")
            return False

    @staticmethod
    def get_by_filters(case_id=None, reviewer_id=None, status=None, date_from=None, date_to=None, assigned_date_from=None, assigned_date_to=None, completed_date_from=None, completed_date_to=None):
        """Get reviews with advanced filtering for admin."""
        try:
            return ReviewSelector.get_by_filters(
                case_id=case_id,
                reviewer_id=reviewer_id,
                status=status,
                date_from=date_from,
                date_to=date_to,
                assigned_date_from=assigned_date_from,
                assigned_date_to=assigned_date_to,
                completed_date_from=completed_date_from,
                completed_date_to=completed_date_to
            )
        except Exception as e:
            logger.error(f"Error filtering reviews: {e}")
            return Review.objects.none()

    @staticmethod
    def reassign_reviewer(review_id: str, new_reviewer_id: str, changed_by_id: str = None, reason: str = None) -> Optional[Review]:
        """
        Reassign a review to a different reviewer.
        
        Requires: Case must have a completed payment before reviewers can be reassigned.
        """
        from django.core.exceptions import ValidationError
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            review = ReviewSelector.get_by_id(review_id)
            if not review:
                logger.error(f"Review {review_id} not found")
                return None
            
            # Validate payment requirement
            is_valid, error = PaymentValidator.validate_case_has_payment(review.case, operation_name="review reassignment")
            if not is_valid:
                logger.warning(f"Review reassignment blocked for case {review.case.id}: {error}")
                raise ValidationError(error)
            new_reviewer = UserSelector.get_by_id(new_reviewer_id)
            
            # Verify new reviewer has reviewer role AND is staff or admin
            if new_reviewer.role != 'reviewer':
                logger.error(f"User {new_reviewer_id} does not have reviewer role")
                return None
            if not (new_reviewer.is_staff or new_reviewer.is_superuser):
                logger.error(f"User {new_reviewer_id} is not staff or admin")
                return None
            
            changed_by = None
            if changed_by_id:
                changed_by = UserSelector.get_by_id(changed_by_id)
            
            updated_review = ReviewRepository.reassign_reviewer(
                review,
                new_reviewer,
                changed_by=changed_by,
                reason=reason
            )
            
            # Log audit event
            try:
                AuditLogService.create_audit_log(
                    level='INFO',
                    logger_name='human_reviews',
                    message=f"Review {review_id} reassigned from {review.reviewer.email if review.reviewer else 'None'} to {new_reviewer.email}",
                    func_name='reassign_reviewer',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return updated_review
        except Review.DoesNotExist:
            logger.error(f"Review {review_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error reassigning reviewer to review {review_id}: {e}")
            return None

    @staticmethod
    def escalate_review(review_id: str, escalated_by_id: str = None, reason: str = None, priority: str = 'high') -> Optional[Review]:
        """
        Escalate a review for urgent attention.
        
        Requires: Case must have a completed payment before reviews can be escalated.
        """
        from django.core.exceptions import ValidationError
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            review = ReviewSelector.get_by_id(review_id)
            if not review:
                logger.error(f"Review {review_id} not found")
                return None
            
            # Validate payment requirement
            is_valid, error = PaymentValidator.validate_case_has_payment(review.case, operation_name="review escalation")
            if not is_valid:
                logger.warning(f"Review escalation blocked for case {review.case.id}: {error}")
                raise ValidationError(error)
            
            escalated_by = None
            if escalated_by_id:
                escalated_by = UserSelector.get_by_id(escalated_by_id)
            
            updated_review = ReviewRepository.escalate_review(
                review,
                escalated_by=escalated_by,
                reason=reason,
                priority=priority
            )
            
            # Log audit event
            try:
                AuditLogService.create_audit_log(
                    level='WARNING',
                    logger_name='human_reviews',
                    message=f"Review {review_id} escalated for case {review.case.id}",
                    func_name='escalate_review',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return updated_review
        except Review.DoesNotExist:
            logger.error(f"Review {review_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error escalating review {review_id}: {e}")
            return None

    @staticmethod
    def approve_review(review_id: str, approved_by_id: str = None, reason: str = None) -> Optional[Review]:
        """
        Approve a review (complete with approval).
        
        Requires: Case must have a completed payment before reviews can be approved.
        """
        from django.core.exceptions import ValidationError
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            review = ReviewSelector.get_by_id(review_id)
            if not review:
                logger.error(f"Review {review_id} not found")
                return None
            
            # Validate payment requirement
            is_valid, error = PaymentValidator.validate_case_has_payment(review.case, operation_name="review approval")
            if not is_valid:
                logger.warning(f"Review approval blocked for case {review.case.id}: {error}")
                raise ValidationError(error)
            
            approved_by = None
            if approved_by_id:
                approved_by = UserSelector.get_by_id(approved_by_id)
            
            # Complete the review with approval reason
            updated_review = ReviewRepository.complete_review(
                review,
                changed_by=approved_by,
                reason=reason or "Review approved"
            )
            
            # Log audit event
            try:
                AuditLogService.create_audit_log(
                    level='INFO',
                    logger_name='human_reviews',
                    message=f"Review {review_id} approved for case {review.case.id}",
                    func_name='approve_review',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return updated_review
        except Review.DoesNotExist:
            logger.error(f"Review {review_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error approving review {review_id}: {e}")
            return None

    @staticmethod
    def reject_review(review_id: str, rejected_by_id: str = None, reason: str = None) -> Optional[Review]:
        """
        Reject a review (send back to pending for changes).
        
        Requires: Case must have a completed payment before reviews can be rejected.
        """
        from django.core.exceptions import ValidationError
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            review = ReviewSelector.get_by_id(review_id)
            if not review:
                logger.error(f"Review {review_id} not found")
                return None
            
            # Validate payment requirement
            is_valid, error = PaymentValidator.validate_case_has_payment(review.case, operation_name="review rejection")
            if not is_valid:
                logger.warning(f"Review rejection blocked for case {review.case.id}: {error}")
                raise ValidationError(error)
            
            rejected_by = None
            if rejected_by_id:
                rejected_by = UserSelector.get_by_id(rejected_by_id)
            
            # Set status back to pending with rejection reason
            updated_review = ReviewRepository.update_review(
                review,
                changed_by=rejected_by,
                reason=reason or "Review rejected - requires changes",
                status='pending'
            )
            
            # Log audit event
            try:
                AuditLogService.create_audit_log(
                    level='WARNING',
                    logger_name='human_reviews',
                    message=f"Review {review_id} rejected for case {review.case.id}: {reason}",
                    func_name='reject_review',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return updated_review
        except Review.DoesNotExist:
            logger.error(f"Review {review_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error rejecting review {review_id}: {e}")
            return None

    @staticmethod
    def request_changes(review_id: str, requested_by_id: str = None, reason: str = None) -> Optional[Review]:
        """
        Request changes to a review (similar to reject but with different semantics).
        
        Requires: Case must have a completed payment before changes can be requested on reviews.
        """
        from django.core.exceptions import ValidationError
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            review = ReviewSelector.get_by_id(review_id)
            if not review:
                logger.error(f"Review {review_id} not found")
                return None
            
            # Validate payment requirement
            is_valid, error = PaymentValidator.validate_case_has_payment(review.case, operation_name="review change request")
            if not is_valid:
                logger.warning(f"Review change request blocked for case {review.case.id}: {error}")
                raise ValidationError(error)
            
            requested_by = None
            if requested_by_id:
                requested_by = UserSelector.get_by_id(requested_by_id)
            
            # Keep status as in_progress but add note about requested changes
            # This is tracked via review notes and status history
            updated_review = ReviewRepository.update_review(
                review,
                changed_by=requested_by,
                reason=reason or "Changes requested",
                metadata={'action': 'request_changes'}
            )
            
            # Log audit event
            try:
                AuditLogService.create_audit_log(
                    level='INFO',
                    logger_name='human_reviews',
                    message=f"Changes requested for review {review_id} on case {review.case.id}",
                    func_name='request_changes',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return updated_review
        except Review.DoesNotExist:
            logger.error(f"Review {review_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error requesting changes for review {review_id}: {e}")
            return None

    @staticmethod
    def get_statistics():
        """
        Get comprehensive statistics for human reviews.
        
        Returns a dictionary with statistics for reviews, review notes, and decision overrides.
        """
        from django.db.models import Count, Avg, Q
        from django.utils import timezone
        from datetime import timedelta
        from human_reviews.selectors.review_note_selector import ReviewNoteSelector
        from human_reviews.selectors.decision_override_selector import DecisionOverrideSelector
        
        try:
            # Review statistics
            all_reviews = ReviewSelector.get_all()
            total_reviews = all_reviews.count()
            reviews_by_status = all_reviews.values('status').annotate(count=Count('id'))
            pending_reviews = ReviewSelector.get_by_status('pending').count()
            in_progress_reviews = ReviewSelector.get_by_status('in_progress').count()
            completed_reviews = ReviewSelector.get_by_status('completed').count()
            cancelled_reviews = ReviewSelector.get_by_status('cancelled').count()
            
            # Reviews with assigned reviewers
            assigned_reviews = all_reviews.filter(reviewer__isnull=False).count()
            unassigned_reviews = all_reviews.filter(reviewer__isnull=True).count()
            
            # Average time to completion
            completed_reviews_with_times = ReviewSelector.get_by_status('completed').filter(
                completed_at__isnull=False,
                assigned_at__isnull=False
            )
            avg_completion_time = None
            if completed_reviews_with_times.exists():
                time_diffs = []
                for review in completed_reviews_with_times:
                    if review.assigned_at and review.completed_at:
                        diff = review.completed_at - review.assigned_at
                        time_diffs.append(diff.total_seconds() / 3600)  # Convert to hours
                if time_diffs:
                    avg_completion_time = sum(time_diffs) / len(time_diffs)
            
            # Review note statistics
            all_notes = ReviewNoteSelector.get_all()
            total_notes = all_notes.count()
            internal_notes = all_notes.filter(is_internal=True).count()
            public_notes = all_notes.filter(is_internal=False).count()
            notes_per_review = all_notes.values('review').annotate(count=Count('id'))
            avg_notes_per_review = notes_per_review.aggregate(avg=Avg('count'))['avg'] or 0.0
            
            # Decision override statistics
            all_overrides = DecisionOverrideSelector.get_all()
            total_overrides = all_overrides.count()
            overrides_by_outcome = all_overrides.values('overridden_outcome').annotate(count=Count('id'))
            overrides_with_reviewer = all_overrides.filter(reviewer__isnull=False).count()
            
            # Recent activity (last 7 days)
            seven_days_ago = timezone.now() - timedelta(days=7)
            recent_reviews = all_reviews.filter(created_at__gte=seven_days_ago).count()
            recent_completions = ReviewSelector.get_by_status('completed').filter(
                completed_at__gte=seven_days_ago
            ).count()
            recent_overrides = all_overrides.filter(created_at__gte=seven_days_ago).count()
            
            # Reviewer workload
            reviewer_workload = all_reviews.filter(
                reviewer__isnull=False,
                status__in=['pending', 'in_progress']
            ).values('reviewer__email').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            return {
                'reviews': {
                    'total': total_reviews,
                    'by_status': {item['status']: item['count'] for item in reviews_by_status},
                    'pending': pending_reviews,
                    'in_progress': in_progress_reviews,
                    'completed': completed_reviews,
                    'cancelled': cancelled_reviews,
                    'assigned': assigned_reviews,
                    'unassigned': unassigned_reviews,
                    'average_completion_time_hours': round(avg_completion_time, 2) if avg_completion_time else None,
                },
                'review_notes': {
                    'total': total_notes,
                    'internal': internal_notes,
                    'public': public_notes,
                    'average_per_review': round(avg_notes_per_review, 2),
                },
                'decision_overrides': {
                    'total': total_overrides,
                    'by_outcome': {item['overridden_outcome']: item['count'] for item in overrides_by_outcome},
                    'with_reviewer': overrides_with_reviewer,
                },
                'recent_activity': {
                    'last_7_days': {
                        'reviews_created': recent_reviews,
                        'reviews_completed': recent_completions,
                        'overrides_created': recent_overrides,
                    }
                },
                'reviewer_workload': [
                    {
                        'reviewer_email': item['reviewer__email'],
                        'active_reviews': item['count']
                    }
                    for item in reviewer_workload
                ],
            }
        except Exception as e:
            logger.error(f"Error getting human reviews statistics: {e}")
            return {}
