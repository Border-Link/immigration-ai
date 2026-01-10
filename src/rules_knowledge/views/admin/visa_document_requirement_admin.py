"""
Admin API Views for VisaDocumentRequirement Management

Admin-only endpoints for managing visa document requirements.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from rules_knowledge.services.visa_document_requirement_service import VisaDocumentRequirementService
from rules_knowledge.serializers.visa_document_requirement.read import (
    VisaDocumentRequirementSerializer,
    VisaDocumentRequirementListSerializer
)
from rules_knowledge.serializers.visa_document_requirement.admin import (
    VisaDocumentRequirementUpdateSerializer,
    BulkVisaDocumentRequirementOperationSerializer,
)
from django.utils.dateparse import parse_datetime

logger = logging.getLogger('django')


class VisaDocumentRequirementAdminListAPI(AuthAPI):
    """
    Admin: Get list of all visa document requirements with advanced filtering.
    
    Endpoint: GET /api/v1/rules-knowledge/admin/visa-document-requirements/
    Auth: Required (staff/superuser only)
    Query Params:
        - rule_version_id: Filter by rule version
        - document_type_id: Filter by document type
        - mandatory: Filter by mandatory status
        - visa_type_id: Filter by visa type
        - jurisdiction: Filter by jurisdiction
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        rule_version_id = request.query_params.get('rule_version_id', None)
        document_type_id = request.query_params.get('document_type_id', None)
        mandatory = request.query_params.get('mandatory', None)
        visa_type_id = request.query_params.get('visa_type_id', None)
        jurisdiction = request.query_params.get('jurisdiction', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        
        try:
            # Parse dates
            parsed_date_from = parse_datetime(date_from) if date_from and isinstance(date_from, str) else date_from
            parsed_date_to = parse_datetime(date_to) if date_to and isinstance(date_to, str) else date_to
            mandatory_bool = mandatory.lower() == 'true' if mandatory is not None else None
            
            # Use service method with filters
            document_requirements = VisaDocumentRequirementService.get_by_filters(
                rule_version_id=rule_version_id,
                document_type_id=document_type_id,
                mandatory=mandatory_bool,
                visa_type_id=visa_type_id,
                jurisdiction=jurisdiction,
                date_from=parsed_date_from,
                date_to=parsed_date_to
            )
            
            return self.api_response(
                message="Visa document requirements retrieved successfully.",
                data=VisaDocumentRequirementListSerializer(document_requirements, many=True).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving visa document requirements: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving visa document requirements.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VisaDocumentRequirementAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed visa document requirement information.
    
    Endpoint: GET /api/v1/rules-knowledge/admin/visa-document-requirements/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        try:
            document_requirement = VisaDocumentRequirementService.get_by_id(id)
            if not document_requirement:
                return self.api_response(
                    message=f"Visa document requirement with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Visa document requirement retrieved successfully.",
                data=VisaDocumentRequirementSerializer(document_requirement).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving visa document requirement {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving visa document requirement.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VisaDocumentRequirementAdminUpdateAPI(AuthAPI):
    """
    Admin: Update visa document requirement.
    
    Endpoint: PATCH /api/v1/rules-knowledge/admin/visa-document-requirements/<id>/update/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def patch(self, request, id):
        serializer = VisaDocumentRequirementUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            document_requirement = VisaDocumentRequirementService.get_by_id(id)
            if not document_requirement:
                return self.api_response(
                    message=f"Visa document requirement with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            updated_document_requirement = VisaDocumentRequirementService.update_document_requirement(
                id,
                **serializer.validated_data
            )
            
            return self.api_response(
                message="Visa document requirement updated successfully.",
                data=VisaDocumentRequirementSerializer(updated_document_requirement).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error updating visa document requirement {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error updating visa document requirement.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VisaDocumentRequirementAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete visa document requirement.
    
    Endpoint: DELETE /api/v1/rules-knowledge/admin/visa-document-requirements/<id>/delete/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        try:
            document_requirement = VisaDocumentRequirementService.get_by_id(id)
            if not document_requirement:
                return self.api_response(
                    message=f"Visa document requirement with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            deleted = VisaDocumentRequirementService.delete_document_requirement(id)
            if not deleted:
                return self.api_response(
                    message="Error deleting visa document requirement.",
                    data=None,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return self.api_response(
                message="Visa document requirement deleted successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deleting visa document requirement {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error deleting visa document requirement.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkVisaDocumentRequirementOperationAPI(AuthAPI):
    """
    Admin: Perform bulk operations on visa document requirements.
    
    Endpoint: POST /api/v1/rules-knowledge/admin/visa-document-requirements/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request):
        serializer = BulkVisaDocumentRequirementOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        document_requirement_ids = serializer.validated_data['document_requirement_ids']
        operation = serializer.validated_data['operation']
        
        results = {
            'success': [],
            'failed': []
        }
        
        try:
            for document_requirement_id in document_requirement_ids:
                try:
                    document_requirement = VisaDocumentRequirementService.get_by_id(str(document_requirement_id))
                    if not document_requirement:
                        results['failed'].append({
                            'document_requirement_id': str(document_requirement_id),
                            'error': 'Visa document requirement not found'
                        })
                        continue
                    
                    if operation == 'set_mandatory':
                        VisaDocumentRequirementService.update_document_requirement(
                            str(document_requirement_id),
                            mandatory=True
                        )
                        results['success'].append(str(document_requirement_id))
                    elif operation == 'set_optional':
                        VisaDocumentRequirementService.update_document_requirement(
                            str(document_requirement_id),
                            mandatory=False
                        )
                        results['success'].append(str(document_requirement_id))
                    elif operation == 'delete':
                        deleted = VisaDocumentRequirementService.delete_document_requirement(str(document_requirement_id))
                        if deleted:
                            results['success'].append(str(document_requirement_id))
                        else:
                            results['failed'].append({
                                'document_requirement_id': str(document_requirement_id),
                                'error': 'Failed to delete'
                            })
                except Exception as e:
                    results['failed'].append({
                        'document_requirement_id': str(document_requirement_id),
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
