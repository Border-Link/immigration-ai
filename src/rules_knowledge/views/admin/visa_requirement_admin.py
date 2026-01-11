"""
Admin API Views for VisaRequirement Management

Admin-only endpoints for managing visa requirements.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from rules_knowledge.services.visa_requirement_service import VisaRequirementService
from rules_knowledge.serializers.visa_requirement.read import VisaRequirementSerializer, VisaRequirementListSerializer
from rules_knowledge.serializers.visa_requirement.admin import (
    VisaRequirementAdminListQuerySerializer,
    VisaRequirementUpdateSerializer,
    BulkVisaRequirementOperationSerializer,
)

logger = logging.getLogger('django')


class VisaRequirementAdminListAPI(AuthAPI):
    """
    Admin: Get list of all visa requirements with advanced filtering.
    
    Endpoint: GET /api/v1/rules-knowledge/admin/visa-requirements/
    Auth: Required (staff/superuser only)
    Query Params:
        - rule_version_id: Filter by rule version
        - rule_type: Filter by rule type
        - is_mandatory: Filter by mandatory status
        - requirement_code: Filter by requirement code (partial match)
        - visa_type_id: Filter by visa type
        - jurisdiction: Filter by jurisdiction
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        # Validate query parameters
        query_serializer = VisaRequirementAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        # Use service method with filters
        requirements = VisaRequirementService.get_by_filters(
            rule_version_id=str(validated_params.get('rule_version_id')) if validated_params.get('rule_version_id') else None,
            rule_type=validated_params.get('rule_type'),
            is_mandatory=validated_params.get('is_mandatory'),
            requirement_code=validated_params.get('requirement_code'),
            visa_type_id=str(validated_params.get('visa_type_id')) if validated_params.get('visa_type_id') else None,
            jurisdiction=validated_params.get('jurisdiction'),
            date_from=validated_params.get('date_from'),
            date_to=validated_params.get('date_to')
        )
        
        # Paginate results
        from rules_knowledge.helpers.pagination import paginate_queryset
        page = validated_params.get('page', 1)
        page_size = validated_params.get('page_size', 20)
        paginated_items, pagination_metadata = paginate_queryset(requirements, page=page, page_size=page_size)
        
        return self.api_response(
            message="Visa requirements retrieved successfully.",
            data={
                'items': VisaRequirementListSerializer(paginated_items, many=True).data,
                'pagination': pagination_metadata
            },
            status_code=status.HTTP_200_OK
        )


class VisaRequirementAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed visa requirement information.
    
    Endpoint: GET /api/v1/rules-knowledge/admin/visa-requirements/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        requirement = VisaRequirementService.get_by_id(id)
        if not requirement:
            return self.api_response(
                message=f"Visa requirement with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return self.api_response(
            message="Visa requirement retrieved successfully.",
            data=VisaRequirementSerializer(requirement).data,
            status_code=status.HTTP_200_OK
        )


class VisaRequirementAdminUpdateAPI(AuthAPI):
    """
    Admin: Update visa requirement.
    
    Endpoint: PATCH /api/v1/rules-knowledge/admin/visa-requirements/<id>/update/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def patch(self, request, id):
        serializer = VisaRequirementUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        updated_requirement = VisaRequirementService.update_requirement(
            id,
            **serializer.validated_data
        )
        
        if not updated_requirement:
            return self.api_response(
                message=f"Visa requirement with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return self.api_response(
            message="Visa requirement updated successfully.",
            data=VisaRequirementSerializer(updated_requirement).data,
            status_code=status.HTTP_200_OK
        )


class VisaRequirementAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete visa requirement.
    
    Endpoint: DELETE /api/v1/rules-knowledge/admin/visa-requirements/<id>/delete/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        deleted = VisaRequirementService.delete_requirement(id)
        if not deleted:
            return self.api_response(
                message=f"Visa requirement with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return self.api_response(
            message="Visa requirement deleted successfully.",
            data=None,
            status_code=status.HTTP_200_OK
        )


class BulkVisaRequirementOperationAPI(AuthAPI):
    """
    Admin: Perform bulk operations on visa requirements.
    
    Endpoint: POST /api/v1/rules-knowledge/admin/visa-requirements/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request):
        serializer = BulkVisaRequirementOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        requirement_ids = serializer.validated_data['requirement_ids']
        operation = serializer.validated_data['operation']
        
        results = {
            'success': [],
            'failed': []
        }
        
        for requirement_id in requirement_ids:
            requirement = VisaRequirementService.get_by_id(str(requirement_id))
            if not requirement:
                results['failed'].append({
                    'requirement_id': str(requirement_id),
                    'error': 'Visa requirement not found'
                })
                continue
            
            if operation == 'set_mandatory':
                updated = VisaRequirementService.update_requirement(str(requirement_id), is_mandatory=True)
                if updated:
                    results['success'].append(str(requirement_id))
                else:
                    results['failed'].append({
                        'requirement_id': str(requirement_id),
                        'error': 'Failed to update'
                    })
            elif operation == 'set_optional':
                updated = VisaRequirementService.update_requirement(str(requirement_id), is_mandatory=False)
                if updated:
                    results['success'].append(str(requirement_id))
                else:
                    results['failed'].append({
                        'requirement_id': str(requirement_id),
                        'error': 'Failed to update'
                    })
            elif operation == 'delete':
                deleted = VisaRequirementService.delete_requirement(str(requirement_id))
                if deleted:
                    results['success'].append(str(requirement_id))
                else:
                    results['failed'].append({
                        'requirement_id': str(requirement_id),
                        'error': 'Failed to delete'
                    })
        
        return self.api_response(
            message=f"Bulk operation '{operation}' completed. {len(results['success'])} succeeded, {len(results['failed'])} failed.",
            data=results,
            status_code=status.HTTP_200_OK
        )
