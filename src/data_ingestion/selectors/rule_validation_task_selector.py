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
        ).all()

    @staticmethod
    def get_by_status(status: str):
        """Get validation tasks by status."""
        return RuleValidationTask.objects.select_related(
            'parsed_rule',
            'parsed_rule__document_version',
            'assigned_to'
        ).filter(status=status).order_by('-created_at')

    @staticmethod
    def get_by_reviewer(reviewer):
        """Get validation tasks assigned to a reviewer."""
        return RuleValidationTask.objects.select_related(
            'parsed_rule',
            'parsed_rule__document_version',
            'assigned_to'
        ).filter(assigned_to=reviewer).order_by('-created_at')

    @staticmethod
    def get_by_parsed_rule(parsed_rule):
        """Get validation tasks for a parsed rule."""
        return RuleValidationTask.objects.select_related(
            'parsed_rule',
            'parsed_rule__document_version',
            'assigned_to'
        ).filter(parsed_rule=parsed_rule).order_by('-created_at').first()
    
    @staticmethod
    def exists_for_parsed_rule(parsed_rule):
        """Check if validation task exists for a parsed rule."""
        return RuleValidationTask.objects.filter(parsed_rule=parsed_rule).exists()

    @staticmethod
    def get_pending():
        """Get all pending validation tasks."""
        return RuleValidationTask.objects.select_related(
            'parsed_rule',
            'parsed_rule__document_version',
            'assigned_to'
        ).filter(status='pending').order_by('sla_deadline', '-created_at')

    @staticmethod
    def get_by_id(task_id):
        """Get validation task by ID."""
        return RuleValidationTask.objects.select_related(
            'parsed_rule',
            'parsed_rule__document_version',
            'assigned_to'
        ).get(id=task_id)

