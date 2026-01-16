"""
Tests for compliance audit log API endpoints.

Endpoints:
- GET /api/v1/compliances/audit-logs/
- GET /api/v1/compliances/audit-logs/<uuid:id>/
"""

import pytest
from rest_framework import status
from datetime import timedelta
from django.utils import timezone


API_PREFIX = "/api/v1/compliances"


@pytest.mark.django_db
class TestAuditLogListAPI:
    @pytest.fixture
    def url(self):
        return f"{API_PREFIX}/audit-logs/"

    def test_list_unauthenticated_returns_401(self, api_client, url):
        res = api_client.get(url)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_authenticated_non_staff_returns_403(self, api_client, url, normal_user):
        api_client.force_authenticate(user=normal_user)
        res = api_client.get(url)
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_list_success_default_recent(self, api_client, url, staff_user, make_audit_log):
        make_audit_log(level="INFO", logger_name="l1", message="m1")
        api_client.force_authenticate(user=staff_user)
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        assert "message" in res.data
        assert "data" in res.data
        assert "items" in res.data["data"]
        assert "pagination" in res.data["data"]

    def test_list_validation_invalid_page_size(self, api_client, url, staff_user):
        api_client.force_authenticate(user=staff_user)
        res = api_client.get(url, {"page_size": 101})
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_validation_invalid_limit(self, api_client, url, staff_user):
        api_client.force_authenticate(user=staff_user)
        res = api_client.get(url, {"limit": 0})
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_validation_date_range_invalid(self, api_client, url, staff_user):
        api_client.force_authenticate(user=staff_user)
        now = timezone.now()
        res = api_client.get(url, {"date_from": now.isoformat(), "date_to": (now - timedelta(days=1)).isoformat()})
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_filter_by_level(self, api_client, url, staff_user, make_audit_log):
        make_audit_log(level="INFO", logger_name="l", message="m1")
        make_audit_log(level="ERROR", logger_name="l", message="m2")

        api_client.force_authenticate(user=staff_user)
        res = api_client.get(url, {"level": "ERROR"})
        assert res.status_code == status.HTTP_200_OK
        items = res.data["data"]["items"]
        assert len(items) >= 1
        assert all(item["level"] == "ERROR" for item in items)

    def test_list_filter_by_logger_name(self, api_client, url, staff_user, make_audit_log):
        make_audit_log(level="INFO", logger_name="logger.a", message="m1")
        make_audit_log(level="INFO", logger_name="logger.b", message="m2")

        api_client.force_authenticate(user=staff_user)
        res = api_client.get(url, {"logger_name": "logger.b"})
        assert res.status_code == status.HTTP_200_OK
        items = res.data["data"]["items"]
        assert len(items) >= 1
        assert all(item["logger_name"] == "logger.b" for item in items)

    def test_list_filter_by_date_range_and_secondary_filters(self, api_client, url, staff_user, make_audit_log):
        make_audit_log(level="INFO", logger_name="logger.a", message="m1")
        make_audit_log(level="ERROR", logger_name="logger.b", message="m2")

        start = (timezone.now() - timedelta(days=1)).isoformat()
        end = (timezone.now() + timedelta(days=1)).isoformat()

        api_client.force_authenticate(user=staff_user)
        res = api_client.get(url, {"date_from": start, "date_to": end, "level": "ERROR", "logger_name": "logger.b"})
        assert res.status_code == status.HTTP_200_OK
        items = res.data["data"]["items"]
        assert len(items) >= 1
        assert all(item["level"] == "ERROR" and item["logger_name"] == "logger.b" for item in items)

    def test_list_pagination(self, api_client, url, staff_user, make_audit_log):
        for i in range(25):
            make_audit_log(level="INFO", logger_name="p", message=f"m{i}")

        api_client.force_authenticate(user=staff_user)
        res = api_client.get(url, {"page": 1, "page_size": 20})
        assert res.status_code == status.HTTP_200_OK
        items = res.data["data"]["items"]
        meta = res.data["data"]["pagination"]
        assert len(items) == 20
        assert meta["page"] == 1
        assert meta["page_size"] == 20
        assert meta["total_count"] >= 25

        res2 = api_client.get(url, {"page": 2, "page_size": 20})
        assert res2.status_code == status.HTTP_200_OK
        items2 = res2.data["data"]["items"]
        meta2 = res2.data["data"]["pagination"]
        assert len(items2) == 5
        assert meta2["page"] == 2
        assert meta2["page_size"] == 20


@pytest.mark.django_db
class TestAuditLogDetailAPI:
    def test_detail_unauthenticated_returns_401(self, api_client):
        res = api_client.get(f"{API_PREFIX}/audit-logs/00000000-0000-0000-0000-000000000000/")
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_detail_non_staff_returns_403(self, api_client, normal_user, make_audit_log):
        log = make_audit_log(level="INFO", logger_name="x", message="m")
        api_client.force_authenticate(user=normal_user)
        res = api_client.get(f"{API_PREFIX}/audit-logs/{log.id}/")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_detail_success(self, api_client, staff_user, make_audit_log):
        log = make_audit_log(level="INFO", logger_name="x", message="m")
        api_client.force_authenticate(user=staff_user)
        res = api_client.get(f"{API_PREFIX}/audit-logs/{log.id}/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["data"]["id"] == str(log.id)
        assert res.data["data"]["level"] == "INFO"

    def test_detail_not_found_returns_404(self, api_client, staff_user):
        from uuid import uuid4

        api_client.force_authenticate(user=staff_user)
        res = api_client.get(f"{API_PREFIX}/audit-logs/{uuid4()}/")
        assert res.status_code == status.HTTP_404_NOT_FOUND

