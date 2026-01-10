from django.urls import path
from immigration_cases.views import (
    CaseCreateAPI,
    CaseListAPI,
    CaseDetailAPI,
    CaseUpdateAPI,
    CaseDeleteAPI,
    CaseEligibilityCheckAPI,
    CaseEligibilityExplanationAPI,
    CaseFactCreateAPI,
    CaseFactListAPI,
    CaseFactDetailAPI,
    CaseFactUpdateAPI,
    CaseFactDeleteAPI,
)

app_name = 'immigration_cases'

urlpatterns = [
    # Case endpoints
    path('cases/', CaseListAPI.as_view(), name='case-list'),
    path('cases/create/', CaseCreateAPI.as_view(), name='case-create'),
    path('cases/<uuid:id>/', CaseDetailAPI.as_view(), name='case-detail'),
    path('cases/<uuid:id>/update/', CaseUpdateAPI.as_view(), name='case-update'),
    path('cases/<uuid:id>/delete/', CaseDeleteAPI.as_view(), name='case-delete'),
    
    # Eligibility endpoints (from implementation.md Section 4.3)
    path('cases/<uuid:id>/eligibility', CaseEligibilityCheckAPI.as_view(), name='case-eligibility-check'),
    path('cases/<uuid:id>/eligibility/<uuid:result_id>/explanation', CaseEligibilityExplanationAPI.as_view(), name='case-eligibility-explanation'),
    
    # CaseFact endpoints
    path('case-facts/', CaseFactListAPI.as_view(), name='case-fact-list'),
    path('case-facts/create/', CaseFactCreateAPI.as_view(), name='case-fact-create'),
    path('case-facts/<uuid:id>/', CaseFactDetailAPI.as_view(), name='case-fact-detail'),
    path('case-facts/<uuid:id>/update/', CaseFactUpdateAPI.as_view(), name='case-fact-update'),
    path('case-facts/<uuid:id>/delete/', CaseFactDeleteAPI.as_view(), name='case-fact-delete'),
]

