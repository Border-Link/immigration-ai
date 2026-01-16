"""
Plan pricing helpers.

Pricing is ADMIN-CONFIGURED (API-driven) via PricingItem + PricingItemPrice.
There are NO hardcoded fallbacks.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional
from payments.selectors.pricing_selector import PricingSelector


class PlanPricing:
    """Centralized pricing for one-off per-case plans and add-ons."""

    @staticmethod
    def get_case_fee_amount(plan: str, currency: str) -> Optional[Decimal]:
        """
        Resolve plan price from DB (active PricingItem kind=plan, code=<plan>, currency=<currency>).

        Returns None if price is not configured.
        """
        try:
            item = PricingSelector.get_items(kind="plan", is_active=True).filter(code=plan).first()
            if item:
                price = PricingSelector.get_prices_for_item(item).filter(currency=currency).first()
                if price:
                    return Decimal(str(price.amount))
        except Exception:
            # Defensive: never break checkout because pricing tables are misconfigured.
            pass

        return None

    @staticmethod
    def get_reviewer_addon_amount(currency: str) -> Optional[Decimal]:
        """
        Resolve reviewer add-on price from DB (active PricingItem kind=addon, code=reviewer_addon, currency=<currency>).

        Returns None if price is not configured.
        """
        try:
            item = PricingSelector.get_items(kind="addon", is_active=True).filter(code="reviewer_addon").first()
            if item:
                price = PricingSelector.get_prices_for_item(item).filter(currency=currency).first()
                if price:
                    return Decimal(str(price.amount))
        except Exception:
            pass

        return None

    @staticmethod
    def get_ai_calls_addon_amount(currency: str) -> Optional[Decimal]:
        """
        Resolve AI calls add-on price from DB (active PricingItem kind=addon, code=ai_calls_addon, currency=<currency>).

        Returns None if price is not configured.
        """
        try:
            item = PricingSelector.get_items(kind="addon", is_active=True).filter(code="ai_calls_addon").first()
            if item:
                price = PricingSelector.get_prices_for_item(item).filter(currency=currency).first()
                if price:
                    return Decimal(str(price.amount))
        except Exception:
            pass

        return None
