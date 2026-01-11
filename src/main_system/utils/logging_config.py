import logging
from pythonjsonlogger.json import JsonFormatter

class CustomJsonFormatter(JsonFormatter):
    """Custom JSON formatter for structured logging."""

    def add_fields(self, log_record, record, message_dict):
        from django.conf import settings
        import traceback
        from django.utils.timezone import now
        import uuid


        """Enhance logs with additional structured fields."""
        super().add_fields(log_record, record, message_dict)

        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["timestamp"] = now().isoformat()  # ISO 8601 timestamp
        log_record["service"] = getattr(settings, "SERVICE_NAME", "default-service")
        log_record["version"] = getattr(settings, "VERSION", "1.0.0")
        log_record["release"] = getattr(settings, "RELEASE", "latest")
        log_record["environment"] = getattr(settings, "DJANGO_ENV", "development")
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
