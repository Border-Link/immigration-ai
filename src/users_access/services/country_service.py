from main_system.utils.cache_utils import cache_result, invalidate_cache
from users_access.models.country import Country
from users_access.repositories.country_repository import CountryRepository
from users_access.selectors.country_selector import CountrySelector
import logging

logger = logging.getLogger('django')

def namespace(*args, **kwargs) -> str:
    """
    Single namespace for all Country-related cached reads.
    Any write operation must bump this namespace to avoid stale reads.
    """
    return "countries"


class CountryService:

    @staticmethod
    @invalidate_cache(namespace, predicate=lambda country: country is not None)
    def create_country(code: str, name: str, has_states: bool = False, 
                       is_jurisdiction: bool = False):
        """Create a new country."""
        try:
            if CountrySelector.code_exists(code):
                logger.warning(f"Country with code {code} already exists")
                return None
            return CountryRepository.create_country(code, name, has_states, is_jurisdiction)
        except Exception as e:
            logger.error(f"Error creating country {code}: {e}")
            return None

    @staticmethod
    @cache_result(timeout=3600, keys=[], namespace=namespace)  # 1 hour - countries rarely change
    def get_all():
        """Get all active countries."""
        try:
            return CountrySelector.get_active()
        except Exception as e:
            logger.error(f"Error fetching countries: {e}")
            return CountrySelector.get_none()

    @staticmethod
    @cache_result(timeout=3600, keys=['code'], namespace=namespace)  # 1 hour - cache country by code
    def get_by_code(code: str):
        """Get country by code."""
        try:
            return CountrySelector.get_by_code(code)
        except Exception as e:
            logger.error(f"Error fetching country {code}: {e}")
            return None

    @staticmethod
    @cache_result(timeout=3600, keys=['country_id'], namespace=namespace)  # 1 hour - cache country by ID
    def get_by_id(country_id):
        """Get country by ID."""
        try:
            return CountrySelector.get_by_id(country_id)
        except Exception as e:
            logger.error(f"Error fetching country by ID {country_id}: {e}")
            return None

    @staticmethod
    @cache_result(timeout=3600, keys=[], namespace=namespace)  # 1 hour - jurisdictions rarely change
    def get_jurisdictions():
        """Get all immigration jurisdictions."""
        try:
            return CountrySelector.get_jurisdictions()
        except Exception as e:
            logger.error(f"Error fetching jurisdictions: {e}")
            return CountrySelector.get_none()

    @staticmethod
    @cache_result(timeout=3600, keys=[], namespace=namespace)  # 1 hour - countries with states rarely change
    def get_with_states():
        """Get countries with states/provinces."""
        try:
            return CountrySelector.get_with_states()
        except Exception as e:
            logger.error(f"Error fetching countries with states: {e}")
            return CountrySelector.get_none()

    @staticmethod
    @cache_result(timeout=1800, keys=['name'], namespace=namespace)  # 30 minutes - cache search results
    def search_by_name(name: str):
        """Search countries by name."""
        try:
            return CountrySelector.search_by_name(name)
        except Exception as e:
            logger.error(f"Error searching countries by name {name}: {e}")
            return CountrySelector.get_none()

    @staticmethod
    @invalidate_cache(namespace, predicate=lambda country: country is not None)
    def update_country(country, **fields):
        """Update country."""
        try:
            return CountryRepository.update_country(country, **fields)
        except Exception as e:
            logger.error(f"Error updating country {country.code}: {e}")
            return None

    @staticmethod
    @invalidate_cache(namespace, predicate=lambda country: country is not None)
    def set_jurisdiction(country, is_jurisdiction: bool):
        """Mark country as jurisdiction."""
        try:
            return CountryRepository.set_jurisdiction(country, is_jurisdiction)
        except Exception as e:
            logger.error(f"Error setting jurisdiction for {country.code}: {e}")
            return None

    @staticmethod
    @invalidate_cache(namespace, predicate=bool)
    def delete_country(country):
        """Delete a country."""
        try:
            return CountryRepository.delete_country(country)
        except Exception as e:
            logger.error(f"Error deleting country {country.code}: {e}")
            return False

    @staticmethod
    def delete_country_by_id(country_id):
        """Delete a country by ID."""
        try:
            country = CountrySelector.get_by_id(country_id)
            return CountryService.delete_country(country)
        except Exception as e:
            logger.error(f"Error deleting country by ID {country_id}: {e}")
            return False

    @staticmethod
    @invalidate_cache(namespace, predicate=lambda country: country is not None)
    def activate_country_by_id(country_id: str, is_active: bool):
        """Activate or deactivate a country by ID."""
        try:
            country = CountrySelector.get_by_id(country_id)
            if not country:
                return None
            return CountryRepository.activate_country(country, is_active)
        except Exception as e:
            logger.error(f"Error activating/deactivating country {country_id}: {e}")
            return None

    @staticmethod
    @invalidate_cache(namespace, predicate=lambda country: country is not None)
    def set_jurisdiction_by_id(country_id: str, is_jurisdiction: bool):
        """Set jurisdiction status for a country by ID."""
        try:
            country = CountrySelector.get_by_id(country_id)
            if not country:
                return None
            return CountryRepository.set_jurisdiction(country, is_jurisdiction)
        except Exception as e:
            logger.error(f"Error setting jurisdiction for country {country_id}: {e}")
            return None
