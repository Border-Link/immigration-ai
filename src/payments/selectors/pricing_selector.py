"""
Pricing selectors (read-only queries).
"""

from django.db.models import QuerySet
from payments.models.pricing import PricingItem, PricingItemPrice


class PricingSelector:
    @staticmethod
    def get_items(kind: str = None, is_active: bool = None) -> QuerySet:
        qs = PricingItem.objects.all().order_by("kind", "code")
        if kind:
            qs = qs.filter(kind=kind)
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        return qs

    @staticmethod
    def get_item_by_id(item_id) -> PricingItem:
        return PricingItem.objects.get(id=item_id)

    @staticmethod
    def get_item_by_code(code: str) -> PricingItem:
        return PricingItem.objects.get(code=code)

    @staticmethod
    def get_price(pricing_item: PricingItem, currency: str) -> PricingItemPrice:
        return PricingItemPrice.objects.get(pricing_item=pricing_item, currency=currency)

    @staticmethod
    def get_prices_for_item(pricing_item: PricingItem) -> QuerySet:
        return PricingItemPrice.objects.filter(pricing_item=pricing_item).order_by("currency")

