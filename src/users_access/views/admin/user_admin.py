"""
Admin API Views for User Management

Admin-only endpoints for managing users.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from users_access.services.user_service import UserService
from users_access.serializers.users.admin import (
    UserAdminListSerializer,
    UserAdminDetailSerializer,
    UserAdminUpdateSerializer,
)
from django.utils.dateparse import parse_datetime

logger = logging.getLogger('django')


class UserAdminListAPI(AuthAPI):
    """
    Admin: Get list of all users with advanced filtering.
    
    Endpoint: GET /api/v1/auth/admin/users/
    Auth: Required (staff/superuser only)
    Query Params:
        - role: Filter by role (user, reviewer, admin)
        - is_active: Filter by active status
        - is_verified: Filter by verified status
        - email: Search by email
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        role = request.query_params.get('role', None)
        is_active = request.query_params.get('is_active', None)
        is_verified = request.query_params.get('is_verified', None)
        email = request.query_params.get('email', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        
        try:
            # Parse parameters
            is_active_bool = is_active.lower() == 'true' if is_active is not None else None
            is_verified_bool = is_verified.lower() == 'true' if is_verified is not None else None
            parsed_date_from = parse_datetime(date_from) if date_from and isinstance(date_from, str) else date_from
            parsed_date_to = parse_datetime(date_to) if date_to and isinstance(date_to, str) else date_to
            
            # Use service method with filters
            users = UserService.get_by_filters(
                role=role,
                is_active=is_active_bool,
                is_verified=is_verified_bool,
                email=email,
                date_from=parsed_date_from,
                date_to=parsed_date_to
            )
            
            return self.api_response(
                message="Users retrieved successfully.",
                data=UserAdminListSerializer(users, many=True).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving users: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving users.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed user information.
    
    Endpoint: GET /api/v1/auth/admin/users/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        try:
            user = UserService.get_by_id(id)
            if not user:
                return self.api_response(
                    message=f"User with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="User retrieved successfully.",
                data=UserAdminDetailSerializer(user).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving user {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving user.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserAdminUpdateAPI(AuthAPI):
    """
    Admin: Update user information.
    
    Endpoint: PATCH /api/v1/auth/admin/users/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def patch(self, request, id):
        serializer = UserAdminUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = UserService.get_by_id(id)
            if not user:
                return self.api_response(
                    message=f"User with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            updated_user = UserService.update_user(user, **serializer.validated_data)
            
            if updated_user:
                return self.api_response(
                    message="User updated successfully.",
                    data=UserAdminDetailSerializer(updated_user).data,
                    status_code=status.HTTP_200_OK
                )
            else:
                return self.api_response(
                    message="Error updating user.",
                    data=None,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except User.DoesNotExist:
            return self.api_response(
                message=f"User with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error updating user {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error updating user.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete user (soft delete by deactivating).
    
    Endpoint: DELETE /api/v1/auth/admin/users/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        try:
            deleted = UserService.delete_user(id)
            if not deleted:
                return self.api_response(
                    message=f"User with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="User deactivated successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deactivating user {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error deactivating user.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserAdminActivateAPI(AuthAPI):
    """
    Admin: Activate user.
    
    Endpoint: POST /api/v1/auth/admin/users/<id>/activate/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request, id):
        try:
            updated_user = UserService.activate_user_by_id(id)
            if not updated_user:
                return self.api_response(
                    message=f"User with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="User activated successfully.",
                data=UserAdminDetailSerializer(updated_user).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error activating user {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error activating user.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserAdminDeactivateAPI(AuthAPI):
    """
    Admin: Deactivate user.
    
    Endpoint: POST /api/v1/auth/admin/users/<id>/deactivate/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request, id):
        try:
            updated_user = UserService.deactivate_user_by_id(id)
            if not updated_user:
                return self.api_response(
                    message=f"User with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="User deactivated successfully.",
                data=UserAdminDetailSerializer(updated_user).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deactivating user {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error deactivating user.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
