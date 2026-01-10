"""
Admin API Views for ParsedRule Management

Admin-only endpoints for managing parsed rules.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from data_ingestion.services.parsed_rule_service import ParsedRuleService
from data_ingestion.serializers.parsed_rule.read import ParsedRuleSerializer, ParsedRuleListSerializer
from data_ingestion.serializers.parsed_rule.admin import (
    ParsedRuleAdminUpdateSerializer,
    BulkParsedRuleOperationSerializer,
)
from django.utils.dateparse import parse_datetime

logger = logging.getLogger('django')


class ParsedRuleAdminListAPI(AuthAPI):
    """
    Admin: Get list of all parsed rules with advanced filtering.
    
    Endpoint: GET /api/v1/data-ingestion/admin/parsed-rules/
    Auth: Required (staff/superuser only)
    Query Params:
        - status: Filter by status
        - visa_code: Filter by visa code
        - rule_type: Filter by rule type
        - min_confidence: Filter by minimum confidence
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        status_filter = request.query_params.get('status', None)
        visa_code = request.query_params.get('visa_code', None)
        rule_type = request.query_params.get('rule_type', None)
        min_confidence = request.query_params.get('min_confidence', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        
        try:
            # Parse parameters
            min_confidence_float = float(min_confidence) if min_confidence else None
            parsed_date_from = parse_datetime(date_from) if date_from and isinstance(date_from, str) else date_from
            parsed_date_to = parse_datetime(date_to) if date_to and isinstance(date_to, str) else date_to
            
            # Use service method with filters
            rules = ParsedRuleService.get_by_filters(
                status=status_filter,
                visa_code=visa_code,
                rule_type=rule_type,
                min_confidence=min_confidence_float,
                date_from=parsed_date_from,
                date_to=parsed_date_to
            )
            
            return self.api_response(
                message="Parsed rules retrieved successfully.",
                data=ParsedRuleListSerializer(rules, many=True).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving parsed rules: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving parsed rules.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ParsedRuleAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed parsed rule information.
    
    Endpoint: GET /api/v1/data-ingestion/admin/parsed-rules/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        try:
            rule = ParsedRuleService.get_by_id(id)
            if not rule:
                return self.api_response(
                    message=f"Parsed rule with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Parsed rule retrieved successfully.",
                data=ParsedRuleSerializer(rule).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving parsed rule {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving parsed rule.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ParsedRuleAdminUpdateAPI(AuthAPI):
    """
    Admin: Update parsed rule.
    
    Endpoint: PATCH /api/v1/data-ingestion/admin/parsed-rules/<id>/update/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def patch(self, request, id):
        serializer = ParsedRuleAdminUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            rule = ParsedRuleService.get_by_id(id)
            if not rule:
                return self.api_response(
                    message=f"Parsed rule with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            updated_rule = ParsedRuleService.update_parsed_rule(
                id,
                **serializer.validated_data
            )
            
            if updated_rule:
                return self.api_response(
                    message="Parsed rule updated successfully.",
                    data=ParsedRuleSerializer(updated_rule).data,
                    status_code=status.HTTP_200_OK
                )
            else:
                return self.api_response(
                    message="Error updating parsed rule.",
                    data=None,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            logger.error(f"Error updating parsed rule {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error updating parsed rule.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ParsedRuleAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete parsed rule.
    
    Endpoint: DELETE /api/v1/data-ingestion/admin/parsed-rules/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        try:
            rule = ParsedRuleService.get_by_id(id)
            if not rule:
                return self.api_response(
                    message=f"Parsed rule with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            deleted = ParsedRuleService.delete_parsed_rule(id)
            if not deleted:
                return self.api_response(
                    message="Error deleting parsed rule.",
                    data=None,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return self.api_response(
                message="Parsed rule deleted successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deleting parsed rule {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error deleting parsed rule.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkParsedRuleOperationAPI(AuthAPI):
    """
    Admin: Perform bulk operations on parsed rules.
    
    Endpoint: POST /api/v1/data-ingestion/admin/parsed-rules/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request):
        serializer = BulkParsedRuleOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        rule_ids = serializer.validated_data['rule_ids']
        operation = serializer.validated_data['operation']
        
        results = {
            'success': [],
            'failed': []
        }
        
        try:
            for rule_id in rule_ids:
                try:
                    rule = ParsedRuleService.get_by_id(str(rule_id))
                    if not rule:
                        results['failed'].append({
                            'rule_id': str(rule_id),
                            'error': 'Parsed rule not found'
                        })
                        continue
                    
                    if operation == 'delete':
                        deleted = ParsedRuleService.delete_parsed_rule(str(rule_id))
                        if deleted:
                            results['success'].append(str(rule_id))
                        else:
                            results['failed'].append({
                                'rule_id': str(rule_id),
                                'error': 'Failed to delete'
                            })
                    elif operation == 'approve':
                        updated = ParsedRuleService.update_status(str(rule_id), 'approved')
                        if updated:
                            results['success'].append(str(rule_id))
                        else:
                            results['failed'].append({
                                'rule_id': str(rule_id),
                                'error': 'Failed to approve'
                            })
                    elif operation == 'reject':
                        updated = ParsedRuleService.update_status(str(rule_id), 'rejected')
                        if updated:
                            results['success'].append(str(rule_id))
                        else:
                            results['failed'].append({
                                'rule_id': str(rule_id),
                                'error': 'Failed to reject'
                            })
                    elif operation == 'mark_pending':
                        updated = ParsedRuleService.update_status(str(rule_id), 'pending')
                        if updated:
                            results['success'].append(str(rule_id))
                        else:
                            results['failed'].append({
                                'rule_id': str(rule_id),
                                'error': 'Failed to mark pending'
                            })
                except Exception as e:
                    results['failed'].append({
                        'rule_id': str(rule_id),
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
