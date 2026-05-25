import asyncio
import json
import uuid
import logging
from datetime import datetime
from enum import Enum
from typing import Callable, Any, Optional

from ecommerce_ops.memory.cache import cache

logger = logging.getLogger("ecommerce_ops.infra.task_queue")


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Task:
    def __init__(self, task_id: str, name: str, coro_factory: Callable, *args, **kwargs):
        self.id = task_id
        self.name = name
        self.coro_factory = coro_factory
        self.args = args
        self.kwargs = kwargs
        self.status = TaskStatus.PENDING
        self.result: Any = None
        self.error: Optional[str] = None
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None


class TaskQueue:
    def __init__(self, num_workers: int = 2, max_queue_size: int = 100, use_redis: bool = False):
        self._queue: asyncio.Queue[Task] = asyncio.Queue(maxsize=max_queue_size)
        self._workers: list[asyncio.Task] = []
        self._num_workers = num_workers
        self._running = False
        self._tasks: dict[str, Task] = {}
        self._use_redis = use_redis
        self._redis_prefix = "tq:"

    async def start(self):
        if self._running:
            return
        self._running = True
        self._workers = [
            asyncio.create_task(self._worker_loop(i), name=f"task-worker-{i}")
            for i in range(self._num_workers)
        ]
        logger.info(
            "TaskQueue started with %d workers (redis=%s)", self._num_workers, self._use_redis
        )

    async def stop(self, wait: bool = True):
        self._running = False
        for _ in range(self._num_workers):
            await self._queue.put(None)
        if wait and self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        logger.info("TaskQueue stopped")

    async def enqueue(
        self, name: str, coro_factory: Callable, *args, **kwargs
    ) -> str:
        task_id = str(uuid.uuid4())
        task = Task(task_id, name, coro_factory, *args, **kwargs)
        self._tasks[task_id] = task
        await self._queue.put(task)

        if self._use_redis:
            try:
                client = await cache.get_client()
                if client:
                    await client.lpush(
                        f"{self._redis_prefix}queue",
                        json.dumps({"task_id": task_id, "name": name}),
                    )
            except Exception as e:
                logger.warning("Failed to enqueue task in Redis: %s", e)

        logger.info("Task %s (%s) enqueued", task_id, name)
        return task_id

    def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    async def _worker_loop(self, worker_id: int):
        logger.debug("Worker %d started", worker_id)
        while self._running:
            task = await self._queue.get()
            if task is None:
                self._queue.task_done()
                break
            try:
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.utcnow()
                logger.info("Worker %d executing task %s (%s)", worker_id, task.id, task.name)
                coro = task.coro_factory(*task.args, **task.kwargs)
                task.result = await coro
                task.status = TaskStatus.COMPLETED
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                logger.exception("Worker %d task %s (%s) failed", worker_id, task.id, task.name)
            finally:
                task.completed_at = datetime.utcnow()
                self._queue.task_done()
        logger.debug("Worker %d stopped", worker_id)
