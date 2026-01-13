"""
Advanced Admin API Views for User Management

Advanced admin-only endpoints for comprehensive user management.
Includes suspension, verification, bulk operations, password reset, etc.
Access restricted to staff/superusers using IsAdminOrStaff permission.

Features:
- User suspension/unsuspension with expiration dates
- User verification management
- Bulk user operations
- Admin password reset (superuser only)
- Role management (superuser only)
- Comprehensive error handling and audit logging
- Security validations (prevent self-modification, protect superusers)
"""
import logging
from rest_framework import status
from django.utils import timezone
from main_system.base.auth_api import AuthAPI
from main_system.permissions.admin_permission import AdminPermission
from main_system.permissions.is_superadmin import IsSuperAdmin
from users_access.services.user_service import UserService
from users_access.serializers.users.admin import (
    UserSuspendSerializer,
    UserVerifySerializer,
    BulkUserOperationSerializer,
    AdminPasswordResetSerializer,
    UserRoleUpdateSerializer,
)

logger = logging.getLogger('django')


class UserSuspendAPI(AuthAPI):
    """
    Admin: Suspend a user (temporary ban with optional expiration).
    
    Endpoint: POST /api/v1/auth/admin/users/<id>/suspend/
    Auth: Required (staff/superuser only)
    
    Request body:
    {
        "reason": "Optional reason for suspension",
        "suspended_until": "Optional ISO datetime for automatic unsuspension"
    }
    """
    permission_classes = [AdminPermission]
    
    def post(self, request, id):
        serializer = UserSuspendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get target user
        target_user = UserService.get_by_id(id)
        if not target_user:
            return self.api_response(
                message=f"User with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Security: Prevent self-suspension
        if str(target_user.id) == str(request.user.id):
            return self.api_response(
                message="You cannot suspend yourself.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Security: Prevent suspension of superusers (unless current user is also superuser)
        if target_user.is_superuser and not request.user.is_superuser:
            return self.api_response(
                message="You cannot suspend a superuser account.",
                data=None,
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Check if already suspended
        if not target_user.is_active:
            return self.api_response(
                message="User is already suspended.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Deactivate user
        updated_user = UserService.deactivate_user_by_id(id)
        if not updated_user:
            return self.api_response(
                message="Error suspending user.",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Extract suspension details
        reason = serializer.validated_data.get('reason', 'No reason provided')
        suspended_until = serializer.validated_data.get('suspended_until')
        
        # Log audit event
        try:
            from compliance.services.audit_log_service import AuditLogService
            suspended_until_str = suspended_until.isoformat() if suspended_until else 'No expiration'
            AuditLogService.create_audit_log(
                level='WARNING',
                logger_name='users_access',
                message=f"User {target_user.email} (ID: {target_user.id}) suspended by {request.user.email} (ID: {request.user.id}). Reason: {reason}. Suspended until: {suspended_until_str}",
                func_name='UserSuspendAPI.post',
                pathname=__file__,
                user=request.user
            )
        except Exception as audit_error:
            logger.warning(f"Failed to create audit log for user suspension: {audit_error}")
        
        # Schedule automatic unsuspension if suspended_until is provided
        if suspended_until:
            try:
                from users_access.tasks.user_tasks import schedule_user_unsuspension_task
                schedule_user_unsuspension_task.apply_async(
                    args=[str(target_user.id)],
                    eta=suspended_until
                )
                logger.info(f"Scheduled automatic unsuspension for user {target_user.id} at {suspended_until.isoformat()}")
            except Exception as task_error:
                logger.warning(f"Failed to schedule automatic unsuspension task: {task_error}")
                # Don't fail the request if task scheduling fails
        
        # Build response message
        message = f"User suspended successfully. Reason: {reason}"
        if suspended_until:
            message += f" Suspended until: {suspended_until.isoformat()}"
        
        # Return response with user details
        from users_access.serializers.users.admin import UserAdminDetailSerializer
        return self.api_response(
            message=message,
            data=UserAdminDetailSerializer(updated_user).data,
            status_code=status.HTTP_200_OK
        )


class UserUnsuspendAPI(AuthAPI):
    """
    Admin: Unsuspend a user (reactivate).
    
    Endpoint: POST /api/v1/auth/admin/users/<id>/unsuspend/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def post(self, request, id):
        # Get target user
        target_user = UserService.get_by_id(id)
        if not target_user:
            return self.api_response(
                message=f"User with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check if already active
        if target_user.is_active:
            return self.api_response(
                message="User is already active.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Activate user
        updated_user = UserService.activate_user_by_id(id)
        if not updated_user:
            return self.api_response(
                message="Error unsuspending user.",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Log audit event
        try:
            from compliance.services.audit_log_service import AuditLogService
            AuditLogService.create_audit_log(
                level='INFO',
                logger_name='users_access',
                message=f"User {target_user.email} (ID: {target_user.id}) unsuspended by {request.user.email} (ID: {request.user.id})",
                func_name='UserUnsuspendAPI.post',
                pathname=__file__,
                user=request.user
            )
        except Exception as audit_error:
            logger.warning(f"Failed to create audit log for user unsuspension: {audit_error}")
        
        # Return response with user details
        from users_access.serializers.users.admin import UserAdminDetailSerializer
        return self.api_response(
            message="User unsuspended successfully.",
            data=UserAdminDetailSerializer(updated_user).data,
            status_code=status.HTTP_200_OK
        )


class UserVerifyAPI(AuthAPI):
    """
    Admin: Verify or unverify a user's email.
    
    Endpoint: POST /api/v1/auth/admin/users/<id>/verify/
    Auth: Required (staff/superuser only)
    
    Request body:
    {
        "is_verified": true/false
    }
    """
    permission_classes = [AdminPermission]
    
    def post(self, request, id):
        serializer = UserVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        target_user = UserService.get_by_id(id)
        if not target_user:
            return self.api_response(
                message=f"User with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        is_verified = serializer.validated_data['is_verified']
        
        # Check if already in desired state
        if target_user.is_verified == is_verified:
            action = "verified" if is_verified else "unverified"
            return self.api_response(
                message=f"User is already {action}.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        updated_user = UserService.update_user(
            target_user,
            is_verified=is_verified
        )
        
        if not updated_user:
            return self.api_response(
                message="Error updating user verification status.",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Log audit event
        try:
            from compliance.services.audit_log_service import AuditLogService
            action = "verified" if is_verified else "unverified"
            AuditLogService.create_audit_log(
                level='INFO',
                logger_name='users_access',
                message=f"User {target_user.email} (ID: {target_user.id}) {action} by {request.user.email} (ID: {request.user.id})",
                func_name='UserVerifyAPI.post',
                pathname=__file__,
                user=request.user
            )
        except Exception as audit_error:
            logger.warning(f"Failed to create audit log for user verification: {audit_error}")
        
        # Return response with user details
        from users_access.serializers.users.admin import UserAdminDetailSerializer
        action = "verified" if is_verified else "unverified"
        return self.api_response(
            message=f"User {action} successfully.",
            data=UserAdminDetailSerializer(updated_user).data,
            status_code=status.HTTP_200_OK
        )


class BulkUserOperationAPI(AuthAPI):
    """
    Admin: Perform bulk operations on multiple users.
    
    Endpoint: POST /api/v1/auth/admin/users/bulk-operation/
    Auth: Required (staff/superuser only)
    
    Request body:
    {
        "user_ids": ["uuid1", "uuid2", ...],
        "operation": "activate|deactivate|verify|unverify|delete|promote_to_reviewer|demote_from_reviewer",
        "reason": "Optional reason for the operation"
    }
    
    Operations:
    - activate: Activate users
    - deactivate: Deactivate users
    - verify: Verify user emails
    - unverify: Unverify user emails
    - delete: Soft delete users (deactivate)
    - promote_to_reviewer: Promote users to reviewer role
    - demote_from_reviewer: Demote reviewers to user role
    """
    permission_classes = [AdminPermission]
    
    def post(self, request):
        serializer = BulkUserOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_ids = serializer.validated_data['user_ids']
        operation = serializer.validated_data['operation']
        reason = serializer.validated_data.get('reason', '')
        
        # Limit bulk operations to prevent abuse
        MAX_BULK_OPERATIONS = 100
        if len(user_ids) > MAX_BULK_OPERATIONS:
            return self.api_response(
                message=f"Too many users specified. Maximum {MAX_BULK_OPERATIONS} allowed per operation.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        results = {
            'success': [],
            'failed': [],
            'skipped': []
        }
        
        current_user_id = str(request.user.id)
        is_superuser = request.user.is_superuser
        
        for user_id in user_ids:
            user_id_str = str(user_id)
            
            try:
                user = UserService.get_by_id(user_id_str)
                if not user:
                    results['failed'].append({
                        'user_id': user_id_str,
                        'error': 'User not found'
                    })
                    continue
                
                # Security: Prevent self-modification for certain operations
                if user_id_str == current_user_id and operation in ['deactivate', 'delete']:
                    results['skipped'].append({
                        'user_id': user_id_str,
                        'error': 'Cannot perform this operation on yourself'
                    })
                    continue
                
                # Security: Prevent modification of superusers (unless current user is also superuser)
                if user.is_superuser and not is_superuser and operation in ['deactivate', 'delete', 'demote_from_reviewer']:
                    results['skipped'].append({
                        'user_id': user_id_str,
                        'error': 'Cannot modify superuser account'
                    })
                    continue
                
                # Perform operation
                updated = None
                
                if operation == 'activate':
                    updated = UserService.activate_user_by_id(user_id_str)
                elif operation == 'deactivate':
                    updated = UserService.deactivate_user_by_id(user_id_str)
                elif operation == 'verify':
                    updated = UserService.update_user(user, is_verified=True)
                elif operation == 'unverify':
                    updated = UserService.update_user(user, is_verified=False)
                elif operation == 'delete':
                    # Soft delete by deactivating
                    updated = UserService.deactivate_user_by_id(user_id_str)
                elif operation == 'promote_to_reviewer':
                    if user.role != 'reviewer':
                        updated = UserService.update_user(
                            user,
                            role='reviewer',
                            is_staff=True
                        )
                    else:
                        results['skipped'].append({
                            'user_id': user_id_str,
                            'error': 'User is already a reviewer'
                        })
                        continue
                elif operation == 'demote_from_reviewer':
                    if user.role == 'reviewer':
                        updated = UserService.update_user(
                            user,
                            role='user',
                            is_staff=False
                        )
                    else:
                        results['skipped'].append({
                            'user_id': user_id_str,
                            'error': 'User is not a reviewer'
                        })
                        continue
                else:
                    results['failed'].append({
                        'user_id': user_id_str,
                        'error': f'Unknown operation: {operation}'
                    })
                    continue
                
                if updated:
                    results['success'].append(user_id_str)
                else:
                    results['failed'].append({
                        'user_id': user_id_str,
                        'error': 'Operation failed'
                    })
                    
            except Exception as e:
                logger.error(f"Error processing bulk operation for user {user_id_str}: {e}", exc_info=True)
                results['failed'].append({
                    'user_id': user_id_str,
                    'error': str(e)
                })
                continue
        
        # Log audit event
        try:
            from compliance.services.audit_log_service import AuditLogService
            AuditLogService.create_audit_log(
                level='INFO',
                logger_name='users_access',
                message=f"Bulk operation '{operation}' performed by {request.user.email} (ID: {request.user.id}). "
                       f"Total: {len(user_ids)}, Success: {len(results['success'])}, "
                       f"Failed: {len(results['failed'])}, Skipped: {len(results['skipped'])}. "
                       f"Reason: {reason if reason else 'No reason provided'}",
                func_name='BulkUserOperationAPI.post',
                pathname=__file__,
                user=request.user
            )
        except Exception as audit_error:
            logger.warning(f"Failed to create audit log for bulk operation: {audit_error}")
        
        total_processed = len(results['success']) + len(results['failed']) + len(results['skipped'])
        message = (
            f"Bulk operation '{operation}' completed. "
            f"{len(results['success'])} succeeded, "
            f"{len(results['failed'])} failed, "
            f"{len(results['skipped'])} skipped."
        )
        
        status_code = status.HTTP_200_OK
        if len(results['failed']) > 0 and len(results['success']) == 0:
            status_code = status.HTTP_207_MULTI_STATUS  # Partial success
        
        return self.api_response(
            message=message,
            data=results,
            status_code=status_code
        )


class AdminPasswordResetAPI(AuthAPI):
    """
    Admin: Reset a user's password (superuser only for security).
    
    Endpoint: POST /api/v1/auth/admin/users/<id>/reset-password/
    Auth: Required (superuser only)
    
    Request body:
    {
        "new_password": "New password (min 8 characters)",
        "send_email": true/false (optional, default: false)
    }
    """
    permission_classes = [IsSuperAdmin]
    
    def post(self, request, id):
        serializer = AdminPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        target_user = UserService.get_by_id(id)
        if not target_user:
            return self.api_response(
                message=f"User with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        new_password = serializer.validated_data['new_password']
        send_email = serializer.validated_data.get('send_email', False)
        
        # Validate password strength
        if len(new_password) < 8:
            return self.api_response(
                message="Password must be at least 8 characters long.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Reset password
        updated_user = UserService.update_password(target_user, new_password)
        
        if not updated_user:
            return self.api_response(
                message="Error resetting password.",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Log audit event (critical security operation)
        try:
            from compliance.services.audit_log_service import AuditLogService
            email_note = "Email notification requested" if send_email else "No email notification"
            AuditLogService.create_audit_log(
                level='WARNING',
                logger_name='users_access',
                message=f"Password reset for user {target_user.email} (ID: {target_user.id}) by superuser {request.user.email} (ID: {request.user.id}). {email_note}",
                func_name='AdminPasswordResetAPI.post',
                pathname=__file__,
                user=request.user
            )
        except Exception as audit_error:
            logger.warning(f"Failed to create audit log for password reset: {audit_error}")
        
        # Send email notification if requested
        email_sent = False
        if send_email:
            try:
                from users_access.tasks.email_tasks import send_admin_password_reset_email_task
                send_admin_password_reset_email_task.delay(
                    user_id=str(target_user.id),
                    new_password=new_password,
                    reset_by_email=request.user.email
                )
                email_sent = True
                logger.info(f"Password reset email queued for user {target_user.email}")
            except ImportError:
                # Task doesn't exist yet - log but don't fail
                logger.warning(f"Password reset email task not found. Email notification requested but not sent.")
            except Exception as email_error:
                logger.error(f"Failed to queue password reset email: {email_error}")
                # Don't fail the request if email fails
        
        # Return response with user details (without password)
        from users_access.serializers.users.admin import UserAdminDetailSerializer
        message = "Password reset successfully."
        if send_email:
            message += " Email notification sent." if email_sent else " Email notification requested but could not be sent."
        
        return self.api_response(
            message=message,
            data=UserAdminDetailSerializer(updated_user).data,
            status_code=status.HTTP_200_OK
        )


class UserRoleManagementAPI(AuthAPI):
    """
    Admin: Update user role and permissions (superuser only).
    
    Endpoint: PATCH /api/v1/auth/admin/users/<id>/role/
    Auth: Required (superuser only)
    
    Request body:
    {
        "role": "user|reviewer|admin",
        "is_staff": true/false (optional),
        "is_superuser": true/false (optional)
    }
    """
    permission_classes = [IsSuperAdmin]
    
    def patch(self, request, id):
        serializer = UserRoleUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        target_user = UserService.get_by_id(id)
        if not target_user:
            return self.api_response(
                message=f"User with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Security: Prevent self-demotion from superuser
        if str(target_user.id) == str(request.user.id):
            new_is_superuser = serializer.validated_data.get('is_superuser')
            if new_is_superuser is False:
                return self.api_response(
                    message="You cannot remove superuser status from yourself.",
                    data=None,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        
        # Build update data
        update_data = {'role': serializer.validated_data['role']}
        
        # Only superuser can set is_staff and is_superuser
        if 'is_staff' in serializer.validated_data:
            update_data['is_staff'] = serializer.validated_data['is_staff']
        if 'is_superuser' in serializer.validated_data:
            update_data['is_superuser'] = serializer.validated_data['is_superuser']
        
        # Validate role consistency
        new_role = update_data['role']
        if new_role == 'reviewer' and not update_data.get('is_staff', target_user.is_staff):
            # Reviewers should be staff
            update_data['is_staff'] = True
        
        # Check if changes are needed
        has_changes = False
        if target_user.role != new_role:
            has_changes = True
        if 'is_staff' in update_data and target_user.is_staff != update_data['is_staff']:
            has_changes = True
        if 'is_superuser' in update_data and target_user.is_superuser != update_data['is_superuser']:
            has_changes = True
        
        if not has_changes:
            return self.api_response(
                message="No changes to apply. User already has the specified role and permissions.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Store old values for audit log
        old_role = target_user.role
        old_is_staff = target_user.is_staff
        old_is_superuser = target_user.is_superuser
        
        updated_user = UserService.update_user(target_user, **update_data)
        
        if not updated_user:
            return self.api_response(
                message="Error updating user role.",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Log audit event (critical security operation)
        try:
            from compliance.services.audit_log_service import AuditLogService
            changes = []
            if old_role != new_role:
                changes.append(f"role: {old_role} -> {new_role}")
            if 'is_staff' in update_data and old_is_staff != update_data['is_staff']:
                changes.append(f"is_staff: {old_is_staff} -> {update_data['is_staff']}")
            if 'is_superuser' in update_data and old_is_superuser != update_data['is_superuser']:
                changes.append(f"is_superuser: {old_is_superuser} -> {update_data['is_superuser']}")
            
            changes_str = ', '.join(changes) if changes else 'No changes'
            AuditLogService.create_audit_log(
                level='WARNING',
                logger_name='users_access',
                message=f"Role updated for user {target_user.email} (ID: {target_user.id}) by superuser {request.user.email} (ID: {request.user.id}). Changes: {changes_str}",
                func_name='UserRoleManagementAPI.patch',
                pathname=__file__,
                user=request.user
            )
        except Exception as audit_error:
            logger.warning(f"Failed to create audit log for role update: {audit_error}")
        
        # Return response with updated user details
        from users_access.serializers.users.admin import UserAdminDetailSerializer
        return self.api_response(
            message="User role updated successfully.",
            data=UserAdminDetailSerializer(updated_user).data,
            status_code=status.HTTP_200_OK
        )
