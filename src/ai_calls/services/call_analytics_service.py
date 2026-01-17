"""
Service for AI calls analytics.

Views/admin must call services only (no selectors/repositories directly).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from django.db.models import Avg, Count, Q, Sum

from ai_calls.selectors.call_audit_log_selector import CallAuditLogSelector
from ai_calls.selectors.call_session_selector import CallSessionSelector


class CallAnalyticsService:
    """Service for admin analytics around call sessions and guardrails."""

    @staticmethod
    def get_call_session_statistics(date_from=None, date_to=None) -> Dict[str, Any]:
        queryset = CallSessionSelector.get_all(include_deleted=False)

        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)

        total_sessions = queryset.count()

        sessions_by_status = dict(
            queryset.values("status")
            .annotate(count=Count("id"))
            .order_by("status")
            .values_list("status", "count")
        )

        completed_sessions = queryset.filter(status="completed", duration_seconds__isnull=False)
        avg_duration = completed_sessions.aggregate(avg=Avg("duration_seconds"))["avg"] or 0.0
        total_duration = completed_sessions.aggregate(total=Sum("duration_seconds"))["total"] or 0

        retry_sessions = queryset.filter(parent_session__isnull=False)
        retry_count = retry_sessions.count()
        retry_rate = (retry_count / total_sessions * 100) if total_sessions > 0 else 0.0

        sessions_by_user = dict(
            queryset.values("user__email")
            .annotate(count=Count("id"))
            .order_by("-count")
            .values_list("user__email", "count")[:10]
        )

        sessions_by_case = dict(
            queryset.values("case_id")
            .annotate(count=Count("id"))
            .order_by("-count")
            .values_list("case_id", "count")[:10]
        )
        sessions_by_case = {str(k): v for k, v in sessions_by_case.items()}

        return {
            "total_sessions": total_sessions,
            "sessions_by_status": sessions_by_status,
            "average_duration_seconds": round(avg_duration, 2),
            "total_duration_seconds": total_duration,
            "retry_count": retry_count,
            "retry_rate_percent": round(retry_rate, 2),
            "sessions_by_user": sessions_by_user,
            "sessions_by_case": sessions_by_case,
        }

    @staticmethod
    def get_guardrail_analytics(date_from=None, date_to=None, event_type: Optional[str] = None) -> Dict[str, Any]:
        audit_logs = CallAuditLogSelector.get_all()

        if date_from:
            audit_logs = audit_logs.filter(created_at__gte=date_from)
        if date_to:
            audit_logs = audit_logs.filter(created_at__lte=date_to)
        if event_type:
            audit_logs = audit_logs.filter(event_type=event_type)

        total_events = audit_logs.count()
        events_by_type = dict(
            audit_logs.values("event_type")
            .annotate(count=Count("id"))
            .order_by("event_type")
            .values_list("event_type", "count")
        )

        sessions_with_guardrails = CallSessionSelector.get_all(include_deleted=False).filter(
            Q(warnings_count__gt=0) | Q(refusals_count__gt=0) | Q(escalated=True)
        )
        if date_from:
            sessions_with_guardrails = sessions_with_guardrails.filter(created_at__gte=date_from)
        if date_to:
            sessions_with_guardrails = sessions_with_guardrails.filter(created_at__lte=date_to)

        total_warnings = sessions_with_guardrails.aggregate(total=Sum("warnings_count"))["total"] or 0
        total_refusals = sessions_with_guardrails.aggregate(total=Sum("refusals_count"))["total"] or 0
        escalated_count = sessions_with_guardrails.filter(escalated=True).count()

        return {
            "total_guardrail_events": total_events,
            "events_by_type": events_by_type,
            "total_warnings": total_warnings,
            "total_refusals": total_refusals,
            "escalated_sessions": escalated_count,
            "sessions_with_guardrails": sessions_with_guardrails.count(),
        }

