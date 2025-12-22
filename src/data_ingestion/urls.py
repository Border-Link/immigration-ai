from django.urls import path
from data_ingestion.views import (
    DataSourceCreateAPI,
    DataSourceListAPI,
    DataSourceDetailAPI,
    DataSourceUpdateAPI,
    DataSourceIngestionTriggerAPI,
)

app_name = 'data_ingestion'

urlpatterns = [
    # Data Sources
    path('data-sources/', DataSourceListAPI.as_view(), name='data-sources-list'),
    path('data-sources/create/', DataSourceCreateAPI.as_view(), name='data-sources-create'),
    path('data-sources/<uuid:id>/', DataSourceDetailAPI.as_view(), name='data-sources-detail'),
    path('data-sources/<uuid:id>/update/', DataSourceUpdateAPI.as_view(), name='data-sources-update'),
    path('data-sources/<uuid:id>/ingest/', DataSourceIngestionTriggerAPI.as_view(), name='data-sources-ingest'),
]

