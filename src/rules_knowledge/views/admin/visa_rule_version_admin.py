"""
Admin API Views for VisaRuleVersion Management

Admin-only endpoints for managing visa rule versions.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from rules_knowledge.services.visa_rule_version_service import VisaRuleVersionService
from rules_knowledge.serializers.visa_rule_version.read import VisaRuleVersionSerializer, VisaRuleVersionListSerializer
from rules_knowledge.serializers.visa_rule_version.admin import (
    VisaRuleVersionPublishSerializer,
    VisaRuleVersionUpdateSerializer,
    BulkVisaRuleVersionOperationSerializer,
)
from django.utils.dateparse import parse_datetime

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
        visa_type_id = request.query_params.get('visa_type_id', None)
        is_published = request.query_params.get('is_published', None)
        jurisdiction = request.query_params.get('jurisdiction', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        effective_from = request.query_params.get('effective_from', None)
        effective_to = request.query_params.get('effective_to', None)
        
        try:
            # Parse dates
            parsed_date_from = parse_datetime(date_from) if date_from and isinstance(date_from, str) else date_from
            parsed_date_to = parse_datetime(date_to) if date_to and isinstance(date_to, str) else date_to
            parsed_effective_from = parse_datetime(effective_from) if effective_from and isinstance(effective_from, str) else effective_from
            parsed_effective_to = parse_datetime(effective_to) if effective_to and isinstance(effective_to, str) else effective_to
            is_published_bool = is_published.lower() == 'true' if is_published is not None else None
            
            # Use service method with filters
            rule_versions = VisaRuleVersionService.get_by_filters(
                visa_type_id=visa_type_id,
                is_published=is_published_bool,
                jurisdiction=jurisdiction,
                date_from=parsed_date_from,
                date_to=parsed_date_to,
                effective_from=parsed_effective_from,
                effective_to=parsed_effective_to
            )
            
            return self.api_response(
                message="Visa rule versions retrieved successfully.",
                data=VisaRuleVersionListSerializer(rule_versions, many=True).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving visa rule versions: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving visa rule versions.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VisaRuleVersionAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed visa rule version information.
    
    Endpoint: GET /api/v1/rules-knowledge/admin/visa-rule-versions/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        try:
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
        except Exception as e:
            logger.error(f"Error retrieving visa rule version {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving visa rule version.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
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
        
        try:
            rule_version = VisaRuleVersionService.get_by_id(id)
            if not rule_version:
                return self.api_response(
                    message=f"Visa rule version with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            updated_rule_version = VisaRuleVersionService.update_rule_version(
                id,
                **serializer.validated_data
            )
            
            return self.api_response(
                message="Visa rule version updated successfully.",
                data=VisaRuleVersionSerializer(updated_rule_version).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error updating visa rule version {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error updating visa rule version.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
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
            
            updated_rule_version = VisaRuleVersionService.publish_rule_version_by_flag(
                rule_version,
                serializer.validated_data['is_published']
            )
            
            action = "published" if serializer.validated_data['is_published'] else "unpublished"
            return self.api_response(
                message=f"Visa rule version {action} successfully.",
                data=VisaRuleVersionSerializer(updated_rule_version).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error publishing/unpublishing visa rule version {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error publishing/unpublishing visa rule version.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VisaRuleVersionAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete visa rule version.
    
    Endpoint: DELETE /api/v1/rules-knowledge/admin/visa-rule-versions/<id>/delete/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        try:
            rule_version = VisaRuleVersionService.get_by_id(id)
            if not rule_version:
                return self.api_response(
                    message=f"Visa rule version with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            deleted = VisaRuleVersionService.delete_rule_version(id)
            if not deleted:
                return self.api_response(
                    message="Error deleting visa rule version.",
                    data=None,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return self.api_response(
                message="Visa rule version deleted successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deleting visa rule version {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error deleting visa rule version.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
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
