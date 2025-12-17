import logging
from django.db import connection
from django.db.utils import OperationalError
from ..models.audit_log import AuditLog

class DatabaseLogHandler(logging.Handler):
    def emit(self, record):
        """Stores log messages in the database."""
        try:
            if "audit_log_auditlog" in connection.introspection.table_names():  #Ensure DB table exists
                AuditLog.objects.create(
                    level=record.levelname,
                    logger_name=record.name,
                    message=self.format(record),
                    pathname=record.pathname,
                    lineno=record.lineno,
                    func_name=record.funcName,
                    process=record.process,
                    thread=record.threadName
                )
        except OperationalError as e:
            logging.getLogger("django").warning(f"Database unavailable: {e}")
        except Exception as e:
            logging.getLogger("django").error(f"Error saving logentry: {e}")
