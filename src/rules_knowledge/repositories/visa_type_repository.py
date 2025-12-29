from django.db import transaction
from rules_knowledge.models.visa_type import VisaType


class VisaTypeRepository:
    """Repository for VisaType write operations."""

    @staticmethod
    def create_visa_type(jurisdiction: str, code: str, name: str, description: str = None, is_active: bool = True):
        """Create a new visa type."""
        with transaction.atomic():
            visa_type = VisaType.objects.create(
                jurisdiction=jurisdiction,
                code=code,
                name=name,
                description=description,
                is_active=is_active
            )
            visa_type.full_clean()
            visa_type.save()
            return visa_type

    @staticmethod
    def update_visa_type(visa_type, **fields):
        """Update visa type fields."""
        with transaction.atomic():
            for key, value in fields.items():
                if hasattr(visa_type, key):
                    setattr(visa_type, key, value)
            visa_type.full_clean()
            visa_type.save()
            return visa_type

    @staticmethod
    def delete_visa_type(visa_type):
        """Delete a visa type."""
        with transaction.atomic():
            visa_type.delete()

