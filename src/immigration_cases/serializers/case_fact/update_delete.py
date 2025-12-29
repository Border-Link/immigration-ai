from rest_framework import serializers
from immigration_cases.models.case_fact import CaseFact


class CaseFactUpdateSerializer(serializers.Serializer):
    """Serializer for updating a case fact."""
    
    fact_value = serializers.JSONField(required=False)
    source = serializers.ChoiceField(choices=CaseFact.SOURCE_CHOICES, required=False)

