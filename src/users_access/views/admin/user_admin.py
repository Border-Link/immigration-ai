"""
Admin API Views for User Management

Admin-only endpoints for managing users.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.admin_permission import AdminPermission
from main_system.views.admin.base import (
    BaseAdminDetailAPI,
    BaseAdminDeleteAPI,
    BaseAdminUpdateAPI,
    BaseAdminActivateAPI,
)
from users_access.services.user_service import UserService
from users_access.serializers.users.admin import (
    UserAdminListQuerySerializer,
    UserAdminListSerializer,
    UserAdminDetailSerializer,
    UserAdminUpdateSerializer,
)


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
    permission_classes = [AdminPermission]
    
    def get(self, request):
        query_serializer = UserAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        users = UserService.get_by_filters(
            role=validated_params.get('role'),
            is_active=validated_params.get('is_active'),
            is_verified=validated_params.get('is_verified'),
            email=validated_params.get('email'),
            date_from=validated_params.get('date_from'),
            date_to=validated_params.get('date_to')
        )
        
        return self.api_response(
            message="Users retrieved successfully.",
            data=UserAdminListSerializer(users, many=True).data,
            status_code=status.HTTP_200_OK
        )


class UserAdminDetailAPI(BaseAdminDetailAPI):
    """
    Admin: Get detailed user information.
    
    Endpoint: GET /api/v1/auth/admin/users/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "User"
    
    def get_entity_by_id(self, entity_id):
        """Get user by ID."""
        return UserService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the detail serializer."""
        return UserAdminDetailSerializer


class UserAdminUpdateAPI(BaseAdminUpdateAPI):
    """
    Admin: Update user information.
    
    Endpoint: PATCH /api/v1/auth/admin/users/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "User"
    
    def get_entity_by_id(self, entity_id):
        """Get user by ID."""
        return UserService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the update serializer."""
        return UserAdminUpdateSerializer
    
    def get_response_serializer_class(self):
        """Return the response serializer."""
        return UserAdminDetailSerializer
    
    def update_entity(self, entity, validated_data):
        """Update the user."""
        # Filter only the fields that are present in validated_data
        update_fields = {k: v for k, v in validated_data.items() if v is not None}
        return UserService.update_user(entity, **update_fields)


class UserAdminDeleteAPI(BaseAdminDeleteAPI):
    """
    Admin: Delete user (soft delete by deactivating).
    
    Endpoint: DELETE /api/v1/auth/admin/users/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "User"
    
    def get_entity_by_id(self, entity_id):
        """Get user by ID."""
        return UserService.get_by_id(entity_id)
    
    def delete_entity(self, entity):
        """Delete (deactivate) the user."""
        return UserService.delete_user(str(entity.id))
    
    def delete(self, request, id):
        """Override to customize success message."""
        entity = self.get_entity_by_id(id)
        if not entity:
            return self.api_response(
                message=f"{self.get_entity_name()} with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        deleted = self.delete_entity(entity)
        if deleted:
            return self.api_response(
                message="User deactivated successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        else:
            return self.api_response(
                message=f"Failed to delete {self.get_entity_name()}.",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserAdminActivateAPI(BaseAdminActivateAPI):
    """
    Admin: Activate user.
    
    Endpoint: POST /api/v1/auth/admin/users/<id>/activate/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "User"
    
    def get_entity_by_id(self, entity_id):
        """Get user by ID."""
        return UserService.get_by_id(entity_id)
    
    def activate_entity(self, entity, is_active):
        """Activate the user."""
        if is_active:
            updated = UserService.activate_user_by_id(str(entity.id))
        else:
            updated = UserService.deactivate_user_by_id(str(entity.id))
        return updated is not None
    
    def post(self, request, id):
        """Override to return serialized data in response."""
        from main_system.serializers.admin.base import ActivateSerializer
        
        serializer = ActivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        is_active = serializer.validated_data['is_active']
        
        entity = self.get_entity_by_id(str(id))
        if not entity:
            return self.api_response(
                message=f"{self.get_entity_name()} not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        try:
            if is_active:
                updated = UserService.activate_user_by_id(str(entity.id))
            else:
                updated = UserService.deactivate_user_by_id(str(entity.id))
            
            if updated:
                action = "activated" if is_active else "deactivated"
                return self.api_response(
                    message=f"{self.get_entity_name()} {action} successfully.",
                    data=UserAdminDetailSerializer(updated).data,
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
            logger.error(f"Error updating {self.get_entity_name()} {id}: {e}", exc_info=True)
            return self.api_response(
                message=f"Error updating {self.get_entity_name()}: {str(e)}",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserAdminDeactivateAPI(BaseAdminActivateAPI):
    """
    Admin: Deactivate user.
    
    Endpoint: POST /api/v1/auth/admin/users/<id>/deactivate/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "User"
    
    def get_entity_by_id(self, entity_id):
        """Get user by ID."""
        return UserService.get_by_id(entity_id)
    
    def activate_entity(self, entity, is_active):
        """Deactivate the user (is_active will always be False)."""
        updated = UserService.deactivate_user_by_id(str(entity.id))
        return updated is not None
    
    def post(self, request, id):
        """Override to always deactivate and return serialized data."""
        entity = self.get_entity_by_id(str(id))
        if not entity:
            return self.api_response(
                message=f"{self.get_entity_name()} not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        try:
            updated = UserService.deactivate_user_by_id(str(entity.id))
            if updated:
                return self.api_response(
                    message="User deactivated successfully.",
                    data=UserAdminDetailSerializer(updated).data,
                    status_code=status.HTTP_200_OK
                )
            else:
                return self.api_response(
                    message=f"Failed to deactivate {self.get_entity_name()}.",
                    data=None,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            import logging
            logger = logging.getLogger('django')
            logger.error(f"Error deactivating {self.get_entity_name()} {id}: {e}", exc_info=True)
            return self.api_response(
                message=f"Error deactivating {self.get_entity_name()}: {str(e)}",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
