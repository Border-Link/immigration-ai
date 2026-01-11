from django.db import transaction
from main_system.repositories.base import BaseRepositoryMixin
from users_access.models.country import Country


class CountryRepository:

    @staticmethod
    def create_country(code: str, name: str, has_states: bool = False, 
                      is_jurisdiction: bool = False, is_active: bool = True):
        """Create a new country."""
        with transaction.atomic():
            country = Country.objects.create(
                code=code,
                name=name,
                has_states=has_states,
                is_jurisdiction=is_jurisdiction,
                is_active=is_active
            )
            country.full_clean()
            country.save()
            return country

    @staticmethod
    def update_country(country, **fields):
        """Update country fields."""
        return BaseRepositoryMixin.update_model_fields(
            country,
            **fields,
            cache_keys=[f'country:{country.id}', f'country:code:{country.code}']
        )

    @staticmethod
    def set_jurisdiction(country, is_jurisdiction: bool):
        """Mark country as jurisdiction or not."""
        with transaction.atomic():
            country.is_jurisdiction = is_jurisdiction
            country.full_clean()
            country.save()
            return country

    @staticmethod
    def activate_country(country, is_active: bool):
        """Activate or deactivate country."""
        with transaction.atomic():
            country.is_active = is_active
            country.full_clean()
            country.save()
            return country

    @staticmethod
    def delete_country(country):
        """Delete a country and all its states/provinces."""
        with transaction.atomic():
            # Delete all states/provinces first (cascade delete)
            # Use model directly to get all states regardless of active status
            from users_access.models.state_province import StateProvince
            StateProvince.objects.filter(country=country).delete()
            # Then delete the country
            country.delete()
            return True

