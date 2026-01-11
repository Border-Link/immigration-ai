from django.urls import path
from human_reviews.views import (
    # Review
    ReviewCreateAPI,
    ReviewListAPI,
    ReviewDetailAPI,
    ReviewPendingAPI,
    ReviewByReviewerAPI,
    ReviewUpdateAPI,
    ReviewAssignAPI,
    ReviewCompleteAPI,
    ReviewCancelAPI,
    ReviewDeleteAPI,
)
from human_reviews.views.review.actions import (
    ReviewReassignAPI,
    ReviewEscalateAPI,
    ReviewApproveAPI,
    ReviewRejectAPI,
    ReviewRequestChangesAPI,
)
from human_reviews.views.review_status_history import (
    ReviewStatusHistoryListAPI,
    ReviewStatusHistoryDetailAPI,
)
from human_reviews.views import (
    # ReviewNote
    ReviewNoteCreateAPI,
    ReviewNoteListAPI,
    ReviewNoteDetailAPI,
    ReviewNotePublicAPI,
    ReviewNoteUpdateAPI,
    ReviewNoteDeleteAPI,
    # DecisionOverride
    DecisionOverrideCreateAPI,
    DecisionOverrideListAPI,
    DecisionOverrideDetailAPI,
    DecisionOverrideLatestAPI,
)
from human_reviews.views.admin import (
    # Review Admin
    ReviewAdminListAPI,
    ReviewAdminDetailAPI,
    ReviewAdminUpdateAPI,
    ReviewAdminDeleteAPI,
    BulkReviewOperationAPI,
    # ReviewNote Admin
    ReviewNoteAdminListAPI,
    ReviewNoteAdminDetailAPI,
    ReviewNoteAdminUpdateAPI,
    ReviewNoteAdminDeleteAPI,
    BulkReviewNoteOperationAPI,
    # DecisionOverride Admin
    DecisionOverrideAdminListAPI,
    DecisionOverrideAdminDetailAPI,
    DecisionOverrideAdminUpdateAPI,
    DecisionOverrideAdminDeleteAPI,
    BulkDecisionOverrideOperationAPI,
    # Analytics
    HumanReviewsStatisticsAPI,
)

app_name = 'human_reviews'

urlpatterns = [
    # Review endpoints
    path('reviews/', ReviewListAPI.as_view(), name='review-list'),
    path('reviews/create/', ReviewCreateAPI.as_view(), name='review-create'),
    path('reviews/pending/', ReviewPendingAPI.as_view(), name='review-pending'),
    path('reviews/my-reviews/', ReviewByReviewerAPI.as_view(), name='review-by-reviewer'),
    path('reviews/<uuid:id>/', ReviewDetailAPI.as_view(), name='review-detail'),
    path('reviews/<uuid:id>/update/', ReviewUpdateAPI.as_view(), name='review-update'),
    path('reviews/<uuid:id>/assign/', ReviewAssignAPI.as_view(), name='review-assign'),
    path('reviews/<uuid:id>/complete/', ReviewCompleteAPI.as_view(), name='review-complete'),
    path('reviews/<uuid:id>/cancel/', ReviewCancelAPI.as_view(), name='review-cancel'),
    path('reviews/<uuid:id>/delete/', ReviewDeleteAPI.as_view(), name='review-delete'),
    path('reviews/<uuid:id>/reassign/', ReviewReassignAPI.as_view(), name='review-reassign'),
    path('reviews/<uuid:id>/escalate/', ReviewEscalateAPI.as_view(), name='review-escalate'),
    path('reviews/<uuid:id>/approve/', ReviewApproveAPI.as_view(), name='review-approve'),
    path('reviews/<uuid:id>/reject/', ReviewRejectAPI.as_view(), name='review-reject'),
    path('reviews/<uuid:id>/request-changes/', ReviewRequestChangesAPI.as_view(), name='review-request-changes'),
    path('reviews/<uuid:review_id>/status-history/', ReviewStatusHistoryListAPI.as_view(), name='review-status-history'),
    
    # ReviewNote endpoints
    path('review-notes/', ReviewNoteListAPI.as_view(), name='review-note-list'),
    path('review-notes/create/', ReviewNoteCreateAPI.as_view(), name='review-note-create'),
    path('review-notes/<uuid:id>/', ReviewNoteDetailAPI.as_view(), name='review-note-detail'),
    path('review-notes/<uuid:id>/update/', ReviewNoteUpdateAPI.as_view(), name='review-note-update'),
    path('review-notes/<uuid:id>/delete/', ReviewNoteDeleteAPI.as_view(), name='review-note-delete'),
    path('reviews/<uuid:review_id>/notes/public/', ReviewNotePublicAPI.as_view(), name='review-note-public'),
    
    # DecisionOverride endpoints
    path('decision-overrides/', DecisionOverrideListAPI.as_view(), name='decision-override-list'),
    path('decision-overrides/create/', DecisionOverrideCreateAPI.as_view(), name='decision-override-create'),
    path('decision-overrides/<uuid:id>/', DecisionOverrideDetailAPI.as_view(), name='decision-override-detail'),
    path('decision-overrides/latest/<uuid:original_result_id>/', DecisionOverrideLatestAPI.as_view(), name='decision-override-latest'),
    
    # Admin endpoints (staff/superuser only)
    # Review Admin
    path('admin/reviews/', ReviewAdminListAPI.as_view(), name='admin-review-list'),
    path('admin/reviews/bulk-operation/', BulkReviewOperationAPI.as_view(), name='admin-review-bulk-operation'),
    path('admin/reviews/<uuid:id>/', ReviewAdminDetailAPI.as_view(), name='admin-review-detail'),
    path('admin/reviews/<uuid:id>/update/', ReviewAdminUpdateAPI.as_view(), name='admin-review-update'),
    path('admin/reviews/<uuid:id>/delete/', ReviewAdminDeleteAPI.as_view(), name='admin-review-delete'),
    
    # ReviewNote Admin
    path('admin/review-notes/', ReviewNoteAdminListAPI.as_view(), name='admin-review-note-list'),
    path('admin/review-notes/bulk-operation/', BulkReviewNoteOperationAPI.as_view(), name='admin-review-note-bulk-operation'),
    path('admin/review-notes/<uuid:id>/', ReviewNoteAdminDetailAPI.as_view(), name='admin-review-note-detail'),
    path('admin/review-notes/<uuid:id>/update/', ReviewNoteAdminUpdateAPI.as_view(), name='admin-review-note-update'),
    path('admin/review-notes/<uuid:id>/delete/', ReviewNoteAdminDeleteAPI.as_view(), name='admin-review-note-delete'),
    
    # DecisionOverride Admin
    path('admin/decision-overrides/', DecisionOverrideAdminListAPI.as_view(), name='admin-decision-override-list'),
    path('admin/decision-overrides/bulk-operation/', BulkDecisionOverrideOperationAPI.as_view(), name='admin-decision-override-bulk-operation'),
    path('admin/decision-overrides/<uuid:id>/', DecisionOverrideAdminDetailAPI.as_view(), name='admin-decision-override-detail'),
    path('admin/decision-overrides/<uuid:id>/update/', DecisionOverrideAdminUpdateAPI.as_view(), name='admin-decision-override-update'),
    path('admin/decision-overrides/<uuid:id>/delete/', DecisionOverrideAdminDeleteAPI.as_view(), name='admin-decision-override-delete'),
    
    # Analytics & Statistics
    path('admin/statistics/', HumanReviewsStatisticsAPI.as_view(), name='admin-statistics'),
    
    # Status History endpoints
    path('status-history/<uuid:id>/', ReviewStatusHistoryDetailAPI.as_view(), name='status-history-detail'),
]

