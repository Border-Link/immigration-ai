from typing import Optional
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.core.exceptions import ValidationError
from data_ingestion.models.parsed_rule import ParsedRule
from data_ingestion.models.document_version import DocumentVersion


class ParsedRuleRepository:
    """Repository for ParsedRule write operations."""

    @staticmethod
    def _normalize_estimated_cost(value: Optional[object]) -> Optional[Decimal]:
        """
        Normalize estimated_cost to a Decimal that fits ParsedRule.estimated_cost:
        DecimalField(max_digits=10, decimal_places=6).
        """
        if value is None:
            return None
        if isinstance(value, Decimal):
            dec = value
        else:
            # IMPORTANT: never Decimal(float) (can create long repeating decimals).
            dec = Decimal(str(value))
        return dec.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

    @staticmethod
    def create_parsed_rule(
        document_version: DocumentVersion,
        visa_code: str,
        rule_type: str,
        extracted_logic: dict,
        description: str,
        source_excerpt: str,
        confidence_score: float = 0.0,
        status: str = 'pending',
        llm_model: Optional[str] = None,
        llm_model_version: Optional[str] = None,
        tokens_used: Optional[int] = None,
        estimated_cost: Optional[float] = None,
        processing_time_ms: Optional[int] = None
    ):
        """Create a new parsed rule with optional metadata."""
        from typing import Optional
        
        with transaction.atomic():
            parsed_rule = ParsedRule.objects.create(
                document_version=document_version,
                visa_code=visa_code,
                rule_type=rule_type,
                extracted_logic=extracted_logic,
                description=description,
                source_excerpt=source_excerpt,
                confidence_score=confidence_score,
                status=status,
                llm_model=llm_model,
                llm_model_version=llm_model_version,
                tokens_used=tokens_used,
                estimated_cost=ParsedRuleRepository._normalize_estimated_cost(estimated_cost),
                processing_time_ms=processing_time_ms,
                version=1,
                is_deleted=False,
            )
            parsed_rule.full_clean()
            parsed_rule.save()
            return parsed_rule

    @staticmethod
    def update_parsed_rule(parsed_rule: ParsedRule, version: int = None, **fields) -> ParsedRule:
        """
        Update parsed rule fields with optimistic locking.

        Uses a single conditional UPDATE (WHERE id AND version) to prevent last-write-wins overwrites.
        """
        with transaction.atomic():
            expected_version = version if version is not None else getattr(parsed_rule, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            allowed_fields = {f.name for f in ParsedRule._meta.fields}
            protected_fields = {"id", "version", "created_at"}
            update_fields = {
                k: v for k, v in fields.items()
                if k in allowed_fields and k not in protected_fields
            }

            if "estimated_cost" in update_fields:
                update_fields["estimated_cost"] = ParsedRuleRepository._normalize_estimated_cost(update_fields["estimated_cost"])

            # QuerySet.update bypasses auto_now; set updated_at explicitly.
            if "updated_at" in allowed_fields:
                update_fields["updated_at"] = timezone.now()

            updated_count = ParsedRule.objects.filter(
                id=parsed_rule.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                **update_fields,
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = ParsedRule.objects.filter(id=parsed_rule.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Parsed rule not found.")
                raise ValidationError(
                    f"Parsed rule was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return ParsedRule.objects.get(id=parsed_rule.id)

    @staticmethod
    def update_status(parsed_rule, status: str):
        """Update parsed rule status."""
        return ParsedRuleRepository.update_parsed_rule(
            parsed_rule,
            version=getattr(parsed_rule, "version", None),
            status=status,
        )

    @staticmethod
    def soft_delete_parsed_rule(parsed_rule: ParsedRule, version: int = None) -> ParsedRule:
        """Soft delete a parsed rule with optimistic locking."""
        with transaction.atomic():
            expected_version = version if version is not None else getattr(parsed_rule, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            now_ts = timezone.now()
            updated_count = ParsedRule.objects.filter(
                id=parsed_rule.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                is_deleted=True,
                deleted_at=now_ts,
                updated_at=now_ts,
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = ParsedRule.objects.filter(id=parsed_rule.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Parsed rule not found.")
                raise ValidationError(
                    f"Parsed rule was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return ParsedRule.objects.get(id=parsed_rule.id)

    @staticmethod
    def delete_parsed_rule(parsed_rule: ParsedRule, version: int = None):
        """
        Delete a parsed rule.

        CRITICAL: Deletion must be soft-delete to preserve auditability.
        """
        ParsedRuleRepository.soft_delete_parsed_rule(parsed_rule, version=version)
        return True
