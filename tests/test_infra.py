"""Tests for Rate Limiter and Task Queue."""

from ecommerce_ops.utils import utc_now

import asyncio
import time
from unittest.mock import AsyncMock

import pytest

from ecommerce_ops.infra.rate_limiter import (
    _memory_block_until,
    _memory_check,
    _memory_store,
)

# ── Rate Limiter Tests ────────────────────────────────────


def test_memory_check_allows_under_limit():
    _memory_store.clear()
    _memory_block_until.clear()

    allowed, count = _memory_check("test_key", 5, 60)
    assert allowed is True
    assert count == 1


def test_memory_check_allows_up_to_limit():
    _memory_store.clear()
    _memory_block_until.clear()

    for _ in range(4):
        allowed, count = _memory_check("test_key", 5, 60)
        assert allowed is True

    allowed, count = _memory_check("test_key", 5, 60)
    assert allowed is True
    assert count == 5


def test_memory_check_blocks_at_limit():
    _memory_store.clear()
    _memory_block_until.clear()

    for _ in range(5):
        _memory_check("test_key", 5, 60)

    allowed, _ = _memory_check("test_key", 5, 60)
    assert allowed is False


def test_memory_check_different_keys_independent():
    _memory_store.clear()
    _memory_block_until.clear()

    for _ in range(5):
        _memory_check("key1", 5, 60)

    allowed, _ = _memory_check("key2", 5, 60)
    assert allowed is True


def test_memory_check_evicts_old_entries():
    _memory_store.clear()
    _memory_block_until.clear()

    for _ in range(3):
        _memory_check("test_key", 5, 1)

    _memory_store["test_key"] = [time.time() - 10]

    allowed, _ = _memory_check("test_key", 5, 1)
    assert allowed is True


def test_memory_check_blocks_for_window():
    _memory_store.clear()
    _memory_block_until.clear()

    for _ in range(5):
        _memory_check("test_key", 5, 60)

    allowed, _ = _memory_check("test_key", 5, 60)
    assert allowed is False


def test_memory_check_eviction_keeps_recent_keys(monkeypatch):
    """When the store exceeds its cap, only the least-recent keys are evicted —
    active clients must keep their sliding windows (regression for the full-clear
    bug that would flush every caller's state on a surge)."""
    import ecommerce_ops.infra.rate_limiter as rl

    monkeypatch.setattr(rl, "MEMORY_MAX_ENTRIES", 3)
    _memory_store.clear()
    _memory_block_until.clear()

    now = time.time()
    _memory_store["stale"] = [now - 100]
    _memory_store["active"] = [now]
    _memory_store["newer"] = [now]
    assert len(_memory_store) == 3  # at cap, nothing evicted

    # Crossing the cap evicts only the oldest key
    allowed, count = _memory_check("fresh", 50, 60)
    assert allowed is True
    assert count == 1
    assert "stale" not in _memory_store
    assert "active" in _memory_store and "newer" in _memory_store

    # The recently-active key keeps its sliding window and is still rate limited
    for _ in range(4):
        allowed, _ = _memory_check("active", 5, 60)
        assert allowed is True
    allowed, _ = _memory_check("active", 5, 60)
    assert allowed is False


def test_memory_check_eviction_drops_blocked_keys(monkeypatch):
    """Evicted keys also lose their block entries so they are not permanently stuck."""
    import ecommerce_ops.infra.rate_limiter as rl

    monkeypatch.setattr(rl, "MEMORY_MAX_ENTRIES", 2)
    _memory_store.clear()
    _memory_block_until.clear()

    now = time.time()
    _memory_store["stale"] = [now - 100]
    _memory_store["fresh"] = [now]
    _memory_block_until["stale"] = now + 60
    assert "stale" in _memory_block_until

    _memory_check("new", 50, 60)  # pushes store over the cap
    assert len(_memory_store) <= 2
    assert "stale" not in _memory_store
    assert "stale" not in _memory_block_until


# ── Task Queue Tests ──────────────────────────────────────


@pytest.mark.asyncio
async def test_task_queue_enqueue():
    from ecommerce_ops.infra.task_queue import TaskQueue

    tq = TaskQueue(num_workers=0)
    task_id = await tq.enqueue("test_task", AsyncMock)
    assert task_id is not None
    assert tq.get_task(task_id) is not None


@pytest.mark.asyncio
async def test_task_queue_max_tasks():

    from ecommerce_ops.infra.task_queue import (
        MAX_TASKS,
        QueueFullError,
        Task,
        TaskQueue,
        TaskStatus,
    )

    tq = TaskQueue(num_workers=0)
    tq._tasks = {str(i): Task(str(i), "test", AsyncMock) for i in range(MAX_TASKS)}
    for t in tq._tasks.values():
        t.status = TaskStatus.RUNNING

    with pytest.raises(QueueFullError, match="maximum capacity"):
        await tq.enqueue("test", AsyncMock)


@pytest.mark.asyncio
async def test_task_queue_evicts_expired():
    from datetime import datetime, timedelta

    from ecommerce_ops.infra.task_queue import Task, TaskQueue, TaskStatus

    tq = TaskQueue(num_workers=0)
    old_task = Task("old", "test", AsyncMock)
    old_task.created_at = utc_now() - timedelta(hours=25)
    old_task.status = TaskStatus.COMPLETED
    tq._tasks["old"] = old_task

    tq._evict_expired()
    assert "old" not in tq._tasks


@pytest.mark.asyncio
async def test_task_queue_worker_executes():
    from ecommerce_ops.infra.task_queue import TaskQueue, TaskStatus

    async def dummy():
        return "done"

    tq = TaskQueue(num_workers=1)
    await tq.start()

    task_id = await tq.enqueue("worker_test", dummy)
    await asyncio.sleep(0.5)

    task = tq.get_task(task_id)
    assert task.status == TaskStatus.COMPLETED
    assert task.result == "done"

    await tq.stop()


@pytest.mark.asyncio
async def test_task_queue_worker_handles_failure():
    from ecommerce_ops.infra.task_queue import TaskQueue, TaskStatus

    async def failing():
        raise ValueError("boom")

    tq = TaskQueue(num_workers=1)
    await tq.start()

    task_id = await tq.enqueue("fail_test", failing)
    await asyncio.sleep(0.5)

    task = tq.get_task(task_id)
    assert task.status == TaskStatus.FAILED
    assert "boom" in task.error

    await tq.stop()


@pytest.mark.asyncio
async def test_task_queue_stop():
    from ecommerce_ops.infra.task_queue import TaskQueue

    tq = TaskQueue(num_workers=2)
    await tq.start()
    assert tq._running is True

    await tq.stop()
    assert tq._running is False
