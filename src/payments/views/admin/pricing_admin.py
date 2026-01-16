from rest_framework import status

from main_system.base.auth_api import AuthAPI
from main_system.permissions.admin_permission import AdminPermission
from payments.serializers.pricing.item import (
    PricingItemSerializer,
    PricingItemCreateSerializer,
    PricingItemUpdateSerializer,
)
from payments.serializers.pricing.price import PricingItemPriceSerializer, PricingItemPriceUpsertSerializer
from payments.services.pricing_service import PricingService


class PricingItemAdminListCreateAPI(AuthAPI):
    """
    Admin: list/create pricing items (plans + add-ons).

    Endpoints:
      - GET  /api/v1/payments/admin/pricing/items/
      - POST /api/v1/payments/admin/pricing/items/
    """

    permission_classes = [AdminPermission]

    def get(self, request):
        kind = request.query_params.get("kind")
        is_active = request.query_params.get("is_active")
        is_active_bool = None
        if is_active is not None:
            is_active_bool = str(is_active).lower() in ("1", "true", "yes")

        qs = PricingService.list_items(kind=kind, is_active=is_active_bool)
        return self.api_response(
            message="Pricing items retrieved successfully.",
            data=PricingItemSerializer(qs, many=True).data,
            status_code=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = PricingItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = PricingService.create_item(**serializer.validated_data)
        if not item:
            return self.api_response(
                message="Error creating pricing item.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        return self.api_response(
            message="Pricing item created successfully.",
            data=PricingItemSerializer(item).data,
            status_code=status.HTTP_201_CREATED,
        )


class PricingItemAdminDetailAPI(AuthAPI):
    """
    Admin: get pricing item detail.

    Endpoint: GET /api/v1/payments/admin/pricing/items/<id>/
    """

    permission_classes = [AdminPermission]

    def get(self, request, id):
        item = PricingService.get_item(str(id))
        if not item:
            return self.api_response(
                message="Pricing item not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return self.api_response(
            message="Pricing item retrieved successfully.",
            data=PricingItemSerializer(item).data,
            status_code=status.HTTP_200_OK,
        )


class PricingItemAdminUpdateAPI(AuthAPI):
    """
    Admin: update pricing item.

    Endpoint: PATCH /api/v1/payments/admin/pricing/items/<id>/
    """

    permission_classes = [AdminPermission]

    def patch(self, request, id):
        serializer = PricingItemUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = PricingService.update_item(str(id), **serializer.validated_data)
        if not updated:
            return self.api_response(
                message="Pricing item not found or update failed.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        return self.api_response(
            message="Pricing item updated successfully.",
            data=PricingItemSerializer(updated).data,
            status_code=status.HTTP_200_OK,
        )


class PricingItemAdminDeleteAPI(AuthAPI):
    """
    Admin: delete pricing item.

    Endpoint: DELETE /api/v1/payments/admin/pricing/items/<id>/
    """

    permission_classes = [AdminPermission]

    def delete(self, request, id):
        ok = PricingService.delete_item(str(id))
        if not ok:
            return self.api_response(
                message="Pricing item not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return self.api_response(
            message="Pricing item deleted successfully.",
            data=None,
            status_code=status.HTTP_200_OK,
        )


class PricingItemPriceAdminListUpsertAPI(AuthAPI):
    """
    Admin: list/upsert currency prices for a pricing item.

    Endpoints:
      - GET  /api/v1/payments/admin/pricing/items/<id>/prices/
      - POST /api/v1/payments/admin/pricing/items/<id>/prices/
    """

    permission_classes = [AdminPermission]

    def get(self, request, id):
        prices = PricingService.list_prices(item_id=str(id))
        if prices is None:
            return self.api_response(
                message="Pricing item not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return self.api_response(
            message="Pricing item prices retrieved successfully.",
            data=PricingItemPriceSerializer(prices, many=True).data,
            status_code=status.HTTP_200_OK,
        )

    def post(self, request, id):
        serializer = PricingItemPriceUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        price = PricingService.upsert_price(
            item_id=str(id),
            currency=serializer.validated_data["currency"],
            amount=serializer.validated_data["amount"],
        )
        if not price:
            return self.api_response(
                message="Pricing item not found or price upsert failed.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        return self.api_response(
            message="Pricing item price upserted successfully.",
            data=PricingItemPriceSerializer(price).data,
            status_code=status.HTTP_200_OK,
        )


class PricingItemPriceAdminDeleteAPI(AuthAPI):
    """
    Admin: delete a specific currency price for a pricing item.

    Endpoint: DELETE /api/v1/payments/admin/pricing/items/<id>/prices/<currency>/
    """

    permission_classes = [AdminPermission]

    def delete(self, request, id, currency):
        ok = PricingService.delete_price(item_id=str(id), currency=str(currency))
        if not ok:
            return self.api_response(
                message="Pricing item or price not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return self.api_response(
            message="Pricing item price deleted successfully.",
            data=None,
            status_code=status.HTTP_200_OK,
        )

