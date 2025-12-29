from django.urls import path
from ai_decisions.views import (
    EligibilityResultCreateAPI,
    EligibilityResultListAPI,
    EligibilityResultDetailAPI,
    EligibilityResultUpdateAPI,
    EligibilityResultDeleteAPI,
)

app_name = 'ai_decisions'

urlpatterns = [
    path('eligibility-results/', EligibilityResultListAPI.as_view(), name='eligibility-result-list'),
    path('eligibility-results/create/', EligibilityResultCreateAPI.as_view(), name='eligibility-result-create'),
    path('eligibility-results/<uuid:id>/', EligibilityResultDetailAPI.as_view(), name='eligibility-result-detail'),
    path('eligibility-results/<uuid:id>/update/', EligibilityResultUpdateAPI.as_view(), name='eligibility-result-update'),
    path('eligibility-results/<uuid:id>/delete/', EligibilityResultDeleteAPI.as_view(), name='eligibility-result-delete'),
]

