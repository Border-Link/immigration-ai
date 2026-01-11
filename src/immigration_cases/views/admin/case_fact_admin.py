"""
Admin API Views for CaseFact Management

Admin-only endpoints for managing case facts.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from immigration_cases.services.case_fact_service import CaseFactService
from immigration_cases.serializers.case_fact.read import CaseFactSerializer, CaseFactListSerializer
from immigration_cases.serializers.case_fact.admin import (
    CaseFactAdminListQuerySerializer,
    CaseFactAdminUpdateSerializer,
    BulkCaseFactOperationSerializer,
)
from immigration_cases.helpers.pagination import paginate_queryset

logger = logging.getLogger('django')


class CaseFactAdminListAPI(AuthAPI):
    """
    Admin: Get list of all case facts with advanced filtering.
    
    Endpoint: GET /api/v1/immigration-cases/admin/case-facts/
    Auth: Required (staff/superuser only)
    Query Params:
        - case_id: Filter by case ID
        - fact_key: Filter by fact key
        - source: Filter by source (user, ai, reviewer)
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        # Validate query parameters
        query_serializer = CaseFactAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        facts = CaseFactService.get_by_filters(
            case_id=str(validated_params.get('case_id')) if validated_params.get('case_id') else None,
            fact_key=validated_params.get('fact_key'),
            source=validated_params.get('source'),
            date_from=validated_params.get('date_from'),
            date_to=validated_params.get('date_to'),
        )
        
        return self.api_response(
            message="Case facts retrieved successfully.",
            data=CaseFactListSerializer(facts, many=True).data,
            status_code=status.HTTP_200_OK
        )


class CaseFactAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed case fact information.
    
    Endpoint: GET /api/v1/immigration-cases/admin/case-facts/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        fact = CaseFactService.get_by_id(id)
        if not fact:
            return self.api_response(
                message=f"Case fact with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return self.api_response(
            message="Case fact retrieved successfully.",
            data=CaseFactSerializer(fact).data,
            status_code=status.HTTP_200_OK
        )


class CaseFactAdminUpdateAPI(AuthAPI):
    """
    Admin: Update case fact value or source.
    
    Endpoint: PATCH /api/v1/immigration-cases/admin/case-facts/<id>/update/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def patch(self, request, id):
        serializer = CaseFactAdminUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        updated_fact = CaseFactService.update_case_fact(id, **serializer.validated_data)
        if not updated_fact:
            return self.api_response(
                message=f"Case fact with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return self.api_response(
            message="Case fact updated successfully.",
            data=CaseFactSerializer(updated_fact).data,
            status_code=status.HTTP_200_OK
        )


class CaseFactAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete a case fact.
    
    Endpoint: DELETE /api/v1/immigration-cases/admin/case-facts/<id>/delete/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        deleted = CaseFactService.delete_case_fact(id)
        if not deleted:
            return self.api_response(
                message=f"Case fact with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return self.api_response(
            message="Case fact deleted successfully.",
            data=None,
            status_code=status.HTTP_200_OK
        )


class BulkCaseFactOperationAPI(AuthAPI):
    """
    Admin: Perform bulk operations on case facts (delete, update_source).
    
    Endpoint: POST /api/v1/immigration-cases/admin/case-facts/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request):
        serializer = BulkCaseFactOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        case_fact_ids = serializer.validated_data['case_fact_ids']
        operation = serializer.validated_data['operation']
        source = serializer.validated_data.get('source')
        
        results = {
            'success': [],
            'failed': []
        }
        
        for fact_id in case_fact_ids:
            fact = CaseFactService.get_by_id(str(fact_id))
            if not fact:
                results['failed'].append({
                    'case_fact_id': str(fact_id),
                    'error': 'Case fact not found'
                })
                continue
            
            if operation == 'delete':
                deleted = CaseFactService.delete_case_fact(str(fact_id))
                if deleted:
                    results['success'].append(str(fact_id))
                else:
                    results['failed'].append({
                        'case_fact_id': str(fact_id),
                        'error': 'Failed to delete case fact.'
                    })
            elif operation == 'update_source':
                if not source:
                    results['failed'].append({
                        'case_fact_id': str(fact_id),
                        'error': "source is required for 'update_source' operation."
                    })
                    continue
                updated_fact = CaseFactService.update_case_fact(str(fact_id), source=source)
                if updated_fact:
                    results['success'].append(CaseFactSerializer(updated_fact).data)
                else:
                    results['failed'].append({
                        'case_fact_id': str(fact_id),
                        'error': 'Failed to update case fact.'
                    })
            else:
                results['failed'].append({
                    'case_fact_id': str(fact_id),
                    'error': f"Invalid operation: {operation}"
                })
        
        return self.api_response(
            message=f"Bulk operation '{operation}' completed. {len(results['success'])} succeeded, {len(results['failed'])} failed.",
            data=results,
            status_code=status.HTTP_200_OK
        )
