from typing import Optional
from users_access.models.state_province import StateProvince
from users_access.repositories.state_province_repository import StateProvinceRepository
from users_access.selectors.state_province_selector import StateProvinceSelector
from users_access.selectors.country_selector import CountrySelector
import logging

logger = logging.getLogger('django')


class StateProvinceService:

    @staticmethod
    def create_state_province(country_id, code: str, name: str, 
                             has_nomination_program: bool = False):
        """Create a new state/province."""
        try:
            country = CountrySelector.get_by_id(country_id)
            if not country.has_states:
                logger.error(f"Country {country.code} does not have states/provinces")
                return None

            if StateProvinceSelector.code_exists(country.code, code):
                logger.warning(f"State {code} already exists for country {country.code}")
                return None

            return StateProvinceRepository.create_state_province(
                country, code, name, has_nomination_program
            )
        except Exception as e:
            logger.error(f"Error creating state/province {code} for country ID {country_id}: {e}")
            return None

    @staticmethod
    def get_by_country(country_code: str):
        """Get all states/provinces for a country by code."""
        try:
            return StateProvinceSelector.get_by_country_code(country_code)
        except Exception as e:
            logger.error(f"Error fetching states for country {country_code}: {e}")
            return StateProvinceSelector.get_none()

    @staticmethod
    def get_by_country_id(country_id):
        """Get all states/provinces for a country by ID."""
        try:
            country = CountrySelector.get_by_id(country_id)
            return StateProvinceSelector.get_by_country_code(country.code)
        except Exception as e:
            logger.error(f"Error fetching states for country ID {country_id}: {e}")
            return StateProvinceSelector.get_none()

    @staticmethod
    def get_by_code(country_code: str, state_code: str):
        """Get specific state/province by codes."""
        try:
            return StateProvinceSelector.get_by_code(country_code, state_code)
        except Exception as e:
            logger.error(f"Error fetching state {state_code} for {country_code}: {e}")
            return None

    @staticmethod
    def get_by_id(state_id):
        """Get state/province by ID."""
        try:
            return StateProvinceSelector.get_by_id(state_id)
        except Exception as e:
            logger.error(f"Error fetching state/province by ID {state_id}: {e}")
            return None

    @staticmethod
    def get_nomination_programs(country_id: Optional[str] = None):
        """Get states/provinces with nomination programs."""
        try:
            if country_id:
                country = CountrySelector.get_by_id(country_id)
                return StateProvinceSelector.get_nomination_programs_by_country(country.code)
            return StateProvinceSelector.get_with_nomination_programs()
        except Exception as e:
            logger.error(f"Error fetching nomination programs: {e}")
            return StateProvinceSelector.get_none()

    @staticmethod
    def update_state_province(state, **fields):
        """Update state/province."""
        try:
            return StateProvinceRepository.update_state_province(state, **fields)
        except Exception as e:
            logger.error(f"Error updating state/province {state.code}: {e}")
            return None

    @staticmethod
    def set_nomination_program(state, has_nomination_program: bool):
        """Set nomination program status."""
        try:
            return StateProvinceRepository.set_nomination_program(state, has_nomination_program)
        except Exception as e:
            logger.error(f"Error setting nomination program for {state.code}: {e}")
            return None

    @staticmethod
    def delete_state_province(state):
        """Delete a state/province."""
        try:
            return StateProvinceRepository.delete_state_province(state)
        except Exception as e:
            logger.error(f"Error deleting state/province {state.code}: {e}")
            return False

    @staticmethod
    def delete_state_province_by_id(state_id):
        """Delete a state/province by ID."""
        try:
            state = StateProvinceSelector.get_by_id(state_id)
            return StateProvinceService.delete_state_province(state)
        except Exception as e:
            logger.error(f"Error deleting state/province by ID {state_id}: {e}")
            return False

    @staticmethod
    def activate_state_province_by_id(state_id: str, is_active: bool):
        """Activate or deactivate a state/province by ID."""
        try:
            state = StateProvinceSelector.get_by_id(state_id)
            if not state:
                return None
            return StateProvinceRepository.activate_state_province(state, is_active)
        except Exception as e:
            logger.error(f"Error activating/deactivating state/province {state_id}: {e}")
            return None
