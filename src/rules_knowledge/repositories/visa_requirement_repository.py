from django.db import transaction
from django.core.exceptions import ValidationError
from rules_knowledge.models.visa_requirement import VisaRequirement
from rules_knowledge.models.visa_rule_version import VisaRuleVersion
from rules_knowledge.helpers.json_logic_validator import JSONLogicValidator


class VisaRequirementRepository:
    """Repository for VisaRequirement write operations."""

    @staticmethod
    def create_requirement(rule_version: VisaRuleVersion, requirement_code: str, rule_type: str,
                          description: str, condition_expression: dict, is_mandatory: bool = True):
        """Create a new visa requirement with JSON Logic validation."""
        # Validate JSON Logic expression
        is_valid, error = JSONLogicValidator.validate_expression(condition_expression)
        if not is_valid:
            raise ValidationError(f"Invalid JSON Logic expression: {error}")
        
        with transaction.atomic():
            # Check for duplicate requirement_code
            if VisaRequirement.objects.filter(
                rule_version=rule_version,
                requirement_code=requirement_code
            ).exists():
                raise ValidationError(
                    f"Requirement with code '{requirement_code}' already exists for this rule version"
                )
            
            requirement = VisaRequirement.objects.create(
                rule_version=rule_version,
                requirement_code=requirement_code,
                rule_type=rule_type,
                description=description,
                condition_expression=condition_expression,
                is_mandatory=is_mandatory
            )
            requirement.full_clean()
            requirement.save()
            return requirement

    @staticmethod
    def update_requirement(requirement, **fields):
        """Update requirement fields with JSON Logic validation."""
        with transaction.atomic():
            # Validate condition_expression if being updated
            if 'condition_expression' in fields:
                is_valid, error = JSONLogicValidator.validate_expression(fields['condition_expression'])
                if not is_valid:
                    raise ValidationError(f"Invalid JSON Logic expression: {error}")
            
            # Check for duplicate requirement_code if being updated
            if 'requirement_code' in fields:
                if VisaRequirement.objects.filter(
                    rule_version=requirement.rule_version,
                    requirement_code=fields['requirement_code']
                ).exclude(id=requirement.id).exists():
                    raise ValidationError(
                        f"Requirement with code '{fields['requirement_code']}' already exists for this rule version"
                    )
            
            for key, value in fields.items():
                if hasattr(requirement, key):
                    setattr(requirement, key, value)
            requirement.full_clean()
            requirement.save()
            return requirement

    @staticmethod
    def delete_requirement(requirement):
        """Delete a requirement."""
        with transaction.atomic():
            requirement.delete()

