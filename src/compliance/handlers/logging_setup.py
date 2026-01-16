from django.db.utils import OperationalError
from django.db import connection
from .handlers import DatabaseLogHandler
import logging


class LoggingSetup:
    _is_initialized = False # this prevents duplicate handlers from being created

    @classmethod
    def safe_setup(cls, sender=None, **kwargs):
        if cls._is_initialized:
            return

        try:
            if connection.connection is None:
                connection.ensure_connection()

            # Use the actual db table name from the model to avoid drift.
            from compliance.models.audit_log import AuditLog
            audit_log_table = AuditLog._meta.db_table

            if audit_log_table in connection.introspection.table_names():
                handler = DatabaseLogHandler()
                for logger_name in ["django", "celery"]:
                    logger = logging.getLogger(logger_name)
                    if not any(isinstance(h, DatabaseLogHandler) for h in logger.handlers):
                        logger.addHandler(handler)

                cls._is_initialized = True
        except OperationalError:
            pass
        except Exception as e:
            logging.getLogger("django").error(f"Error during LoggingSetup.safe_setup: {e}")






