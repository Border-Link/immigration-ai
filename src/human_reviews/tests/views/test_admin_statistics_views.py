import pytest
from rest_framework import status


API_PREFIX = "/api/v1/human-reviews"


@pytest.mark.django_db
class TestAdminStatisticsViews:
    def test_statistics_requires_staff(self, api_client, case_owner):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{API_PREFIX}/admin/statistics/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_statistics_success(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{API_PREFIX}/admin/statistics/")
        assert resp.status_code == status.HTTP_200_OK
        assert "reviews" in resp.data["data"]

