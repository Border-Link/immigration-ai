import logging

class LazyDatabaseLogHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._handler = None

    def emit(self, record):
        if self._handler is None:
            from .handlers import DatabaseLogHandler
            self._handler = DatabaseLogHandler()
        self._handler.emit(record)
