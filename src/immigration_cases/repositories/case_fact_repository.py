from django.db import transaction
from django.core.exceptions import ValidationError
from immigration_cases.models.case_fact import CaseFact
from immigration_cases.models.case import Case
from immigration_cases.helpers.case_validator import CaseValidator


class CaseFactRepository:
    """Repository for CaseFact write operations."""

    @staticmethod
    def create_case_fact(case: Case, fact_key: str, fact_value, source: str = 'user'):
        """Create a new case fact with business rule validation."""
        with transaction.atomic():
            # Validate fact key
            is_valid, error = CaseValidator.validate_fact_key(fact_key)
            if not is_valid:
                raise ValidationError(error)
            
            # Validate fact value
            is_valid, error = CaseValidator.validate_fact_value(fact_key, fact_value)
            if not is_valid:
                raise ValidationError(error)
            
            fact = CaseFact.objects.create(
                case=case,
                fact_key=fact_key,
                fact_value=fact_value,
                source=source
            )
            fact.full_clean()
            fact.save()
            
            # Invalidate cache
            from django.core.cache import cache
            cache.delete(f"case_facts:case:{case.id}")
            cache.delete("case_facts:all")
            
            return fact

    @staticmethod
    def update_case_fact(fact: CaseFact, **fields):
        """Update case fact fields with business rule validation."""
        with transaction.atomic():
            # Validate if fact_key is being updated
            if 'fact_key' in fields:
                is_valid, error = CaseValidator.validate_fact_key(fields['fact_key'])
                if not is_valid:
                    raise ValidationError(error)
            
            # Validate if fact_value is being updated
            if 'fact_value' in fields:
                fact_key = fields.get('fact_key', fact.fact_key)
                is_valid, error = CaseValidator.validate_fact_value(fact_key, fields['fact_value'])
                if not is_valid:
                    raise ValidationError(error)
            
            for key, value in fields.items():
                if hasattr(fact, key):
                    setattr(fact, key, value)
            fact.full_clean()
            fact.save()
            return fact

    @staticmethod
    def delete_case_fact(fact: CaseFact):
        """Delete a case fact."""
        with transaction.atomic():
            fact.delete()

