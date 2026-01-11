"""
Admin API Views for VisaRuleVersion Management

Admin-only endpoints for managing visa rule versions.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from django.core.exceptions import ValidationError
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from rules_knowledge.services.visa_rule_version_service import VisaRuleVersionService
from rules_knowledge.serializers.visa_rule_version.read import VisaRuleVersionSerializer, VisaRuleVersionListSerializer
from rules_knowledge.serializers.visa_rule_version.admin import (
    VisaRuleVersionAdminListQuerySerializer,
    VisaRuleVersionPublishSerializer,
    VisaRuleVersionUpdateSerializer,
    BulkVisaRuleVersionOperationSerializer,
)
from django.core.exceptions import ValidationError

logger = logging.getLogger('django')


class VisaRuleVersionAdminListAPI(AuthAPI):
    """
    Admin: Get list of all visa rule versions with advanced filtering.
    
    Endpoint: GET /api/v1/rules-knowledge/admin/visa-rule-versions/
    Auth: Required (staff/superuser only)
    Query Params:
        - visa_type_id: Filter by visa type
        - is_published: Filter by published status
        - jurisdiction: Filter by jurisdiction
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
        - effective_from: Filter by effective_from date
        - effective_to: Filter by effective_to date
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        # Validate query parameters
        query_serializer = VisaRuleVersionAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        # Use service method with filters
        rule_versions = VisaRuleVersionService.get_by_filters(
            visa_type_id=str(validated_params.get('visa_type_id')) if validated_params.get('visa_type_id') else None,
            is_published=validated_params.get('is_published'),
            jurisdiction=validated_params.get('jurisdiction'),
            date_from=validated_params.get('date_from'),
            date_to=validated_params.get('date_to'),
            effective_from=validated_params.get('effective_from'),
            effective_to=validated_params.get('effective_to')
        )
        
        # Paginate results
        from rules_knowledge.helpers.pagination import paginate_queryset
        page = validated_params.get('page', 1)
        page_size = validated_params.get('page_size', 20)
        paginated_items, pagination_metadata = paginate_queryset(rule_versions, page=page, page_size=page_size)
        
        return self.api_response(
            message="Visa rule versions retrieved successfully.",
            data={
                'items': VisaRuleVersionListSerializer(paginated_items, many=True).data,
                'pagination': pagination_metadata
            },
            status_code=status.HTTP_200_OK
        )


class VisaRuleVersionAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed visa rule version information.
    
    Endpoint: GET /api/v1/rules-knowledge/admin/visa-rule-versions/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        rule_version = VisaRuleVersionService.get_by_id(id)
        if not rule_version:
            return self.api_response(
                message=f"Visa rule version with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return self.api_response(
            message="Visa rule version retrieved successfully.",
            data=VisaRuleVersionSerializer(rule_version).data,
            status_code=status.HTTP_200_OK
        )


class VisaRuleVersionAdminUpdateAPI(AuthAPI):
    """
    Admin: Update visa rule version.
    
    Endpoint: PATCH /api/v1/rules-knowledge/admin/visa-rule-versions/<id>/update/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def patch(self, request, id):
        serializer = VisaRuleVersionUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Extract version for optimistic locking if provided
        expected_version = serializer.validated_data.pop('version', None)
        updated_by = request.user if request.user.is_authenticated else None
        
        try:
            updated_rule_version = VisaRuleVersionService.update_rule_version(
                id,
                updated_by=updated_by,
                expected_version=expected_version,
                **serializer.validated_data
            )
            
            if not updated_rule_version:
                return self.api_response(
                    message=f"Visa rule version with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Visa rule version updated successfully.",
                data=VisaRuleVersionSerializer(updated_rule_version).data,
                status_code=status.HTTP_200_OK
            )
        except ValidationError as e:
            # Handle version conflicts (optimistic locking)
            if 'version' in str(e).lower() or 'Version conflict' in str(e) or 'modified by another user' in str(e).lower():
                return self.api_response(
                    message="Visa rule version was modified by another user. Please refresh and try again.",
                    data={'error': 'version_conflict', 'detail': str(e)},
                    status_code=status.HTTP_409_CONFLICT
                )
            # Handle other validation errors
            return self.api_response(
                message=str(e),
                data={'error': 'validation_error', 'detail': str(e)},
                status_code=status.HTTP_400_BAD_REQUEST
            )


class VisaRuleVersionAdminPublishAPI(AuthAPI):
    """
    Admin: Publish or unpublish a visa rule version.
    
    Endpoint: POST /api/v1/rules-knowledge/admin/visa-rule-versions/<id>/publish/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request, id):
        serializer = VisaRuleVersionPublishSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            rule_version = VisaRuleVersionService.get_by_id(id)
            if not rule_version:
                return self.api_response(
                    message=f"Visa rule version with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Extract version for optimistic locking if provided
            expected_version = serializer.validated_data.get('version')
            published_by = request.user if request.user.is_authenticated else None
            
            # Use publish_rule_version for proper optimistic locking support
            if serializer.validated_data['is_published']:
                updated_rule_version = VisaRuleVersionService.publish_rule_version(
                    id, published_by=published_by, expected_version=expected_version
                )
            else:
                # For unpublish, use update_rule_version
                updated_rule_version = VisaRuleVersionService.update_rule_version(
                    id, updated_by=published_by, expected_version=expected_version, is_published=False
                )
            
            if not updated_rule_version:
                return self.api_response(
                    message=f"Visa rule version with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            action = "published" if serializer.validated_data['is_published'] else "unpublished"
            return self.api_response(
                message=f"Visa rule version {action} successfully.",
                data=VisaRuleVersionSerializer(updated_rule_version).data,
                status_code=status.HTTP_200_OK
            )
        except ValidationError as e:
            # Handle version conflicts (optimistic locking)
            if 'version' in str(e).lower() or 'Version conflict' in str(e) or 'modified by another user' in str(e).lower():
                return self.api_response(
                    message="Visa rule version was modified by another user. Please refresh and try again.",
                    data={'error': 'version_conflict', 'detail': str(e)},
                    status_code=status.HTTP_409_CONFLICT
                )
            # Handle other validation errors
            return self.api_response(
                message=str(e),
                data={'error': 'validation_error', 'detail': str(e)},
                status_code=status.HTTP_400_BAD_REQUEST
            )


class VisaRuleVersionAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete visa rule version.
    
    Endpoint: DELETE /api/v1/rules-knowledge/admin/visa-rule-versions/<id>/delete/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        deleted = VisaRuleVersionService.delete_rule_version(id)
        if not deleted:
            return self.api_response(
                message=f"Visa rule version with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return self.api_response(
            message="Visa rule version deleted successfully.",
            data=None,
            status_code=status.HTTP_200_OK
        )


class BulkVisaRuleVersionOperationAPI(AuthAPI):
    """
    Admin: Perform bulk operations on visa rule versions.
    
    Endpoint: POST /api/v1/rules-knowledge/admin/visa-rule-versions/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request):
        serializer = BulkVisaRuleVersionOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        rule_version_ids = serializer.validated_data['rule_version_ids']
        operation = serializer.validated_data['operation']
        
        results = {
            'success': [],
            'failed': []
        }
        
        try:
            for rule_version_id in rule_version_ids:
                try:
                    rule_version = VisaRuleVersionService.get_by_id(str(rule_version_id))
                    if not rule_version:
                        results['failed'].append({
                            'rule_version_id': str(rule_version_id),
                            'error': 'Visa rule version not found'
                        })
                        continue
                    
                    if operation == 'publish':
                        VisaRuleVersionService.publish_rule_version_by_flag(rule_version, True)
                        results['success'].append(str(rule_version_id))
                    elif operation == 'unpublish':
                        VisaRuleVersionService.publish_rule_version_by_flag(rule_version, False)
                        results['success'].append(str(rule_version_id))
                    elif operation == 'delete':
                        deleted = VisaRuleVersionService.delete_rule_version(str(rule_version_id))
                        if deleted:
                            results['success'].append(str(rule_version_id))
                        else:
                            results['failed'].append({
                                'rule_version_id': str(rule_version_id),
                                'error': 'Failed to delete'
                            })
                except Exception as e:
                    results['failed'].append({
                        'rule_version_id': str(rule_version_id),
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
