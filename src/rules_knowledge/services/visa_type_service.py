import logging
from typing import Optional
from helpers.cache_utils import cache_result
from rules_knowledge.models.visa_type import VisaType
from rules_knowledge.repositories.visa_type_repository import VisaTypeRepository
from rules_knowledge.selectors.visa_type_selector import VisaTypeSelector

logger = logging.getLogger('django')


class VisaTypeService:
    """Service for VisaType business logic."""

    @staticmethod
    def create_visa_type(jurisdiction: str, code: str, name: str, description: str = None, is_active: bool = True):
        """Create a new visa type."""
        try:
            # Check if already exists
            try:
                VisaTypeSelector.get_by_code(jurisdiction, code)
                logger.warning(f"Visa type with jurisdiction {jurisdiction} and code {code} already exists")
                return None
            except VisaType.DoesNotExist:
                pass
            
            return VisaTypeRepository.create_visa_type(jurisdiction, code, name, description, is_active)
        except Exception as e:
            logger.error(f"Error creating visa type {jurisdiction}/{code}: {e}")
            return None

    @staticmethod
    @cache_result(timeout=1800, keys=[])  # 30 minutes - rarely changes
    def get_all():
        """Get all visa types."""
        try:
            return VisaTypeSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all visa types: {e}")
            return VisaType.objects.none()

    @staticmethod
    @cache_result(timeout=1800, keys=[])  # 30 minutes - rarely changes
    def get_active():
        """Get all active visa types."""
        try:
            return VisaTypeSelector.get_active()
        except Exception as e:
            logger.error(f"Error fetching active visa types: {e}")
            return VisaType.objects.none()

    @staticmethod
    @cache_result(timeout=1800, keys=['jurisdiction'])  # 30 minutes - cache by jurisdiction
    def get_by_jurisdiction(jurisdiction: str):
        """Get visa types by jurisdiction."""
        try:
            return VisaTypeSelector.get_by_jurisdiction(jurisdiction)
        except Exception as e:
            logger.error(f"Error fetching visa types for jurisdiction {jurisdiction}: {e}")
            return VisaType.objects.none()

    @staticmethod
    @cache_result(timeout=3600, keys=['type_id'])  # 1 hour - cache by ID
    def get_by_id(type_id: str) -> Optional[VisaType]:
        """Get visa type by ID."""
        try:
            return VisaTypeSelector.get_by_id(type_id)
        except VisaType.DoesNotExist:
            logger.error(f"Visa type {type_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching visa type {type_id}: {e}")
            return None

    @staticmethod
    def update_visa_type(type_id: str, **fields) -> Optional[VisaType]:
        """Update visa type."""
        try:
            visa_type = VisaTypeSelector.get_by_id(type_id)
            return VisaTypeRepository.update_visa_type(visa_type, **fields)
        except VisaType.DoesNotExist:
            logger.error(f"Visa type {type_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating visa type {type_id}: {e}")
            return None

    @staticmethod
    def delete_visa_type(type_id: str) -> bool:
        """Delete visa type."""
        try:
            visa_type = VisaTypeSelector.get_by_id(type_id)
            VisaTypeRepository.delete_visa_type(visa_type)
            return True
        except VisaType.DoesNotExist:
            logger.error(f"Visa type {type_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting visa type {type_id}: {e}")
            return False

    @staticmethod
    def get_by_filters(jurisdiction=None, is_active=None, code=None, date_from=None, date_to=None):
        """Get visa types with advanced filtering for admin."""
        try:
            return VisaTypeSelector.get_by_filters(
                jurisdiction=jurisdiction,
                is_active=is_active,
                code=code,
                date_from=date_from,
                date_to=date_to
            )
        except Exception as e:
            logger.error(f"Error filtering visa types: {e}")
            return VisaType.objects.none()

    @staticmethod
    def activate_visa_type(visa_type, is_active: bool) -> Optional[VisaType]:
        """Activate or deactivate a visa type."""
        try:
            return VisaTypeRepository.update_visa_type(visa_type, is_active=is_active)
        except Exception as e:
            logger.error(f"Error activating/deactivating visa type: {e}")
            return None
