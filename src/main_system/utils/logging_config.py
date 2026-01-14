import logging

# Import JsonFormatter at module level - this should be safe as it doesn't depend on Django
try:
    from pythonjsonlogger.json import JsonFormatter
except ImportError:
    # Fallback if pythonjsonlogger is not available
    JsonFormatter = logging.Formatter

class CustomJsonFormatter(JsonFormatter):
    """Custom JSON formatter for structured logging."""

    def add_fields(self, log_record, record, message_dict):
        """Enhance logs with additional structured fields."""
        # Lazy imports to avoid circular dependencies during Django setup
        # These imports happen when the method is called, not when the module is imported
        try:
            from django.conf import settings
            import traceback
            from django.utils.timezone import now
            import uuid
        except ImportError:
            # Django not yet initialized - use fallbacks
            import datetime
            import uuid
            import traceback
            settings = None
            now = lambda: datetime.datetime.now(datetime.timezone.utc)
        
        # Call parent's add_fields
        super().add_fields(log_record, record, message_dict)

        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["timestamp"] = now().isoformat()  # ISO 8601 timestamp
        
        # Only access Django settings if available
        if settings is not None:
            log_record["service"] = getattr(settings, "SERVICE_NAME", "default-service")
            log_record["version"] = getattr(settings, "VERSION", "1.0.0")
            log_record["release"] = getattr(settings, "RELEASE", "latest")
            log_record["environment"] = getattr(settings, "DJANGO_ENV", "development")
        else:
            log_record["service"] = "default-service"
            log_record["version"] = "1.0.0"
            log_record["release"] = "latest"
            log_record["environment"] = "development"
        
        log_record["request_id"] = getattr(record, "request_id", str(uuid.uuid4()))  # Unique request ID
        log_record["user_id"] = getattr(record, "user_id", None)
        log_record["ip_address"] = getattr(record, "ip_address", None)
        log_record["path"] = getattr(record, "path", None)
        log_record["method"] = getattr(record, "method", None)
        log_record["status_code"] = getattr(record, "status_code", None)
        log_record["duration"] = getattr(record, "duration", None)

        # Ensure message is properly formatted
        try:
            log_record["message"] = record.getMessage()
        except Exception as e:
            log_record["message"] = str(e)
            log_record["error"] = "Failed to format message"

        # Capture stack trace if available
        if record.exc_info:
            log_record["stack_trace"] = "".join(traceback.format_exception(*record.exc_info))
