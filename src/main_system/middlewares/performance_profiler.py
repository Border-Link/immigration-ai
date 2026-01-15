"""
Performance profiling middleware (opt-in).

Enable with:
- PERF_PROFILE_REQUESTS=1  -> log request duration + DB query counts/timings

Notes:
- Designed to be safe to leave enabled in code but disabled by default.
- Intended for staging/production to identify hot endpoints for caching.
"""

from __future__ import annotations

import logging
import time
from typing import Optional, Callable, Awaitable, Any
import inspect

from django.conf import settings
from django.db import connection

logger = logging.getLogger("django")


class PerformanceProfilerMiddleware:
    """
    New-style middleware (sync + async compatible).

    Edge-case handling:
    - Logs even when a view raises (exception path).
    - Safe/no-op when PERF_PROFILE_REQUESTS is disabled.
    - DB query stats rely on Django query logging; in production this is often off by design.
    """

    def __init__(self, get_response: Callable[..., Any]):
        self.get_response = get_response
        self._is_async = inspect.iscoroutinefunction(get_response)

    def __call__(self, request):
        if self._is_async:
            return self._acall(request)

        if not getattr(settings, "PERF_PROFILE_REQUESTS", False):
            return self.get_response(request)

        start = time.perf_counter()
        db_q_start = len(getattr(connection, "queries", []))

        response = None
        exc: Optional[BaseException] = None
        try:
            response = self.get_response(request)
            return response
        except BaseException as e:
            exc = e
            raise
        finally:
            self._log(request=request, response=response, exc=exc, start=start, db_q_start=db_q_start)

    async def _acall(self, request):
        if not getattr(settings, "PERF_PROFILE_REQUESTS", False):
            return await self.get_response(request)

        start = time.perf_counter()
        db_q_start = len(getattr(connection, "queries", []))

        response = None
        exc: Optional[BaseException] = None
        try:
            response = await self.get_response(request)
            return response
        except BaseException as e:
            exc = e
            raise
        finally:
            self._log(request=request, response=response, exc=exc, start=start, db_q_start=db_q_start)

    def _log(self, *, request, response, exc: Optional[BaseException], start: float, db_q_start: int) -> None:
        duration_ms = (time.perf_counter() - start) * 1000.0

        # DB query accounting (only populated when Django is configured to collect query stats).
        queries = getattr(connection, "queries", [])
        new_queries = queries[db_q_start:]

        query_count = len(new_queries)
        db_time_ms = 0.0
        for q in new_queries:
            try:
                db_time_ms += float(q.get("time", 0.0)) * 1000.0
            except Exception:
                continue

        status = getattr(response, "status_code", 500 if exc else "")
        if exc is not None:
            logger.info(
                "PERF request=%s %s status=%s duration_ms=%.1f db_queries=%s db_time_ms=%.1f exc=%s",
                getattr(request, "method", "UNKNOWN"),
                getattr(request, "path", ""),
                status,
                duration_ms,
                query_count,
                db_time_ms,
                exc.__class__.__name__,
            )
            return

        logger.info(
            "PERF request=%s %s status=%s duration_ms=%.1f db_queries=%s db_time_ms=%.1f",
            getattr(request, "method", "UNKNOWN"),
            getattr(request, "path", ""),
            status,
            duration_ms,
            query_count,
            db_time_ms,
        )

