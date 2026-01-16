from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.ai_reasoning_permission import AIReasoningPermission
from ai_decisions.permissions.eligibility_result_permissions import CanModifyEligibilityResult
from ai_decisions.services.eligibility_result_service import EligibilityResultService
from ai_decisions.serializers.eligibility_result.read import EligibilityResultSerializer
from ai_decisions.serializers.eligibility_result.update_delete import EligibilityResultUpdateSerializer


class EligibilityResultUpdateAPI(AuthAPI):
    """
    Update an eligibility result.
    
    Security: Users can only update results for cases they own (unless admin/reviewer).
    """
    permission_classes = [AIReasoningPermission, CanModifyEligibilityResult]

    def patch(self, request, id):
        result = EligibilityResultService.get_by_id(id)
        if not result:
            return self.api_response(
                message=f"Eligibility result with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Enforce object-level access (case ownership/admin write).
        self.check_object_permissions(request, result)

        serializer = EligibilityResultUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_result = EligibilityResultService.update_eligibility_result(id, **serializer.validated_data)
        if not updated_result:
            return self.api_response(
                message=f"Error updating eligibility result with ID '{id}'.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        return self.api_response(
            message="Eligibility result updated successfully.",
            data=EligibilityResultSerializer(updated_result).data,
            status_code=status.HTTP_200_OK
        )


class EligibilityResultDeleteAPI(AuthAPI):
    """
    Delete an eligibility result.
    
    Security: Users can only delete results for cases they own (unless admin/reviewer).
    """
    permission_classes = [AIReasoningPermission, CanModifyEligibilityResult]

    def delete(self, request, id):
        result = EligibilityResultService.get_by_id(id)
        if not result:
            return self.api_response(
                message=f"Eligibility result with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Enforce object-level access (case ownership/admin write).
        self.check_object_permissions(request, result)

        success = EligibilityResultService.delete_eligibility_result(id)
        if not success:
            return self.api_response(
                message=f"Error deleting eligibility result with ID '{id}'.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        return self.api_response(
            message="Eligibility result deleted successfully.",
            data=None,
            status_code=status.HTTP_200_OK
        )

