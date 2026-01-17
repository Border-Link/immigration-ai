from data_ingestion.models.rule_validation_task import RuleValidationTask


class RuleValidationTaskSelector:
    """Selector for RuleValidationTask read operations."""

    @staticmethod
    def get_all():
        """Get all validation tasks."""
        return RuleValidationTask.objects.select_related(
            'parsed_rule',
            'parsed_rule__document_version',
            'assigned_to'
        ).filter(is_deleted=False)

    @staticmethod
    def get_by_status(status: str):
        """Get validation tasks by status."""
        return RuleValidationTask.objects.select_related(
            'parsed_rule',
            'parsed_rule__document_version',
            'assigned_to'
        ).filter(status=status, is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_by_reviewer(reviewer):
        """Get validation tasks assigned to a reviewer."""
        return RuleValidationTask.objects.select_related(
            'parsed_rule',
            'parsed_rule__document_version',
            'assigned_to'
        ).filter(assigned_to=reviewer, is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_by_parsed_rule(parsed_rule):
        """Get validation tasks for a parsed rule."""
        return RuleValidationTask.objects.select_related(
            'parsed_rule',
            'parsed_rule__document_version',
            'assigned_to'
        ).filter(parsed_rule=parsed_rule, is_deleted=False).order_by('-created_at').first()
    
    @staticmethod
    def exists_for_parsed_rule(parsed_rule):
        """Check if validation task exists for a parsed rule."""
        return RuleValidationTask.objects.filter(parsed_rule=parsed_rule, is_deleted=False).exists()

    @staticmethod
    def get_pending():
        """Get all pending validation tasks."""
        return RuleValidationTask.objects.select_related(
            'parsed_rule',
            'parsed_rule__document_version',
            'assigned_to'
        ).filter(status='pending', is_deleted=False).order_by('sla_deadline', '-created_at')

    @staticmethod
    def get_by_id(task_id):
        """Get validation task by ID."""
        return RuleValidationTask.objects.select_related(
            'parsed_rule',
            'parsed_rule__document_version',
            'assigned_to'
        ).filter(id=task_id, is_deleted=False).first()

    @staticmethod
    def get_by_reviewer_id(reviewer_id: str):
        """Get validation tasks assigned to a reviewer by reviewer ID."""
        return RuleValidationTask.objects.select_related(
            'parsed_rule',
            'parsed_rule__document_version',
            'assigned_to'
        ).filter(assigned_to_id=reviewer_id, is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_none():
        """Get empty queryset."""
        return RuleValidationTask.objects.none()

    @staticmethod
    def get_by_filters(status: str = None, assigned_to_id: str = None, date_from=None, date_to=None, sla_overdue: bool = None):
        """Get validation tasks with filters."""
        from django.utils import timezone
        
        if status:
            queryset = RuleValidationTaskSelector.get_by_status(status)
        elif assigned_to_id:
            queryset = RuleValidationTaskSelector.get_by_reviewer_id(assigned_to_id)
        else:
            queryset = RuleValidationTaskSelector.get_all()
        
        if sla_overdue:
            now = timezone.now()
            queryset = queryset.filter(sla_deadline__lt=now, status__in=['pending', 'in_progress'])
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset

    @staticmethod
    def get_statistics():
        """Get validation task statistics."""
        from django.db.models import Count
        
        queryset = RuleValidationTask.objects.filter(is_deleted=False)
        
        total_tasks = queryset.count()
        tasks_by_status = queryset.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        pending_tasks = queryset.filter(status='pending').count()
        
        return {
            'total': total_tasks,
            'pending': pending_tasks,
            'by_status': list(tasks_by_status),
        }
