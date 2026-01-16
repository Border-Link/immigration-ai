"""
Pricing repository (write operations).
"""

from django.db import transaction
from django.core.exceptions import ValidationError
from payments.models.pricing import PricingItem, PricingItemPrice


class PricingRepository:
    @staticmethod
    def create_item(**fields) -> PricingItem:
        with transaction.atomic():
            item = PricingItem.objects.create(**fields)
            item.full_clean()
            item.save()
            return item

    @staticmethod
    def update_item(item: PricingItem, **fields) -> PricingItem:
        with transaction.atomic():
            for k, v in fields.items():
                if hasattr(item, k):
                    setattr(item, k, v)
            item.full_clean()
            item.save()
            return item

    @staticmethod
    def delete_item(item: PricingItem) -> None:
        with transaction.atomic():
            item.delete()

    @staticmethod
    def upsert_price(pricing_item: PricingItem, currency: str, amount) -> PricingItemPrice:
        with transaction.atomic():
            obj, _created = PricingItemPrice.objects.update_or_create(
                pricing_item=pricing_item,
                currency=currency,
                defaults={"amount": amount},
            )
            obj.full_clean()
            obj.save()
            return obj

    @staticmethod
    def delete_price(price: PricingItemPrice) -> None:
        with transaction.atomic():
            price.delete()

