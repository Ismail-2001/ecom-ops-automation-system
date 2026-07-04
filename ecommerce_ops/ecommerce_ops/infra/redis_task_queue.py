"""
Redis-Backed Task Queue
Replaces in-memory asyncio.Queue for production use.
"""
import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional

logger = logging.getLogger("ecommerce_ops.infra.redis_task_queue")


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Task:
    """Task definition."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: float = 300.0
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "payload": self.payload,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "error": self.error,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            payload=data.get("payload", {}),
            status=TaskStatus(data.get("status", "pending")),
            priority=TaskPriority(data.get("priority", "normal")),
            created_at=data.get("created_at", time.time()),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            result=data.get("result"),
            error=data.get("error"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            timeout_seconds=data.get("timeout_seconds", 300),
            tags=data.get("tags", []),
        )


class RedisTaskQueue:
    """
    Redis-backed task queue with priority, retry, and timeout support.
    Works across multiple worker instances.
    """

    QUEUE_KEY = "taskqueue:pending"
    PROCESSING_KEY = "taskqueue:processing"
    RESULTS_PREFIX = "taskqueue:result:"
    TASK_PREFIX = "taskqueue:task:"

    def __init__(self, redis_client, num_workers: int = 2, max_queue_size: int = 1000):
        self.redis = redis_client
        self.num_workers = num_workers
        self.max_queue_size = max_queue_size
        self._handlers: Dict[str, Callable] = {}
        self._workers: List[asyncio.Task] = []
        self._running = False
        self._stats = {"enqueued": 0, "completed": 0, "failed": 0, "retried": 0}

    def register_handler(self, task_name: str, handler: Callable[..., Coroutine]):
        """Register a handler for a task type."""
        self._handlers[task_name] = handler
        logger.info(f"Registered handler for task: {task_name}")

    async def enqueue(
        self,
        task_name: str,
        payload: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout_seconds: float = 300.0,
        max_retries: int = 3,
        tags: Optional[List[str]] = None,
    ) -> str:
        """Enqueue a task. Returns task ID."""
        task = Task(
            name=task_name,
            payload=payload,
            priority=priority,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            tags=tags or [],
        )

        try:
            # Store task data
            await self.redis.hset(
                f"{self.TASK_PREFIX}{task.id}",
                mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in task.to_dict().items()},
            )
            await self.redis.expire(f"{self.TASK_PREFIX}{task.id}", 86400)  # 24h TTL

            # Add to priority queue
            score = self._priority_score(priority)
            await self.redis.zadd(self.QUEUE_KEY, {task.id: score})

            self._stats["enqueued"] += 1
            logger.info(f"Enqueued task {task.id} ({task_name}) with priority {priority.value}")
            return task.id

        except Exception as e:
            logger.error(f"Failed to enqueue task: {e}")
            raise

    async def dequeue(self) -> Optional[Task]:
        """Dequeue the highest priority task."""
        try:
            # Get highest priority task
            result = await self.redis.zpopmax(self.QUEUE_KEY, count=1)
            if not result:
                return None

            task_id = result[0][0]
            if isinstance(task_id, bytes):
                task_id = task_id.decode()

            # Get task data
            task_data = await self.redis.hgetall(f"{self.TASK_PREFIX}{task_id}")
            if not task_data:
                return None

            task = self._dict_to_task(task_data)
            task.status = TaskStatus.PROCESSING
            task.started_at = time.time()

            # Move to processing
            await self.redis.hset(
                f"{self.TASK_PREFIX}{task.id}",
                mapping={"status": "processing", "started_at": str(task.started_at)},
            )
            await self.redis.sadd(self.PROCESSING_KEY, task.id)

            return task

        except Exception as e:
            logger.error(f"Failed to dequeue task: {e}")
            return None

    async def complete_task(self, task_id: str, result: Any = None):
        """Mark a task as completed."""
        try:
            await self.redis.hset(
                f"{self.TASK_PREFIX}{task_id}",
                mapping={
                    "status": "completed",
                    "completed_at": str(time.time()),
                    "result": json.dumps(result) if result else "",
                },
            )
            await self.redis.srem(self.PROCESSING_KEY, task_id)
            await self.redis.setex(f"{self.RESULTS_PREFIX}{task_id}", 3600, json.dumps(result) if result else "")

            self._stats["completed"] += 1
            logger.info(f"Task {task_id} completed")

        except Exception as e:
            logger.error(f"Failed to complete task: {e}")

    async def fail_task(self, task_id: str, error: str, retry: bool = True):
        """Mark a task as failed, optionally retrying."""
        try:
            task_data = await self.redis.hgetall(f"{self.TASK_PREFIX}{task_id}")
            if not task_data:
                return

            task = self._dict_to_task(task_data)

            if retry and task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.RETRY
                await self.redis.hset(
                    f"{self.TASK_PREFIX}{task_id}",
                    mapping={
                        "status": "retry",
                        "retry_count": str(task.retry_count),
                        "error": error,
                    },
                )
                # Re-enqueue with lower priority
                await self.redis.zadd(self.QUEUE_KEY, {task_id: self._priority_score(TaskPriority.LOW)})
                self._stats["retried"] += 1
                logger.info(f"Task {task_id} retrying ({task.retry_count}/{task.max_retries})")
            else:
                task.status = TaskStatus.FAILED
                await self.redis.hset(
                    f"{self.TASK_PREFIX}{task_id}",
                    mapping={
                        "status": "failed",
                        "completed_at": str(time.time()),
                        "error": error,
                    },
                )
                self._stats["failed"] += 1
                logger.error(f"Task {task_id} failed: {error}")

            await self.redis.srem(self.PROCESSING_KEY, task_id)

        except Exception as e:
            logger.error(f"Failed to handle task failure: {e}")

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        try:
            task_data = await self.redis.hgetall(f"{self.TASK_PREFIX}{task_id}")
            if not task_data:
                return None
            return self._dict_to_task(task_data)
        except Exception as e:
            logger.error(f"Failed to get task: {e}")
            return None

    async def get_result(self, task_id: str, timeout: float = 30.0) -> Any:
        """Wait for and get task result."""
        start = time.time()
        while time.time() - start < timeout:
            task = await self.get_task(task_id)
            if task and task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                return task.result if task.status == TaskStatus.COMPLETED else None
            await asyncio.sleep(0.1)
        return None

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task."""
        try:
            removed = await self.redis.zrem(self.QUEUE_KEY, task_id)
            if removed:
                await self.redis.hset(
                    f"{self.TASK_PREFIX}{task_id}",
                    mapping={"status": "cancelled"},
                )
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to cancel task: {e}")
            return False

    async def start(self):
        """Start worker tasks."""
        self._running = True
        for i in range(self.num_workers):
            worker = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self._workers.append(worker)
        logger.info(f"Started {self.num_workers} workers")

    async def stop(self, wait: bool = True):
        """Stop worker tasks."""
        self._running = False
        for worker in self._workers:
            worker.cancel()
        if wait:
            await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        logger.info("Workers stopped")

    async def _worker_loop(self, worker_id: str):
        """Worker loop that processes tasks."""
        logger.info(f"{worker_id} started")
        while self._running:
            try:
                task = await self.dequeue()
                if not task:
                    await asyncio.sleep(0.5)
                    continue

                handler = self._handlers.get(task.name)
                if not handler:
                    await self.fail_task(task.id, f"No handler for task: {task.name}", retry=False)
                    continue

                try:
                    result = await asyncio.wait_for(
                        handler(task.payload),
                        timeout=task.timeout_seconds,
                    )
                    await self.complete_task(task.id, result)
                except asyncio.TimeoutError:
                    await self.fail_task(task.id, f"Task timed out after {task.timeout_seconds}s")
                except Exception as e:
                    await self.fail_task(task.id, str(e))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"{worker_id} error: {e}")
                await asyncio.sleep(1)

        logger.info(f"{worker_id} stopped")

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        return {**self._stats, "handlers": list(self._handlers.keys()), "workers": self.num_workers}

    @staticmethod
    def _priority_score(priority: TaskPriority) -> float:
        """Convert priority to score (higher = processed first)."""
        scores = {
            TaskPriority.CRITICAL: 1000,
            TaskPriority.HIGH: 100,
            TaskPriority.NORMAL: 10,
            TaskPriority.LOW: 1,
        }
        return scores.get(priority, 10)

    @staticmethod
    def _dict_to_task(data: Dict[str, bytes]) -> Task:
        """Convert Redis hash to Task."""
        def get(key, default=""):
            val = data.get(key, default)
            return val.decode() if isinstance(val, bytes) else val

        return Task(
            id=get("id"),
            name=get("name"),
            payload=json.loads(get("payload", "{}")),
            status=TaskStatus(get("status", "pending")),
            priority=TaskPriority(get("priority", "normal")),
            created_at=float(get("created_at", time.time())),
            started_at=float(get("started_at")) if get("started_at") else None,
            completed_at=float(get("completed_at")) if get("completed_at") else None,
            result=json.loads(get("result", "null")) if get("result") else None,
            error=get("error") or None,
            retry_count=int(get("retry_count", 0)),
            max_retries=int(get("max_retries", 3)),
            timeout_seconds=float(get("timeout_seconds", 300)),
            tags=json.loads(get("tags", "[]")),
        )
