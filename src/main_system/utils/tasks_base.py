import json
import time
from celery import Task
from django.utils.timezone import now
from django_celery_results.models import TaskResult
import logging

logger = logging.getLogger('django')

class BaseTaskWithMeta(Task):
    abstract = True

    def __init__(self):
        self.start_time = None

    def before_start(self, task_id, args, kwargs):
        self.start_time = time.perf_counter()

    def on_success(self, retval, task_id, args, kwargs):
        execution_time = time.perf_counter() - self.start_time

        task_log = self._build_log(
            status="SUCCESS",
            task_id=task_id,
            args=args,
            kwargs=kwargs,
            retval=retval,
            message=f"Task {self.name} completed successfully",
            error_message=None,
            traceback=None
        )
        task_log["execution_time"] = f"{execution_time:.6f} seconds"

        self._update_task_result(task_log)
        logger.info(json.dumps(task_log, indent=4))

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        task_log = self._build_log(
            status="FAILURE",
            task_id=task_id,
            args=args,
            kwargs=kwargs,
            retval=None,
            message=f"Task {self.name} failed with error: {str(exc)}",
            error_message=str(exc),
            traceback=str(einfo)
        )
        self._update_task_result(task_log)
        logger.error(json.dumps(task_log, indent=4))

    def _build_log(self, status, task_id, args, kwargs, retval, message, error_message, traceback):
        req = getattr(self, "request", None)

        return {
            "task_id": task_id or (req.id if req else None),
            "task_name": self.name,
            "status": status,
            "worker": getattr(req, "hostname", None),
            "worker_pid": getattr(req, "worker_pid", None),
            "parent_id": getattr(req, "parent_id", None),
            "root_id": getattr(req, "root_id", None),
            "correlation_id": getattr(req, "correlation_id", None),
            "retries": getattr(req, "retries", 0),
            "eta": str(getattr(req, "eta", None)),
            "expires": str(getattr(req, "expires", None)),
            "timelimit": getattr(req, "timelimit", None),
            "rate_limit": getattr(req, "rate_limit", None),
            "priority": getattr(req, "priority", None),
            "delivery_info": self._serialize(getattr(req, "delivery_info", {})),
            "args": self._serialize(args),
            "args_repr": getattr(req, "argsrepr", None),
            "kwargs": self._serialize(kwargs),
            "kwargs_repr": getattr(req, "kwargsrepr", None),
            "result": self._serialize(retval),
            "error_message": error_message,
            "traceback": traceback,
            "timestamp": str(now()),
            "message": message,
        }

    def _update_task_result(self, task_log):
        try:
            TaskResult.objects.update_or_create(
                task_id=task_log['task_id'],
                defaults={"meta": json.dumps(task_log)}
            )
        except Exception as e:
            logger.error(f"Error updating task result in DB: {e}")

    def _serialize(self, data):
        try:
            return json.loads(json.dumps(data, default=str))
        except Exception as e:
            logger.warning(f"Failed to serialize data: {e}")
            return str(data)
