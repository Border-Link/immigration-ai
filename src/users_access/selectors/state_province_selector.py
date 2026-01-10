from users_access.models.state_province import StateProvince


class StateProvinceSelector:

    @staticmethod
    def get_all():
        """Get all states/provinces with country."""
        return StateProvince.objects.select_related('country').all()

    @staticmethod
    def get_active():
        """Get all active states/provinces with country."""
        return StateProvince.objects.select_related('country').filter(is_active=True)

    @staticmethod
    def get_by_country(country):
        """Get all states/provinces for a country."""
        return StateProvince.objects.select_related('country').filter(
            country=country,
            is_active=True
        )

    @staticmethod
    def get_by_country_code(country_code: str):
        """Get states/provinces by country code."""
        return StateProvince.objects.select_related('country').filter(
            country__code__iexact=country_code,
            country__is_active=True,
            is_active=True
        )

    @staticmethod
    def get_by_code(country_code: str, state_code: str):
        """Get specific state/province by country and state codes (active only)."""
        return StateProvince.objects.select_related('country').get(
            country__code__iexact=country_code,
            code__iexact=state_code,
            is_active=True
        )

    @staticmethod
    def get_by_code_any(country_code: str, state_code: str):
        """Get specific state/province by country and state codes (including inactive)."""
        return StateProvince.objects.select_related('country').get(
            country__code__iexact=country_code,
            code__iexact=state_code
        )

    @staticmethod
    def get_with_nomination_programs():
        """Get states/provinces with nomination programs."""
        return StateProvince.objects.select_related('country').filter(
            has_nomination_program=True,
            is_active=True
        )

    @staticmethod
    def get_nomination_programs_by_country(country_code: str):
        """Get nomination programs for a specific country."""
        return StateProvince.objects.select_related('country').filter(
            country__code__iexact=country_code,
            has_nomination_program=True,
            is_active=True
        )

    @staticmethod
    def code_exists(country_code: str, state_code: str) -> bool:
        """Check if state/province code exists for country."""
        return StateProvince.objects.filter(
            country__code__iexact=country_code,
            code__iexact=state_code
        ).exists()

    @staticmethod
    def get_by_id(state_id):
        """Get state/province by ID (UUID)."""
        return StateProvince.objects.select_related('country').get(id=state_id)

    @staticmethod
    def get_none():
        """Get empty queryset."""
        return StateProvince.objects.none()
