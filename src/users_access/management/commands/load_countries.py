"""
Management command to load countries and states/provinces from JSON file.

Usage:
    python manage.py load_countries
    python manage.py load_countries --update  # Update existing countries
    python manage.py load_countries --clear  # Clear all before loading
"""
import json
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from users_access.services.country_service import CountryService
from users_access.services.state_province_service import StateProvinceService
from users_access.selectors.country_selector import CountrySelector
from users_access.selectors.state_province_selector import StateProvinceSelector
from .state_code_mappings import get_state_code_from_name


class Command(BaseCommand):
    help = 'Load countries and states/provinces from JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing countries instead of skipping them'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing countries and states before loading'
        )

    def handle(self, *args, **options):
        update = options.get('update', False)
        clear = options.get('clear', False)

        # Default to data/countries.json in the commands directory
        commands_dir = os.path.dirname(__file__)
        file_path = os.path.join(commands_dir, 'data', 'countries.json')

        if not os.path.exists(file_path):
            raise CommandError(f'JSON file not found: {file_path}')

        # Clear existing data if requested
        if clear:
            self.stdout.write(self.style.WARNING('Clearing all existing countries and states...'))
            # Use selectors to get querysets, then delete
            all_states = StateProvinceSelector.get_all()
            all_countries = CountrySelector.get_all()
            all_states.delete()
            all_countries.delete()
            self.stdout.write(self.style.SUCCESS('Cleared all countries and states.'))

        # Load and parse JSON
        self.stdout.write(f'Loading countries from: {file_path}')
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise CommandError(f'Invalid JSON file: {e}')
        except Exception as e:
            raise CommandError(f'Error reading file: {e}')

        # Handle both formats: array directly or wrapped in "countries" key
        if isinstance(data, list):
            countries_data = data
        elif 'countries' in data:
            countries_data = data['countries']
        else:
            raise CommandError('JSON file must contain a "countries" array or be an array directly')
        self.stdout.write(f'Found {len(countries_data)} countries to process')

        # Process countries
        created_countries = 0
        updated_countries = 0
        skipped_countries = 0
        created_states = 0
        updated_states = 0
        skipped_states = 0
        errors = []

        with transaction.atomic():
            for country_data in countries_data:
                try:
                    # Handle both formats: 'code' or 'countryCode'

                    code = (country_data.get('code') or country_data.get('countryCode') or '').strip().upper()
                    name = country_data.get('name', '').strip()
                    # Handle both formats: 'has_states' or infer from stateProvinces
                    states_data = country_data.get('states_provinces') or country_data.get('stateProvinces') or []
                    has_states = country_data.get('has_states', len(states_data) > 0)
                    # Default is_jurisdiction based on common immigration countries
                    is_jurisdiction = country_data.get('is_jurisdiction', False)
                    # Set as jurisdiction if it's a common immigration destination
                    common_jurisdictions = ['CA', 'AU', 'US', 'GB', 'NZ', 'IE', 'DE', 'FR', 'ES', 'IT', 'PT', 'NL', 'BE', 'CH', 'AT', 'SE', 'NO', 'DK', 'FI']
                    if code in common_jurisdictions:
                        is_jurisdiction = True

                    if not code or not name:
                        errors.append(f'Skipping country with missing code or name: {country_data}')
                        continue

                    # Check if country exists (including inactive)
                    existing_country = None
                    if CountrySelector.code_exists(code):
                        try:
                            existing_country = CountrySelector.get_by_code_any(code)
                        except Exception:
                            pass

                    if existing_country:
                        if update:
                            # Update existing country
                            CountryService.update_country(
                                existing_country,
                                name=name,
                                has_states=has_states,
                                is_jurisdiction=is_jurisdiction
                            )
                            updated_countries += 1
                            self.stdout.write(
                                self.style.SUCCESS(f'  Updated: {name} ({code})')
                            )
                            country = existing_country
                        else:
                            skipped_countries += 1
                            self.stdout.write(
                                self.style.WARNING(f'  Skipped (exists): {name} ({code})')
                            )
                            country = existing_country
                    else:
                        # Create new country
                        country = CountryService.create_country(
                            code=code,
                            name=name,
                            has_states=has_states,
                            is_jurisdiction=is_jurisdiction
                        )
                        if country:
                            created_countries += 1
                            self.stdout.write(
                                self.style.SUCCESS(f'  Created: {name} ({code})')
                            )
                        else:
                            errors.append(f'Failed to create country: {name} ({code})')
                            continue

                    # Process states/provinces
                    if country and has_states and states_data:
                        for idx, state_data in enumerate(states_data):
                            try:
                                # Handle both formats: 'code' or generate from name/index
                                state_code = state_data.get('code', '').strip().upper()
                                state_name = state_data.get('name', '').strip()
                                
                                # If no code provided, generate one from name
                                if not state_code and state_name:
                                    state_code = get_state_code_from_name(code, state_name)
                                
                                # Default has_nomination_program based on country
                                has_nomination = state_data.get('has_nomination_program', False)
                                # Canada and Australia states typically have nomination programs
                                if code in ['CA', 'AU'] and not has_nomination:
                                    # Some exceptions
                                    if code == 'CA' and state_code in ['QC', 'NT', 'NU']:
                                        has_nomination = False
                                    elif code == 'CA':
                                        has_nomination = True
                                    elif code == 'AU':
                                        has_nomination = True

                                if not state_code or not state_name:
                                    errors.append(
                                        f'  Skipping state with missing code or name in {name}: {state_data}'
                                    )
                                    continue

                                # Check if state exists (including inactive)
                                existing_state = None
                                if StateProvinceSelector.code_exists(code, state_code):
                                    try:
                                        existing_state = StateProvinceSelector.get_by_code_any(code, state_code)
                                    except Exception:
                                        pass

                                if existing_state:
                                    if update:
                                        StateProvinceService.update_state_province(
                                            existing_state,
                                            name=state_name,
                                            has_nomination_program=has_nomination
                                        )
                                        updated_states += 1
                                        self.stdout.write(
                                            self.style.SUCCESS(f'    Updated state: {state_name} ({state_code})')
                                        )
                                    else:
                                        skipped_states += 1
                                else:
                                    state = StateProvinceService.create_state_province(
                                        country_code=code,
                                        code=state_code,
                                        name=state_name,
                                        has_nomination_program=has_nomination
                                    )
                                    if state:
                                        created_states += 1
                                        self.stdout.write(
                                            self.style.SUCCESS(f'    Created state: {state_name} ({state_code})')
                                        )
                                    else:
                                        errors.append(
                                            f'    Failed to create state: {state_name} ({state_code}) in {name}'
                                        )
                            except Exception as e:
                                errors.append(
                                    f'    Error processing state {state_data.get("code", "unknown")} in {name}: {e}'
                                )

                except Exception as e:
                    errors.append(f'Error processing country {country_data.get("code", "unknown")}: {e}')

        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('SUMMARY'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'Countries - Created: {created_countries}, Updated: {updated_countries}, Skipped: {skipped_countries}')
        self.stdout.write(f'States/Provinces - Created: {created_states}, Updated: {updated_states}, Skipped: {skipped_states}')

        if errors:
            self.stdout.write('\n' + self.style.ERROR('ERRORS:'))
            for error in errors:
                self.stdout.write(self.style.ERROR(f'  - {error}'))
        else:
            self.stdout.write(self.style.SUCCESS('\nAll countries and states loaded successfully!'))

