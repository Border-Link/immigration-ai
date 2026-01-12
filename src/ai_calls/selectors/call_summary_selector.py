from ai_calls.models.call_summary import CallSummary


class CallSummarySelector:
    """Selector for CallSummary read operations."""

    @staticmethod
    def get_by_call_session(call_session):
        """Get call summary for call session."""
        return CallSummary.objects.select_related('call_session').filter(
            call_session=call_session
        ).first()

    @staticmethod
    def get_by_id(summary_id):
        """Get call summary by ID."""
        return CallSummary.objects.select_related('call_session').get(id=summary_id)

    @staticmethod
    def get_by_case(case):
        """Get call summaries for a case."""
        return CallSummary.objects.select_related(
            'call_session', 'call_session__case'
        ).filter(
            call_session__case=case
        ).order_by('-created_at')

    @staticmethod
    def get_none():
        """Get empty queryset."""
        return CallSummary.objects.none()
