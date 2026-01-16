from django.urls import path
from ai_calls.views.call_session import (
    CallSessionCreateAPI,
    CallSessionDetailAPI,
    CallSessionPrepareAPI,
    CallSessionStartAPI,
    CallSessionEndAPI,
    CallSessionTerminateAPI,
    CallSessionSpeechAPI,
    CallSessionTranscriptAPI,
    CallSessionHeartbeatAPI,
)
from ai_calls.views.admin import (
    CallSessionAdminListAPI,
    CallSessionAdminDetailAPI,
    CallSessionStatisticsAPI,
    GuardrailAnalyticsAPI,
)

app_name = 'ai_calls'

urlpatterns = [
    # Public Call Session endpoints
    path('sessions/', CallSessionCreateAPI.as_view(), name='call-sessions-create'),
    path('sessions/<uuid:session_id>/', CallSessionDetailAPI.as_view(), name='call-sessions-detail'),
    path('sessions/<uuid:session_id>/prepare/', CallSessionPrepareAPI.as_view(), name='call-sessions-prepare'),
    path('sessions/<uuid:session_id>/start/', CallSessionStartAPI.as_view(), name='call-sessions-start'),
    path('sessions/<uuid:session_id>/end/', CallSessionEndAPI.as_view(), name='call-sessions-end'),
    path('sessions/<uuid:session_id>/terminate/', CallSessionTerminateAPI.as_view(), name='call-sessions-terminate'),
    path('sessions/<uuid:session_id>/speech/', CallSessionSpeechAPI.as_view(), name='call-sessions-speech'),
    path('sessions/<uuid:session_id>/transcript/', CallSessionTranscriptAPI.as_view(), name='call-sessions-transcript'),
    path('sessions/<uuid:session_id>/heartbeat/', CallSessionHeartbeatAPI.as_view(), name='call-sessions-heartbeat'),
    
    # Admin endpoints
    path('admin/sessions/', CallSessionAdminListAPI.as_view(), name='admin-call-sessions-list'),
    # BaseAdminDetailAPI expects kwarg name `id`
    path('admin/sessions/<uuid:id>/', CallSessionAdminDetailAPI.as_view(), name='admin-call-sessions-detail'),
    path('admin/statistics/', CallSessionStatisticsAPI.as_view(), name='admin-call-statistics'),
    path('admin/guardrail-analytics/', GuardrailAnalyticsAPI.as_view(), name='admin-guardrail-analytics'),
]
