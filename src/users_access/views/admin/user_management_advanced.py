"""
Advanced Admin API Views for User Management

Advanced admin-only endpoints for comprehensive user management.
Includes suspension, verification, bulk operations, password reset, etc.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from main_system.permissions.is_superuser import IsSuperUser
from users_access.services.user_service import UserService
from users_access.serializers.users.admin import (
    UserSuspendSerializer,
    UserVerifySerializer,
    BulkUserOperationSerializer,
    AdminPasswordResetSerializer,
    UserRoleUpdateSerializer,
)
from django.contrib.auth.hashers import make_password
from django.utils import timezone

logger = logging.getLogger('django')


class UserSuspendAPI(AuthAPI):
    """
    Admin: Suspend a user (temporary ban with optional expiration).
    
    Endpoint: POST /api/v1/auth/admin/users/<id>/suspend/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request, id):
        serializer = UserSuspendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            updated_user = UserService.deactivate_user_by_id(id)
            if not updated_user:
                return self.api_response(
                    message=f"User with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message=f"User suspended successfully. Reason: {serializer.validated_data.get('reason', 'No reason provided')}",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error suspending user {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error suspending user.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserUnsuspendAPI(AuthAPI):
    """
    Admin: Unsuspend a user (reactivate).
    
    Endpoint: POST /api/v1/auth/admin/users/<id>/unsuspend/
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
                message="User unsuspended successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error unsuspending user {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error unsuspending user.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserVerifyAPI(AuthAPI):
    """
    Admin: Verify or unverify a user's email.
    
    Endpoint: POST /api/v1/auth/admin/users/<id>/verify/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request, id):
        serializer = UserVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = UserService.get_by_id(id)
            if not user:
                return self.api_response(
                    message=f"User with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            updated_user = UserService.update_user(
                user,
                is_verified=serializer.validated_data['is_verified']
            )
            
            if not updated_user:
                return self.api_response(
                    message="Error verifying user.",
                    data=None,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            action = "verified" if serializer.validated_data['is_verified'] else "unverified"
            return self.api_response(
                message=f"User {action} successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error verifying user {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error verifying user.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkUserOperationAPI(AuthAPI):
    """
    Admin: Perform bulk operations on multiple users.
    
    Endpoint: POST /api/v1/auth/admin/users/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request):
        serializer = BulkUserOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_ids = serializer.validated_data['user_ids']
        operation = serializer.validated_data['operation']
        reason = serializer.validated_data.get('reason', '')
        
        results = {
            'success': [],
            'failed': []
        }
        
        try:
            for user_id in user_ids:
                try:
                    user = UserService.get_by_id(str(user_id))
                    if not user:
                        results['failed'].append({
                            'user_id': str(user_id),
                            'error': 'User not found'
                        })
                        continue
                    
                    if operation == 'activate':
                        updated = UserService.activate_user_by_id(str(user_id))
                    elif operation == 'deactivate':
                        updated = UserService.deactivate_user_by_id(str(user_id))
                    elif operation == 'verify':
                        updated = UserService.update_user(user, is_verified=True)
                    elif operation == 'unverify':
                        updated = UserService.update_user(user, is_verified=False)
                    elif operation == 'delete':
                        # Soft delete by deactivating
                        updated = UserService.deactivate_user_by_id(str(user_id))
                    elif operation == 'promote_to_reviewer':
                        updated = UserService.update_user(
                            user,
                            role='reviewer',
                            is_staff=True
                        )
                    elif operation == 'demote_from_reviewer':
                        if user.role == 'reviewer':
                            updated = UserService.update_user(
                                user,
                                role='user',
                                is_staff=False
                            )
                        else:
                            updated = None
                    
                    if updated:
                        results['success'].append(str(user_id))
                    else:
                        results['failed'].append({
                            'user_id': str(user_id),
                            'error': 'Operation failed'
                        })
                except Exception as e:
                    results['failed'].append({
                        'user_id': str(user_id),
                        'error': str(e)
                    })
            
            return self.api_response(
                message=f"Bulk operation '{operation}' completed. {len(results['success'])} succeeded, {len(results['failed'])} failed.",
                data=results,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error in bulk operation: {e}", exc_info=True)
            return self.api_response(
                message="Error performing bulk operation.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminPasswordResetAPI(AuthAPI):
    """
    Admin: Reset a user's password (superuser only for security).
    
    Endpoint: POST /api/v1/auth/admin/users/<id>/reset-password/
    Auth: Required (superuser only)
    """
    permission_classes = [IsSuperUser]
    
    def post(self, request, id):
        serializer = AdminPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = UserService.get_by_id(id)
            if not user:
                return self.api_response(
                    message=f"User with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            new_password = serializer.validated_data['new_password']
            
            # Reset password
            updated_user = UserService.update_password(user, new_password)
            
            if not updated_user:
                return self.api_response(
                    message="Error resetting password.",
                    data=None,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # TODO: Send email notification if send_email is True
            # if serializer.validated_data.get('send_email'):
            #     send_password_reset_email(user, new_password)
            
            return self.api_response(
                message="Password reset successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error resetting password for user {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error resetting password.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserRoleManagementAPI(AuthAPI):
    """
    Admin: Update user role and permissions (superuser only).
    
    Endpoint: PATCH /api/v1/auth/admin/users/<id>/role/
    Auth: Required (superuser only)
    """
    permission_classes = [IsSuperUser]
    
    def patch(self, request, id):
        serializer = UserRoleUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = UserService.get_by_id(id)
            if not user:
                return self.api_response(
                    message=f"User with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            update_data = {'role': serializer.validated_data['role']}
            
            # Only superuser can set is_staff and is_superuser
            if 'is_staff' in serializer.validated_data:
                update_data['is_staff'] = serializer.validated_data['is_staff']
            if 'is_superuser' in serializer.validated_data:
                update_data['is_superuser'] = serializer.validated_data['is_superuser']
            
            updated_user = UserService.update_user(user, **update_data)
            
            if not updated_user:
                return self.api_response(
                    message="Error updating user role.",
                    data=None,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return self.api_response(
                message="User role updated successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error updating user role {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error updating user role.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
