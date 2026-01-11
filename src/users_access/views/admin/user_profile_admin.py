"""
Admin API Views for UserProfile Management

Admin-only endpoints for managing user profiles.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from main_system.views.admin.base import (
    BaseAdminDetailAPI,
    BaseAdminUpdateAPI,
)
from users_access.services.user_profile_service import UserProfileService
from users_access.services.user_service import UserService
from users_access.serializers.user_profile.profile_serializer import (
    UserProfileSerializer,
    UserProfileUpdateSerializer
)
from users_access.serializers.users.admin import UserProfileAdminListQuerySerializer


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
        query_serializer = UserProfileAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        profiles = UserProfileService.get_by_filters(
            user_id=str(validated_params.get('user_id')) if validated_params.get('user_id') else None,
            nationality=validated_params.get('nationality'),
            consent_given=validated_params.get('consent_given'),
            date_from=validated_params.get('date_from'),
            date_to=validated_params.get('date_to')
        )
        
        return self.api_response(
            message="User profiles retrieved successfully.",
            data=UserProfileSerializer(profiles, many=True).data,
            status_code=status.HTTP_200_OK
        )


class UserProfileAdminDetailAPI(BaseAdminDetailAPI):
    """
    Admin: Get detailed user profile information.
    
    Endpoint: GET /api/v1/auth/admin/user-profiles/<user_id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "User profile"
    
    def get_entity_by_id(self, entity_id):
        """Get user profile by user ID (custom logic - gets profile from user)."""
        user = UserService.get_by_id(entity_id)
        if not user:
            return None
        return UserProfileService.get_profile(user)
    
    def get_serializer_class(self):
        """Return the detail serializer."""
        return UserProfileSerializer
    
    def get(self, request, user_id):
        """Override to check both user and profile existence."""
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
        
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(profile)
        
        return self.api_response(
            message=f"{self.get_entity_name()} retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )


class UserProfileAdminUpdateAPI(BaseAdminUpdateAPI):
    """
    Admin: Update user profile information.
    
    Endpoint: PATCH /api/v1/auth/admin/user-profiles/<user_id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "User profile"
    
    def get_entity_by_id(self, entity_id):
        """Get user profile by user ID (custom logic - gets profile from user)."""
        user = UserService.get_by_id(entity_id)
        if not user:
            return None
        return UserProfileService.get_profile(user)
    
    def get_serializer_class(self):
        """Return the update serializer."""
        return UserProfileUpdateSerializer
    
    def get_response_serializer_class(self):
        """Return the response serializer."""
        return UserProfileSerializer
    
    def patch(self, request, user_id):
        """Override to check both user and profile existence."""
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
        
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            updated_profile = UserProfileService.update_profile(user, **serializer.validated_data)
            if updated_profile:
                response_serializer = self.get_response_serializer_class()
                if response_serializer:
                    response_data = response_serializer(updated_profile).data
                else:
                    response_data = serializer_class(updated_profile).data
                
                return self.api_response(
                    message=f"{self.get_entity_name()} updated successfully.",
                    data=response_data,
                    status_code=status.HTTP_200_OK
                )
            else:
                return self.api_response(
                    message=f"Failed to update {self.get_entity_name()}.",
                    data=None,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            import logging
            logger = logging.getLogger('django')
            logger.error(f"Error updating {self.get_entity_name()} {user_id}: {e}", exc_info=True)
            return self.api_response(
                message=f"Error updating {self.get_entity_name()}: {str(e)}",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
