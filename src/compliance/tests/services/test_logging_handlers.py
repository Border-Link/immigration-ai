"""
Tests for compliance.handlers.*

We keep these unit-level by mocking DB/connection introspection.
"""

import pytest
import logging
from unittest.mock import patch, MagicMock


@pytest.mark.django_db
class TestDatabaseLogHandler:
    def test_emit_writes_to_db_when_table_exists(self):
        from compliance.handlers.handlers import DatabaseLogHandler
        from compliance.models.audit_log import AuditLog

        handler = DatabaseLogHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))

        record = logging.LogRecord(
            name="django",
            level=logging.INFO,
            pathname="/tmp/x.py",
            lineno=10,
            msg="hello",
            args=(),
            exc_info=None,
        )
        record.funcName = "f"
        record.process = 123
        record.threadName = "MainThread"

        with patch("compliance.handlers.handlers.connection") as conn, \
             patch.object(AuditLog.objects, "create") as create:
            conn.introspection.table_names.return_value = [AuditLog._meta.db_table]
            handler.emit(record)
            assert create.called is True
            kwargs = create.call_args.kwargs
            assert kwargs["level"] == "INFO"
            assert kwargs["logger_name"] == "django"
            assert kwargs["message"] == "hello"

    def test_emit_noops_when_table_introspection_fails(self):
        from compliance.handlers.handlers import DatabaseLogHandler
        from compliance.models.audit_log import AuditLog

        handler = DatabaseLogHandler()
        record = logging.LogRecord("django", logging.INFO, "p", 1, "m", (), None)

        with patch("compliance.handlers.handlers.connection") as conn, \
             patch.object(AuditLog.objects, "create") as create:
            conn.introspection.table_names.side_effect = Exception("blocked")
            handler.emit(record)
            assert create.called is False


@pytest.mark.django_db
class TestLazyDatabaseLogHandler:
    def test_lazy_handler_instantiates_once(self):
        from compliance.handlers.logging_handler import LazyDatabaseLogHandler

        lazy = LazyDatabaseLogHandler()
        record = logging.LogRecord("django", logging.INFO, "p", 1, "m", (), None)

        # DatabaseLogHandler is imported lazily inside emit() from compliance.handlers.handlers
        with patch("compliance.handlers.handlers.DatabaseLogHandler") as cls:
            inst = MagicMock()
            cls.return_value = inst

            lazy.emit(record)
            lazy.emit(record)
            assert cls.call_count == 1
            assert inst.emit.call_count == 2


@pytest.mark.django_db
class TestLoggingSetup:
    def test_safe_setup_adds_handler_when_table_exists_and_is_idempotent(self):
        from compliance.handlers.logging_setup import LoggingSetup
        from compliance.models.audit_log import AuditLog

        # Reset between tests (class-level singleton)
        LoggingSetup._is_initialized = False

        dummy_logger = MagicMock()
        dummy_logger.handlers = []

        def get_logger(_name):
            return dummy_logger

        with patch("compliance.handlers.logging_setup.connection") as conn, \
             patch("compliance.handlers.logging_setup.logging.getLogger", side_effect=get_logger), \
             patch("compliance.handlers.logging_setup.DatabaseLogHandler") as handler_cls:
            conn.connection = object()
            conn.introspection.table_names.return_value = [AuditLog._meta.db_table]

            LoggingSetup.safe_setup()
            assert handler_cls.called is True
            assert dummy_logger.addHandler.called is True

            # Second call should do nothing
            dummy_logger.addHandler.reset_mock()
            LoggingSetup.safe_setup()
            assert dummy_logger.addHandler.called is False

