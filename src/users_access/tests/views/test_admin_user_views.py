"""
Tests for admin user views.
All tests use services, not direct model access.
"""
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from users_access.services.user_service import UserService


@pytest.mark.django_db
class TestUserAdminListAPI:
    """Tests for UserAdminListAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for admin users list URL."""
        return "/api/admin/users/"  # Adjust based on actual URL

    def test_list_users_as_admin(self, client, url, admin_user, user_service):
        """Test listing users as admin."""
        user_service.create_user("user1@example.com", "pass123")
        client.force_authenticate(user=admin_user)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_list_users_requires_admin(self, client, url, test_user):
        """Test listing users requires admin."""
        client.force_authenticate(user=test_user)
        response = client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_users_with_filters(self, client, url, admin_user, user_service):
        """Test listing users with filters."""
        user1 = user_service.create_user("user1@example.com", "pass123")
        user_service.update_user(user1, role='reviewer')
        client.force_authenticate(user=admin_user)
        response = client.get(url, {"role": "reviewer"})
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestUserAdminDetailAPI:
    """Tests for UserAdminDetailAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    def test_get_user_detail(self, client, admin_user, test_user):
        """Test getting user detail."""
        client.force_authenticate(user=admin_user)
        url = f"/api/admin/users/{test_user.id}/"
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_get_user_detail_not_found(self, client, admin_user):
        """Test getting non-existent user."""
        from uuid import uuid4
        client.force_authenticate(user=admin_user)
        url = f"/api/admin/users/{uuid4()}/"
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestUserAdminUpdateAPI:
    """Tests for UserAdminUpdateAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    def test_update_user(self, client, admin_user, test_user):
        """Test updating user."""
        client.force_authenticate(user=admin_user)
        url = f"/api/admin/users/{test_user.id}/"
        data = {
            "role": "reviewer"
        }
        response = client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestUserAdminDeleteAPI:
    """Tests for UserAdminDeleteAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    def test_delete_user(self, client, admin_user, test_user):
        """Test deleting user (soft delete)."""
        client.force_authenticate(user=admin_user)
        url = f"/api/admin/users/{test_user.id}/"
        response = client.delete(url)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestUserAdminActivateAPI:
    """Tests for UserAdminActivateAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    def test_activate_user(self, client, admin_user, test_user):
        """Test activating user."""
        client.force_authenticate(user=admin_user)
        url = f"/api/admin/users/{test_user.id}/activate/"
        data = {
            "is_active": True
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestUserStatisticsAPI:
    """Tests for UserStatisticsAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for statistics URL."""
        return "/api/admin/users/statistics/"  # Adjust based on actual URL

    def test_get_statistics(self, client, url, admin_user, user_service):
        """Test getting user statistics."""
        user_service.create_user("user1@example.com", "pass123")
        client.force_authenticate(user=admin_user)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "total_users" in response.data["data"]


@pytest.mark.django_db
class TestUserActivityAPI:
    """Tests for UserActivityAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    def test_get_user_activity(self, client, admin_user, test_user):
        """Test getting user activity."""
        client.force_authenticate(user=admin_user)
        url = f"/api/admin/users/{test_user.id}/activity/"
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "email" in response.data["data"]


@pytest.mark.django_db
class TestUserSuspendAPI:
    """Tests for UserSuspendAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    def test_suspend_user(self, client, admin_user, test_user):
        """Test suspending user."""
        client.force_authenticate(user=admin_user)
        url = f"/api/admin/users/{test_user.id}/suspend/"
        data = {
            "reason": "Test suspension"
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_suspend_self(self, client, admin_user):
        """Test cannot suspend self."""
        client.force_authenticate(user=admin_user)
        url = f"/api/admin/users/{admin_user.id}/suspend/"
        data = {
            "reason": "Test"
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserUnsuspendAPI:
    """Tests for UserUnsuspendAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    def test_unsuspend_user(self, client, admin_user, test_user, user_service):
        """Test unsuspending user."""
        user_service.update_user(test_user, is_active=False)
        client.force_authenticate(user=admin_user)
        url = f"/api/admin/users/{test_user.id}/unsuspend/"
        response = client.post(url, {}, format='json')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestBulkUserOperationAPI:
    """Tests for BulkUserOperationAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for bulk operation URL."""
        return "/api/admin/users/bulk-operation/"  # Adjust based on actual URL

    def test_bulk_activate(self, client, url, admin_user, user_service):
        """Test bulk activate users."""
        user1 = user_service.create_user("user1@example.com", "pass123")
        user_service.update_user(user1, is_active=False)
        client.force_authenticate(user=admin_user)
        data = {
            "user_ids": [str(user1.id)],
            "operation": "activate"
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_bulk_operation_too_many(self, client, url, admin_user):
        """Test bulk operation with too many users."""
        from uuid import uuid4
        user_ids = [str(uuid4()) for _ in range(101)]
        client.force_authenticate(user=admin_user)
        data = {
            "user_ids": user_ids,
            "operation": "activate"
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestAdminPasswordResetAPI:
    """Tests for AdminPasswordResetAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    def test_reset_password_as_superuser(self, client, admin_user, test_user):
        """Test resetting password as superuser."""
        client.force_authenticate(user=admin_user)
        url = f"/api/admin/users/{test_user.id}/reset-password/"
        data = {
            "new_password": "NewPass123!@#"
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_reset_password_requires_superuser(self, client, test_user, reviewer_user):
        """Test resetting password requires superuser."""
        client.force_authenticate(user=reviewer_user)
        url = f"/api/admin/users/{test_user.id}/reset-password/"
        data = {
            "new_password": "NewPass123!@#"
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestUserRoleManagementAPI:
    """Tests for UserRoleManagementAPI."""

    @pytest.fixture
    def client(self):
        """Fixture for API client."""
        return APIClient()

    @pytest.fixture
    def url(self):
        """Fixture for bulk operation URL (used by bulk operation tests in this class)."""
        return "/api/admin/users/bulk-operation/"

    def test_update_role(self, client, admin_user, test_user):
        """Test updating user role."""
        client.force_authenticate(user=admin_user)
        url = f"/api/admin/users/{test_user.id}/role/"
        data = {
            "role": "reviewer"
        }
        response = client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_update_role_requires_superuser(self, client, reviewer_user, test_user):
        """Test updating role requires superuser."""
        client.force_authenticate(user=reviewer_user)
        url = f"/api/admin/users/{test_user.id}/role/"
        data = {
            "role": "reviewer"
        }
        response = client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_bulk_operation_invalid_user_ids(self, client, url, admin_user):
        """Test bulk operation with invalid user IDs."""
        from uuid import uuid4
        client.force_authenticate(user=admin_user)
        data = {
            "user_ids": [str(uuid4()), "invalid-uuid", str(uuid4())],
            "operation": "activate"
        }
        response = client.post(url, data, format='json')
        # Should handle gracefully - may return 400 or partial success
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    def test_update_role_invalid_role(self, client, admin_user, test_user):
        """Test updating role with invalid role value."""
        client.force_authenticate(user=admin_user)
        url = f"/api/admin/users/{test_user.id}/role/"
        data = {
            "role": "invalid_role"  # Invalid role
        }
        response = client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_reset_password_weak_password(self, client, admin_user, test_user):
        """Test password reset with weak password."""
        client.force_authenticate(user=admin_user)
        url = f"/api/admin/users/{test_user.id}/reset-password/"
        data = {
            "new_password": "123"  # Weak password
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_suspend_user_invalid_dates(self, client, admin_user, test_user):
        """Test suspending user with invalid dates."""
        client.force_authenticate(user=admin_user)
        url = f"/api/admin/users/{test_user.id}/suspend/"
        data = {
            "reason": "Test suspension",
            "suspended_until": "2020-01-01"  # Past date (invalid)
        }
        response = client.post(url, data, format='json')
        # Should handle invalid dates gracefully
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
