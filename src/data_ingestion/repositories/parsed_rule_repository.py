from typing import Optional
from django.db import transaction
from main_system.repositories.base import BaseRepositoryMixin
from data_ingestion.models.parsed_rule import ParsedRule
from data_ingestion.models.document_version import DocumentVersion


class ParsedRuleRepository:
    """Repository for ParsedRule write operations."""

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
                estimated_cost=estimated_cost,
                processing_time_ms=processing_time_ms
            )
            parsed_rule.full_clean()
            parsed_rule.save()
            return parsed_rule

    @staticmethod
    def update_parsed_rule(parsed_rule, **fields):
        """Update parsed rule fields."""
        return BaseRepositoryMixin.update_model_fields(
            parsed_rule,
            **fields,
            cache_keys=[f'parsed_rule:{parsed_rule.id}']
        )

    @staticmethod
    def update_status(parsed_rule, status: str):
        """Update parsed rule status."""
        with transaction.atomic():
            parsed_rule.status = status
            parsed_rule.full_clean()
            parsed_rule.save()
            return parsed_rule

    @staticmethod
    def delete_parsed_rule(parsed_rule):
        """Delete a parsed rule."""
        with transaction.atomic():
            parsed_rule.delete()
            return True
