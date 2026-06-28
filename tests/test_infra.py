"""Tests for Rate Limiter and Task Queue."""

import asyncio
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ecommerce_ops.infra.rate_limiter import _memory_check, _memory_store, _memory_block_until


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

    for i in range(4):
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

    allowed, count = _memory_check("test_key", 5, 60)
    assert allowed is False


def test_memory_check_different_keys_independent():
    _memory_store.clear()
    _memory_block_until.clear()

    for _ in range(5):
        _memory_check("key1", 5, 60)

    allowed, count = _memory_check("key2", 5, 60)
    assert allowed is True


def test_memory_check_evicts_old_entries():
    _memory_store.clear()
    _memory_block_until.clear()

    for _ in range(3):
        _memory_check("test_key", 5, 1)

    _memory_store["test_key"] = [time.time() - 10]

    allowed, count = _memory_check("test_key", 5, 1)
    assert allowed is True


def test_memory_check_blocks_for_window():
    _memory_store.clear()
    _memory_block_until.clear()

    for _ in range(5):
        _memory_check("test_key", 5, 60)

    allowed, _ = _memory_check("test_key", 5, 60)
    assert allowed is False


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
    from ecommerce_ops.infra.task_queue import TaskQueue, MAX_TASKS

    tq = TaskQueue(num_workers=0)
    tq._tasks = {str(i): MagicMock(created_at=time.time()) for i in range(MAX_TASKS)}

    with pytest.raises(RuntimeError, match="full"):
        await tq.enqueue("test", AsyncMock)


@pytest.mark.asyncio
async def test_task_queue_evicts_expired():
    from ecommerce_ops.infra.task_queue import TaskQueue, Task, TaskStatus

    tq = TaskQueue(num_workers=0)
    old_task = Task("old", "test", AsyncMock)
    old_task.created_at = time.time() - 86400 * 25
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
