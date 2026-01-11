"""
Prometheus Metrics for Users Access Module

Custom metrics for monitoring user access operations including:
- User registration and authentication
- OTP operations
- Password reset operations
- User profile management
- Device session management
"""
import time
from functools import wraps

# Import prometheus_client for custom metrics
try:
    from prometheus_client import Counter, Histogram, Gauge
except ImportError:
    Counter = None
    Histogram = None
    Gauge = None


# User Management Metrics
if Counter and Histogram:
    user_registrations_total = Counter(
        'users_access_user_registrations_total',
        'Total number of user registrations',
        ['status']  # status: success, failure, email_exists
    )
    
    user_authentications_total = Counter(
        'users_access_user_authentications_total',
        'Total number of user authentications',
        ['status', 'method']  # status: success, failure; method: password, otp, token
    )
    
    authentication_duration_seconds = Histogram(
        'users_access_authentication_duration_seconds',
        'Duration of authentication operations in seconds',
        ['method'],
        buckets=(0.1, 0.5, 1.0, 2.0, 5.0)
    )
    
    # OTP Metrics
    otp_generations_total = Counter(
        'users_access_otp_generations_total',
        'Total number of OTP generations',
        ['purpose']  # purpose: login, registration, password_reset, 2fa
    )
    
    otp_verifications_total = Counter(
        'users_access_otp_verifications_total',
        'Total number of OTP verifications',
        ['status']  # status: success, failure, expired
    )
    
    otp_verification_duration_seconds = Histogram(
        'users_access_otp_verification_duration_seconds',
        'Duration of OTP verification in seconds',
        [],
        buckets=(0.1, 0.5, 1.0, 2.0)
    )
    
    # Password Reset Metrics
    password_reset_requests_total = Counter(
        'users_access_password_reset_requests_total',
        'Total number of password reset requests',
        ['status']  # status: success, failure, user_not_found
    )
    
    password_resets_total = Counter(
        'users_access_password_resets_total',
        'Total number of password resets completed',
        ['status']  # status: success, failure, token_invalid
    )
    
    password_reset_duration_seconds = Histogram(
        'users_access_password_reset_duration_seconds',
        'Duration of password reset operations in seconds',
        [],
        buckets=(0.5, 1.0, 2.0, 5.0)
    )
    
    # User Profile Metrics
    user_profile_updates_total = Counter(
        'users_access_user_profile_updates_total',
        'Total number of user profile updates',
        ['update_type']  # update_type: name, avatar, settings, etc.
    )
    
    # Device Session Metrics
    device_sessions_created_total = Counter(
        'users_access_device_sessions_created_total',
        'Total number of device sessions created',
        ['device_type']  # device_type: web, mobile, tablet
    )
    
    device_sessions_active = Gauge(
        'users_access_device_sessions_active',
        'Current number of active device sessions',
        ['device_type']
    )
    
    device_session_duration_seconds = Histogram(
        'users_access_device_session_duration_seconds',
        'Duration of device sessions in seconds',
        ['device_type'],
        buckets=(300, 1800, 3600, 7200, 86400, 604800)  # 5 min to 1 week
    )
    
    # User Account Metrics
    user_accounts_by_status = Gauge(
        'users_access_user_accounts_by_status',
        'Current number of user accounts by status',
        ['status']  # status: active, inactive, suspended, deleted
    )
    
    user_accounts_by_role = Gauge(
        'users_access_user_accounts_by_role',
        'Current number of user accounts by role',
        ['role']  # role: user, reviewer, admin
    )
    
    # Security Metrics
    failed_login_attempts_total = Counter(
        'users_access_failed_login_attempts_total',
        'Total number of failed login attempts',
        ['reason']  # reason: invalid_password, user_not_found, account_locked
    )
    
    account_lockouts_total = Counter(
        'users_access_account_lockouts_total',
        'Total number of account lockouts',
        ['reason']  # reason: too_many_failed_attempts, suspicious_activity
    )
    
else:
    # Dummy metrics
    user_registrations_total = None
    user_authentications_total = None
    authentication_duration_seconds = None
    otp_generations_total = None
    otp_verifications_total = None
    otp_verification_duration_seconds = None
    password_reset_requests_total = None
    password_resets_total = None
    password_reset_duration_seconds = None
    user_profile_updates_total = None
    device_sessions_created_total = None
    device_sessions_active = None
    device_session_duration_seconds = None
    user_accounts_by_status = None
    user_accounts_by_role = None
    failed_login_attempts_total = None
    account_lockouts_total = None


def track_user_registration(status: str):
    """Track user registration."""
    if user_registrations_total:
        user_registrations_total.labels(status=status).inc()


def track_user_authentication(status: str, method: str, duration: float):
    """Track user authentication."""
    if user_authentications_total:
        user_authentications_total.labels(status=status, method=method).inc()
    if authentication_duration_seconds:
        authentication_duration_seconds.labels(method=method).observe(duration)


def track_otp_generation(purpose: str):
    """Track OTP generation."""
    if otp_generations_total:
        otp_generations_total.labels(purpose=purpose).inc()


def track_otp_verification(status: str, duration: float):
    """Track OTP verification."""
    if otp_verifications_total:
        otp_verifications_total.labels(status=status).inc()
    if otp_verification_duration_seconds:
        otp_verification_duration_seconds.observe(duration)


def track_password_reset_request(status: str):
    """Track password reset request."""
    if password_reset_requests_total:
        password_reset_requests_total.labels(status=status).inc()


def track_password_reset(status: str, duration: float):
    """Track password reset completion."""
    if password_resets_total:
        password_resets_total.labels(status=status).inc()
    if password_reset_duration_seconds:
        password_reset_duration_seconds.observe(duration)


def track_user_profile_update(update_type: str):
    """Track user profile update."""
    if user_profile_updates_total:
        user_profile_updates_total.labels(update_type=update_type).inc()


def track_device_session_created(device_type: str):
    """Track device session creation."""
    if device_sessions_created_total:
        device_sessions_created_total.labels(device_type=device_type).inc()


def update_device_sessions_active(device_type: str, count: int):
    """Update active device sessions gauge."""
    if device_sessions_active:
        device_sessions_active.labels(device_type=device_type).set(count)


def track_device_session_duration(device_type: str, duration: float):
    """Track device session duration."""
    if device_session_duration_seconds:
        device_session_duration_seconds.labels(device_type=device_type).observe(duration)


def update_user_accounts_by_status(status: str, count: int):
    """Update user accounts by status gauge."""
    if user_accounts_by_status:
        user_accounts_by_status.labels(status=status).set(count)


def update_user_accounts_by_role(role: str, count: int):
    """Update user accounts by role gauge."""
    if user_accounts_by_role:
        user_accounts_by_role.labels(role=role).set(count)


def track_failed_login_attempt(reason: str):
    """Track failed login attempt."""
    if failed_login_attempts_total:
        failed_login_attempts_total.labels(reason=reason).inc()


def track_account_lockout(reason: str):
    """Track account lockout."""
    if account_lockouts_total:
        account_lockouts_total.labels(reason=reason).inc()
