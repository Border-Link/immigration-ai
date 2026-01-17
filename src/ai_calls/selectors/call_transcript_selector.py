from ai_calls.models.call_transcript import CallTranscript


class CallTranscriptSelector:
    """Selector for CallTranscript read operations."""

    @staticmethod
    def get_by_call_session(call_session, include_cold: bool = False):
        """Get transcript for call session."""
        queryset = CallTranscript.objects.filter(
            call_session=call_session,
            is_deleted=False,
        )
        
        if not include_cold:
            queryset = queryset.filter(storage_tier='hot')
        
        return queryset.order_by('turn_number')

    @staticmethod
    def get_by_id(transcript_id):
        """Get transcript turn by ID."""
        return CallTranscript.objects.select_related('call_session').filter(id=transcript_id, is_deleted=False).first()

    @staticmethod
    def get_by_turn_number(call_session, turn_number: int):
        """Get transcript turn by turn number."""
        return CallTranscript.objects.filter(
            call_session=call_session,
            turn_number=turn_number,
            is_deleted=False,
        ).first()

    @staticmethod
    def get_hot_storage_transcripts(days_threshold: int = 90):
        """Get transcripts in hot storage older than threshold."""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days_threshold)
        
        return CallTranscript.objects.filter(
            storage_tier='hot',
            timestamp__lt=cutoff_date,
            is_deleted=False,
        ).order_by('timestamp')

    @staticmethod
    def get_latest_turn_number(call_session):
        """Get the latest turn number for a call session."""
        last_turn = CallTranscript.objects.filter(
            call_session=call_session,
            is_deleted=False,
        ).order_by('-turn_number').first()
        return last_turn.turn_number if last_turn else 0

    @staticmethod
    def get_none():
        """Get empty queryset."""
        return CallTranscript.objects.none()
