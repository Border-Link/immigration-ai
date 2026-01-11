from rest_framework import serializers
from immigration_cases.models.case import Case


class CaseUpdateSerializer(serializers.Serializer):
    """Serializer for updating a case."""
    
    status = serializers.ChoiceField(choices=Case.STATUS_CHOICES, required=False)
    jurisdiction = serializers.ChoiceField(choices=Case.JURISDICTION_CHOICES, required=False)
    version = serializers.IntegerField(required=True, help_text="Current version of the case for optimistic locking")
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500, help_text="Reason for the update")

