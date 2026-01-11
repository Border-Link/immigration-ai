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
    VisaRequirementUpdateSerializer,
    BulkVisaRequirementOperationSerializer,
)
from django.utils.dateparse import parse_datetime

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
        rule_version_id = request.query_params.get('rule_version_id', None)
        rule_type = request.query_params.get('rule_type', None)
        is_mandatory = request.query_params.get('is_mandatory', None)
        requirement_code = request.query_params.get('requirement_code', None)
        visa_type_id = request.query_params.get('visa_type_id', None)
        jurisdiction = request.query_params.get('jurisdiction', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        
        try:
            # Parse dates
            parsed_date_from = parse_datetime(date_from) if date_from and isinstance(date_from, str) else date_from
            parsed_date_to = parse_datetime(date_to) if date_to and isinstance(date_to, str) else date_to
            is_mandatory_bool = is_mandatory.lower() == 'true' if is_mandatory is not None else None
            
            # Use service method with filters
            requirements = VisaRequirementService.get_by_filters(
                rule_version_id=rule_version_id,
                rule_type=rule_type,
                is_mandatory=is_mandatory_bool,
                requirement_code=requirement_code,
                visa_type_id=visa_type_id,
                jurisdiction=jurisdiction,
                date_from=parsed_date_from,
                date_to=parsed_date_to
            )
            
            return self.api_response(
                message="Visa requirements retrieved successfully.",
                data=VisaRequirementListSerializer(requirements, many=True).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving visa requirements: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving visa requirements.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VisaRequirementAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed visa requirement information.
    
    Endpoint: GET /api/v1/rules-knowledge/admin/visa-requirements/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        try:
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
        except Exception as e:
            logger.error(f"Error retrieving visa requirement {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving visa requirement.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
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
        
        try:
            requirement = VisaRequirementService.get_by_id(id)
            if not requirement:
                return self.api_response(
                    message=f"Visa requirement with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            updated_requirement = VisaRequirementService.update_requirement(
                id,
                **serializer.validated_data
            )
            
            return self.api_response(
                message="Visa requirement updated successfully.",
                data=VisaRequirementSerializer(updated_requirement).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error updating visa requirement {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error updating visa requirement.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VisaRequirementAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete visa requirement.
    
    Endpoint: DELETE /api/v1/rules-knowledge/admin/visa-requirements/<id>/delete/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        try:
            requirement = VisaRequirementService.get_by_id(id)
            if not requirement:
                return self.api_response(
                    message=f"Visa requirement with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            deleted = VisaRequirementService.delete_requirement(id)
            if not deleted:
                return self.api_response(
                    message="Error deleting visa requirement.",
                    data=None,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return self.api_response(
                message="Visa requirement deleted successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deleting visa requirement {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error deleting visa requirement.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
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
        
        try:
            for requirement_id in requirement_ids:
                try:
                    requirement = VisaRequirementService.get_by_id(str(requirement_id))
                    if not requirement:
                        results['failed'].append({
                            'requirement_id': str(requirement_id),
                            'error': 'Visa requirement not found'
                        })
                        continue
                    
                    if operation == 'set_mandatory':
                        VisaRequirementService.update_requirement(str(requirement_id), is_mandatory=True)
                        results['success'].append(str(requirement_id))
                    elif operation == 'set_optional':
                        VisaRequirementService.update_requirement(str(requirement_id), is_mandatory=False)
                        results['success'].append(str(requirement_id))
                    elif operation == 'delete':
                        deleted = VisaRequirementService.delete_requirement(str(requirement_id))
                        if deleted:
                            results['success'].append(str(requirement_id))
                        else:
                            results['failed'].append({
                                'requirement_id': str(requirement_id),
                                'error': 'Failed to delete'
                            })
                except Exception as e:
                    results['failed'].append({
                        'requirement_id': str(requirement_id),
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
