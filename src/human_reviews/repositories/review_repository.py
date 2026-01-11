from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.core.exceptions import ValidationError
from human_reviews.models.review import Review
from human_reviews.models.review_status_history import ReviewStatusHistory
from immigration_cases.models.case import Case
from human_reviews.helpers.status_transition_validator import ReviewStatusTransitionValidator
from django.conf import settings


class ReviewRepository:
    """Repository for Review write operations."""

    @staticmethod
    def create_review(case: Case, reviewer=None, status: str = 'pending'):
        """Create a new review."""
        with transaction.atomic():
            assigned_at = timezone.now() if reviewer else None
            
            review = Review.objects.create(
                case=case,
                reviewer=reviewer,
                status=status,
                assigned_at=assigned_at
            )
            review.full_clean()
            review.save()
            return review

    @staticmethod
    def update_review(review, version=None, changed_by=None, reason=None, metadata=None, **fields):
        """Update review fields with status transition validation, history tracking, and optimistic locking."""
        with transaction.atomic():
            # Optimistic locking check
            if version is not None:
                current_version = Review.objects.filter(id=review.id).values_list('version', flat=True).first()
                if current_version != version:
                    raise ValidationError(
                        f"Review was modified by another user. "
                        f"Expected version {version}, got {current_version}. "
                        f"Please refresh and try again."
                    )
            
            # Track status changes
            previous_status = review.status
            status_changed = False
            
            # Validate status transition if status is being updated
            if 'status' in fields:
                is_valid, error = ReviewStatusTransitionValidator.validate_transition(
                    review.status,
                    fields['status']
                )
                if not is_valid:
                    raise ValidationError(error)
                status_changed = True
            
            # Increment version for optimistic locking
            # Use F() expression to ensure atomic increment
            Review.objects.filter(id=review.id).update(version=F('version') + 1)
            
            # Refresh review to get updated version
            review.refresh_from_db()
            
            # Update fields (excluding version which is already updated)
            for key, value in fields.items():
                if hasattr(review, key) and key != 'version':
                    setattr(review, key, value)
            
            review.full_clean()
            review.save()
            
            # Create status history entry if status changed
            if status_changed:
                ReviewStatusHistory.objects.create(
                    review=review,
                    previous_status=previous_status,
                    new_status=review.status,
                    changed_by=changed_by,
                    reason=reason,
                    metadata=metadata or {}
                )
            
            return review

    @staticmethod
    def assign_reviewer(review, reviewer, changed_by=None, reason=None):
        """Assign a reviewer to a review with history tracking."""
        with transaction.atomic():
            previous_status = review.status
            previous_reviewer = review.reviewer
            
            # Increment version for optimistic locking
            Review.objects.filter(id=review.id).update(version=F('version') + 1)
            review.refresh_from_db()
            
            review.reviewer = reviewer
            review.status = 'in_progress'
            review.assigned_at = timezone.now()
            review.full_clean()
            review.save()
            
            # Create status history entry
            ReviewStatusHistory.objects.create(
                review=review,
                previous_status=previous_status,
                new_status='in_progress',
                changed_by=changed_by,
                reason=reason or f"Assigned to reviewer {reviewer.email if reviewer else 'None'}",
                metadata={
                    'previous_reviewer_id': str(previous_reviewer.id) if previous_reviewer else None,
                    'new_reviewer_id': str(reviewer.id) if reviewer else None,
                    'action': 'assign'
                }
            )
            
            return review

    @staticmethod
    def complete_review(review, changed_by=None, reason=None):
        """Mark review as completed with history tracking."""
        with transaction.atomic():
            previous_status = review.status
            
            # Validate transition
            is_valid, error = ReviewStatusTransitionValidator.validate_transition(
                review.status,
                'completed'
            )
            if not is_valid:
                raise ValidationError(error)
            
            # Increment version for optimistic locking
            Review.objects.filter(id=review.id).update(version=F('version') + 1)
            review.refresh_from_db()
            
            review.status = 'completed'
            review.completed_at = timezone.now()
            review.full_clean()
            review.save()
            
            # Create status history entry
            ReviewStatusHistory.objects.create(
                review=review,
                previous_status=previous_status,
                new_status='completed',
                changed_by=changed_by,
                reason=reason or "Review completed",
                metadata={'action': 'complete'}
            )
            
            return review

    @staticmethod
    def cancel_review(review, changed_by=None, reason=None):
        """Cancel a review with history tracking."""
        with transaction.atomic():
            previous_status = review.status
            
            # Validate transition
            is_valid, error = ReviewStatusTransitionValidator.validate_transition(
                review.status,
                'cancelled'
            )
            if not is_valid:
                raise ValidationError(error)
            
            # Increment version for optimistic locking
            Review.objects.filter(id=review.id).update(version=F('version') + 1)
            review.refresh_from_db()
            
            review.status = 'cancelled'
            review.full_clean()
            review.save()
            
            # Create status history entry
            ReviewStatusHistory.objects.create(
                review=review,
                previous_status=previous_status,
                new_status='cancelled',
                changed_by=changed_by,
                reason=reason or "Review cancelled",
                metadata={'action': 'cancel'}
            )
            
            return review
    
    @staticmethod
    def reassign_reviewer(review, new_reviewer, changed_by=None, reason=None):
        """Reassign a review to a different reviewer with history tracking."""
        with transaction.atomic():
            previous_reviewer = review.reviewer
            previous_status = review.status
            
            # Increment version for optimistic locking
            Review.objects.filter(id=review.id).update(version=F('version') + 1)
            review.refresh_from_db()
            
            review.reviewer = new_reviewer
            # If reassigning, keep status as in_progress or set to in_progress
            if review.status == 'pending':
                review.status = 'in_progress'
                review.assigned_at = timezone.now()
            review.full_clean()
            review.save()
            
            # Create status history entry
            ReviewStatusHistory.objects.create(
                review=review,
                previous_status=previous_status,
                new_status=review.status,
                changed_by=changed_by,
                reason=reason or f"Reassigned from {previous_reviewer.email if previous_reviewer else 'None'} to {new_reviewer.email if new_reviewer else 'None'}",
                metadata={
                    'previous_reviewer_id': str(previous_reviewer.id) if previous_reviewer else None,
                    'new_reviewer_id': str(new_reviewer.id) if new_reviewer else None,
                    'action': 'reassign'
                }
            )
            
            return review
    
    @staticmethod
    def escalate_review(review, escalated_by=None, reason=None, priority=None):
        """Escalate a review (mark for urgent attention) with history tracking."""
        with transaction.atomic():
            previous_status = review.status
            
            # Increment version for optimistic locking (even though status doesn't change)
            Review.objects.filter(id=review.id).update(version=F('version') + 1)
            review.refresh_from_db()
            
            # Escalation doesn't change status, but we track it
            metadata = {
                'action': 'escalate',
                'priority': priority or 'high',
                'escalated_at': timezone.now().isoformat()
            }
            
            # Create status history entry for escalation
            ReviewStatusHistory.objects.create(
                review=review,
                previous_status=previous_status,
                new_status=previous_status,  # Status doesn't change on escalation
                changed_by=escalated_by,
                reason=reason or "Review escalated for urgent attention",
                metadata=metadata
            )
            
            return review

    @staticmethod
    def delete_review(review):
        """Delete a review."""
        with transaction.atomic():
            review.delete()

