"""
Admin API Views for DecisionOverride Management

Admin-only endpoints for managing decision overrides.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from human_reviews.services.decision_override_service import DecisionOverrideService
from human_reviews.serializers.decision_override.read import DecisionOverrideSerializer, DecisionOverrideListSerializer
from human_reviews.serializers.decision_override.admin import (
    DecisionOverrideAdminUpdateSerializer,
    BulkDecisionOverrideOperationSerializer,
)
from django.utils.dateparse import parse_datetime

logger = logging.getLogger('django')


class DecisionOverrideAdminListAPI(AuthAPI):
    """
    Admin: Get list of all decision overrides with advanced filtering.
    
    Endpoint: GET /api/v1/human-reviews/admin/decision-overrides/
    Auth: Required (staff/superuser only)
    Query Params:
        - case_id: Filter by case ID
        - reviewer_id: Filter by reviewer ID
        - original_result_id: Filter by original eligibility result ID
        - overridden_outcome: Filter by overridden outcome (eligible, not_eligible, requires_review)
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        case_id = request.query_params.get('case_id', None)
        reviewer_id = request.query_params.get('reviewer_id', None)
        original_result_id = request.query_params.get('original_result_id', None)
        overridden_outcome = request.query_params.get('overridden_outcome', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        
        try:
            # Parse dates
            parsed_date_from = parse_datetime(date_from) if date_from and isinstance(date_from, str) else date_from
            parsed_date_to = parse_datetime(date_to) if date_to and isinstance(date_to, str) else date_to
            
            # Use service method with filters
            overrides = DecisionOverrideService.get_by_filters(
                case_id=case_id,
                reviewer_id=reviewer_id,
                original_result_id=original_result_id,
                overridden_outcome=overridden_outcome,
                date_from=parsed_date_from,
                date_to=parsed_date_to
            )
            
            return self.api_response(
                message="Decision overrides retrieved successfully.",
                data=DecisionOverrideListSerializer(overrides, many=True).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving decision overrides: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving decision overrides.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DecisionOverrideAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed decision override information.
    
    Endpoint: GET /api/v1/human-reviews/admin/decision-overrides/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        try:
            override = DecisionOverrideService.get_by_id(id)
            if not override:
                return self.api_response(
                    message=f"Decision override with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Decision override retrieved successfully.",
                data=DecisionOverrideSerializer(override).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving decision override {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving decision override.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DecisionOverrideAdminUpdateAPI(AuthAPI):
    """
    Admin: Update decision override.
    
    Endpoint: PUT /api/v1/human-reviews/admin/decision-overrides/<id>/update/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def put(self, request, id):
        serializer = DecisionOverrideAdminUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            override = DecisionOverrideService.get_by_id(id)
            if not override:
                return self.api_response(
                    message=f"Decision override with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            update_fields = {}
            if 'overridden_outcome' in serializer.validated_data:
                update_fields['overridden_outcome'] = serializer.validated_data['overridden_outcome']
            if 'reason' in serializer.validated_data:
                update_fields['reason'] = serializer.validated_data['reason']
            
            updated_override = DecisionOverrideService.update_decision_override(id, **update_fields)
            if not updated_override:
                return self.api_response(
                    message="Error updating decision override.",
                    data=None,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return self.api_response(
                message="Decision override updated successfully.",
                data=DecisionOverrideSerializer(updated_override).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error updating decision override {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error updating decision override.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DecisionOverrideAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete decision override.
    
    Endpoint: DELETE /api/v1/human-reviews/admin/decision-overrides/<id>/delete/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        try:
            override = DecisionOverrideService.get_by_id(id)
            if not override:
                return self.api_response(
                    message=f"Decision override with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            deleted = DecisionOverrideService.delete_decision_override(id)
            if not deleted:
                return self.api_response(
                    message="Error deleting decision override.",
                    data=None,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return self.api_response(
                message="Decision override deleted successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deleting decision override {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error deleting decision override.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkDecisionOverrideOperationAPI(AuthAPI):
    """
    Admin: Perform bulk operations on decision overrides.
    
    Endpoint: POST /api/v1/human-reviews/admin/decision-overrides/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request):
        serializer = BulkDecisionOverrideOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        override_ids = serializer.validated_data['decision_override_ids']
        operation = serializer.validated_data['operation']
        
        results = {
            'success': [],
            'failed': []
        }
        
        try:
            for override_id in override_ids:
                try:
                    if operation == 'delete':
                        deleted = DecisionOverrideService.delete_decision_override(str(override_id))
                        if deleted:
                            results['success'].append(str(override_id))
                        else:
                            results['failed'].append({
                                'override_id': str(override_id),
                                'error': 'Decision override not found or failed to delete'
                            })
                except Exception as e:
                    results['failed'].append({
                        'override_id': str(override_id),
                        'error': str(e)
                    })
            
            return self.api_response(
                message=f"Bulk operation '{operation}' completed. {len(results['success'])} succeeded, {len(results['failed'])} failed.",
                data=results,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error performing bulk operation on decision overrides: {e}", exc_info=True)
            return self.api_response(
                message="Error performing bulk operation.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
