"""
Admin API Views for UserProfile Management

Admin-only endpoints for managing user profiles.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from users_access.services.user_profile_service import UserProfileService
from users_access.services.user_service import UserService
from users_access.serializers.user_profile.profile_serializer import (
    UserProfileSerializer,
    UserProfileUpdateSerializer
)
from django.utils.dateparse import parse_datetime

logger = logging.getLogger('django')


class UserProfileAdminListAPI(AuthAPI):
    """
    Admin: Get list of all user profiles with advanced filtering.
    
    Endpoint: GET /api/v1/auth/admin/user-profiles/
    Auth: Required (staff/superuser only)
    Query Params:
        - user_id: Filter by user ID
        - nationality: Filter by nationality country code
        - consent_given: Filter by consent status
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        user_id = request.query_params.get('user_id', None)
        nationality = request.query_params.get('nationality', None)
        consent_given = request.query_params.get('consent_given', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        
        try:
            parsed_date_from = parse_datetime(date_from) if date_from and isinstance(date_from, str) else date_from
            parsed_date_to = parse_datetime(date_to) if date_to and isinstance(date_to, str) else date_to
            
            consent_given_bool = consent_given.lower() == 'true' if consent_given is not None else None
            
            profiles = UserProfileService.get_by_filters(
                user_id=user_id,
                nationality=nationality,
                consent_given=consent_given_bool,
                date_from=parsed_date_from,
                date_to=parsed_date_to
            )
            
            return self.api_response(
                message="User profiles retrieved successfully.",
                data=UserProfileSerializer(profiles, many=True).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving user profiles: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving user profiles.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserProfileAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed user profile information.
    
    Endpoint: GET /api/v1/auth/admin/user-profiles/<user_id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, user_id):
        try:
            user = UserService.get_by_id(user_id)
            if not user:
                return self.api_response(
                    message=f"User with ID '{user_id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            profile = UserProfileService.get_profile(user)
            if not profile:
                return self.api_response(
                    message=f"User profile for user ID '{user_id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="User profile retrieved successfully.",
                data=UserProfileSerializer(profile).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving user profile for user {user_id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving user profile.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserProfileAdminUpdateAPI(AuthAPI):
    """
    Admin: Update user profile information.
    
    Endpoint: PATCH /api/v1/auth/admin/user-profiles/<user_id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def patch(self, request, user_id):
        serializer = UserProfileUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = UserService.get_by_id(user_id)
            if not user:
                return self.api_response(
                    message=f"User with ID '{user_id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            updated_profile = UserProfileService.update_profile(user, **serializer.validated_data)
            
            if updated_profile:
                return self.api_response(
                    message="User profile updated successfully.",
                    data=UserProfileSerializer(updated_profile).data,
                    status_code=status.HTTP_200_OK
                )
            else:
                return self.api_response(
                    message="Error updating user profile.",
                    data=None,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            logger.error(f"Error updating user profile for user {user_id}: {e}", exc_info=True)
            return self.api_response(
                message="Error updating user profile.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
