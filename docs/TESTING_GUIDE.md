# Testing Guide

This guide explains how to run tests for the `users_access` module and the entire project.

## Prerequisites

1. **Install dependencies** (if not already installed):
   ```bash
   pip install -r requirements.txt
   ```

2. **Install pytest-django** (required for Django tests with pytest):
   ```bash
   pip install pytest-django
   ```

3. **Set up test database** (Django will create this automatically, but ensure your database settings are configured)

## Running Tests

### Option 1: Using pytest (Recommended)

#### Run all tests in `users_access`:
```bash
cd src
pytest users_access/tests/ -v
```

#### Run all tests with coverage:
```bash
cd src
pytest users_access/tests/ --cov=users_access --cov-report=html --cov-report=term
```

#### Run specific test file:
```bash
cd src
pytest users_access/tests/services/test_user_service.py -v
pytest users_access/tests/views/test_user_views.py -v
```

#### Run specific test class:
```bash
cd src
pytest users_access/tests/services/test_user_service.py::TestUserService -v
```

#### Run specific test method:
```bash
cd src
pytest users_access/tests/services/test_user_service.py::TestUserService::test_create_user -v
```

#### Run tests by pattern:
```bash
cd src
pytest users_access/tests/ -k "test_create" -v  # Runs all tests with "create" in the name
```

#### Run only service tests:
```bash
cd src
pytest users_access/tests/services/ -v
```

#### Run only view tests:
```bash
cd src
pytest users_access/tests/views/ -v
```

### Option 2: Using Django's Test Runner

#### Run all tests:
```bash
cd src
python manage.py test users_access.tests
```

#### Run specific test file:
```bash
cd src
python manage.py test users_access.tests.services.test_user_service
python manage.py test users_access.tests.views.test_user_views
```

#### Run specific test class:
```bash
cd src
python manage.py test users_access.tests.services.test_user_service.TestUserService
```

#### Run with verbosity:
```bash
cd src
python manage.py test users_access.tests --verbosity=2
```

### Option 3: Using Makefile

The Makefile includes a test command:
```bash
make test
```

## Test Structure

```
users_access/tests/
├── conftest.py              # Shared pytest fixtures
├── services/               # Service layer tests
│   ├── test_user_service.py
│   ├── test_user_profile_service.py
│   ├── test_otp_service.py
│   ├── test_country_service.py
│   ├── test_state_province_service.py
│   ├── test_user_settings_service.py
│   ├── test_notification_service.py
│   ├── test_password_reset_service.py
│   └── test_user_device_session_service.py
└── views/                   # View/API layer tests
    ├── test_user_views.py
    ├── test_user_profile_views.py
    ├── test_user_settings_views.py
    ├── test_forgot_password_views.py
    ├── test_admin_user_views.py
    └── ... (other view tests)
```

## Environment Variables

Ensure your test environment is configured. You may need to set:

```bash
export DJANGO_SETTINGS_MODULE=main_system.settings
```

Or create a `.env` file with test database settings.

## Common Test Commands

### Run tests with detailed output:
```bash
cd src
pytest users_access/tests/ -v -s
```

### Run tests and stop on first failure:
```bash
cd src
pytest users_access/tests/ -x
```

### Run tests in parallel (if pytest-xdist is installed):
```bash
cd src
pytest users_access/tests/ -n auto
```

### Run tests with coverage report:
```bash
cd src
pytest users_access/tests/ --cov=users_access --cov-report=term-missing
```

### Generate HTML coverage report:
```bash
cd src
pytest users_access/tests/ --cov=users_access --cov-report=html
# Then open htmlcov/index.html in your browser
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'pytest_django'"
**Solution**: Install pytest-django:
```bash
pip install pytest-django
```

### Issue: "django.core.exceptions.ImproperlyConfigured"
**Solution**: Ensure Django settings are configured:
```bash
export DJANGO_SETTINGS_MODULE=main_system.settings
```

### Issue: Database errors during tests
**Solution**: Django creates a test database automatically. Ensure your database user has CREATE DATABASE permissions.

### Issue: Tests are slow
**Solution**: 
- Use `--reuse-db` flag to reuse test database:
  ```bash
  pytest users_access/tests/ --reuse-db
  ```
- Run tests in parallel with pytest-xdist:
  ```bash
  pip install pytest-xdist
  pytest users_access/tests/ -n auto
  ```

## Test Coverage Goals

- **Target**: 80%+ code coverage
- **Current Focus**: Views and Services (as per test strategy)

## Running Tests in CI/CD

For CI/CD pipelines, use:
```bash
cd src
pytest users_access/tests/ --cov=users_access --cov-report=xml --junitxml=test-results.xml
```

This generates:
- Coverage report in XML format
- Test results in JUnit XML format (for CI integration)
