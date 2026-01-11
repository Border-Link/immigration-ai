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
    CaseFactAdminUpdateSerializer,
    BulkCaseFactOperationSerializer,
)
from django.utils.dateparse import parse_datetime
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
        case_id = request.query_params.get('case_id', None)
        fact_key = request.query_params.get('fact_key', None)
        source = request.query_params.get('source', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        
        try:
            facts = CaseFactService.get_by_filters(
                case_id=case_id,
                fact_key=fact_key,
                source=source,
                date_from=parse_datetime(date_from) if date_from else None,
                date_to=parse_datetime(date_to) if date_to else None,
            )
            
            return self.api_response(
                message="Case facts retrieved successfully.",
                data=CaseFactListSerializer(facts, many=True).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving case facts: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving case facts.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CaseFactAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed case fact information.
    
    Endpoint: GET /api/v1/immigration-cases/admin/case-facts/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        try:
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
        except Exception as e:
            logger.error(f"Error retrieving case fact {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving case fact.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
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
        
        try:
            fact = CaseFactService.get_by_id(id)
            if not fact:
                return self.api_response(
                    message=f"Case fact with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            updated_fact = CaseFactService.update_case_fact(id, **serializer.validated_data)
            
            return self.api_response(
                message="Case fact updated successfully.",
                data=CaseFactSerializer(updated_fact).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error updating case fact {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error updating case fact.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CaseFactAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete a case fact.
    
    Endpoint: DELETE /api/v1/immigration-cases/admin/case-facts/<id>/delete/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        try:
            fact = CaseFactService.get_by_id(id)
            if not fact:
                return self.api_response(
                    message=f"Case fact with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            deleted = CaseFactService.delete_case_fact(id)
            if not deleted:
                return self.api_response(
                    message="Error deleting case fact.",
                    data=None,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return self.api_response(
                message="Case fact deleted successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deleting case fact {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error deleting case fact.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
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
            try:
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
                        raise Exception("Failed to delete case fact.")
                    continue # Skip serialization for deleted items
                elif operation == 'update_source':
                    if not source:
                        raise ValueError("source is required for 'update_source' operation.")
                    updated_fact = CaseFactService.update_case_fact(str(fact_id), source=source)
                    if updated_fact:
                        results['success'].append(CaseFactSerializer(updated_fact).data)
                    else:
                        raise Exception("Failed to update case fact.")
                else:
                    raise ValueError(f"Invalid operation: {operation}")
            except Exception as e:
                results['failed'].append({
                    'case_fact_id': str(fact_id),
                    'error': str(e)
                })
        
        return self.api_response(
            message=f"Bulk operation '{operation}' completed. {len(results['success'])} succeeded, {len(results['failed'])} failed.",
            data=results,
            status_code=status.HTTP_200_OK
        )
