import logging
from typing import Optional

from django.core.exceptions import ObjectDoesNotExist

from payments.models.pricing import PricingItem, PricingItemPrice
from payments.repositories.pricing_repository import PricingRepository
from payments.selectors.pricing_selector import PricingSelector

logger = logging.getLogger("django")


class PricingService:
    """Business logic for pricing configuration (admin-managed)."""

    @staticmethod
    def list_items(kind: str = None, is_active: bool = None):
        return PricingSelector.get_items(kind=kind, is_active=is_active)

    @staticmethod
    def get_item(item_id: str) -> Optional[PricingItem]:
        try:
            return PricingSelector.get_item_by_id(item_id)
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def create_item(**fields) -> Optional[PricingItem]:
        try:
            return PricingRepository.create_item(**fields)
        except Exception as e:
            logger.error(f"Error creating pricing item: {e}", exc_info=True)
            return None

    @staticmethod
    def update_item(item_id: str, **fields) -> Optional[PricingItem]:
        try:
            item = PricingSelector.get_item_by_id(item_id)
            return PricingRepository.update_item(item, **fields)
        except ObjectDoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error updating pricing item {item_id}: {e}", exc_info=True)
            return None

    @staticmethod
    def delete_item(item_id: str) -> bool:
        try:
            item = PricingSelector.get_item_by_id(item_id)
            PricingRepository.delete_item(item)
            return True
        except ObjectDoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Error deleting pricing item {item_id}: {e}", exc_info=True)
            return False

    @staticmethod
    def upsert_price(item_id: str, currency: str, amount) -> Optional[PricingItemPrice]:
        try:
            item = PricingSelector.get_item_by_id(item_id)
            return PricingRepository.upsert_price(item, currency=currency, amount=amount)
        except ObjectDoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error upserting price for item {item_id}: {e}", exc_info=True)
            return None

    @staticmethod
    def delete_price(item_id: str, currency: str) -> bool:
        try:
            item = PricingSelector.get_item_by_id(item_id)
            price = PricingSelector.get_price(item, currency=currency)
            PricingRepository.delete_price(price)
            return True
        except ObjectDoesNotExist:
            return False

    @staticmethod
    def list_prices(item_id: str):
        try:
            item = PricingSelector.get_item_by_id(item_id)
            return PricingSelector.get_prices_for_item(item)
        except ObjectDoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error deleting price for item {item_id} currency {currency}: {e}", exc_info=True)
            return False

