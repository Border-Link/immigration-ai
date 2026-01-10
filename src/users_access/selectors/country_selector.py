from users_access.models.country import Country


class CountrySelector:

    @staticmethod
    def get_all():
        """Get all countries."""
        return Country.objects.all()

    @staticmethod
    def get_active():
        """Get all active countries."""
        return Country.objects.filter(is_active=True)

    @staticmethod
    def get_by_code(code: str):
        """Get country by ISO code (active only)."""
        return Country.objects.get(code__iexact=code, is_active=True)

    @staticmethod
    def get_by_code_any(code: str):
        """Get country by ISO code (including inactive)."""
        return Country.objects.get(code__iexact=code)

    @staticmethod
    def get_jurisdictions():
        """Get all countries that are immigration jurisdictions."""
        return Country.objects.filter(is_jurisdiction=True, is_active=True)

    @staticmethod
    def get_with_states():
        """Get countries that have states/provinces with prefetched states."""
        return Country.objects.prefetch_related('states_provinces').filter(
            has_states=True,
            is_active=True
        )

    @staticmethod
    def code_exists(code: str) -> bool:
        """Check if country code exists."""
        return Country.objects.filter(code__iexact=code).exists()

    @staticmethod
    def search_by_name(name: str):
        """Search countries by name."""
        return Country.objects.filter(name__icontains=name, is_active=True)

    @staticmethod
    def get_by_id(country_id):
        """Get country by ID (UUID)."""
        return Country.objects.get(id=country_id)

    @staticmethod
    def get_none():
        """Get empty queryset."""
        return Country.objects.none()
