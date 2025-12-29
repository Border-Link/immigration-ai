from django.db import transaction
from django.conf import settings
from immigration_cases.models.case import Case


class CaseRepository:
    """Repository for Case write operations."""

    @staticmethod
    def create_case(user, jurisdiction: str, status: str = 'draft'):
        """Create a new case."""
        with transaction.atomic():
            case = Case.objects.create(
                user=user,
                jurisdiction=jurisdiction,
                status=status
            )
            case.full_clean()
            case.save()
            return case

    @staticmethod
    def update_case(case: Case, **fields):
        """Update case fields."""
        with transaction.atomic():
            for key, value in fields.items():
                if hasattr(case, key):
                    setattr(case, key, value)
            case.full_clean()
            case.save()
            return case

    @staticmethod
    def delete_case(case: Case):
        """Delete a case."""
        with transaction.atomic():
            case.delete()

