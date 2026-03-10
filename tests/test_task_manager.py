"""调度任务管理测试。"""

from pathlib import Path

import pytest

from src.schedulers import RuntimeTaskManager, TaskLockError


def test_task_manager_prevents_duplicate_scheduler_runs(tmp_path):
    """验证同名任务重复获取锁时会失败。"""

    manager = RuntimeTaskManager(Path(tmp_path))

    with manager.guard(task_name="demo", run_id="run-1", run_mode="scheduler"):
        with pytest.raises(TaskLockError):
            manager.acquire(task_name="demo", run_id="run-2", run_mode="scheduler")


def test_task_manager_releases_lock_after_context(tmp_path):
    """验证上下文退出后锁文件会被清理。"""

    manager = RuntimeTaskManager(Path(tmp_path))
    lock_path = Path(tmp_path) / "locks" / "demo.lock"

    with manager.guard(task_name="demo", run_id="run-1", run_mode="scheduler"):
        assert lock_path.exists()

    assert not lock_path.exists()


def test_task_manager_recovers_stale_lock(tmp_path):
    """验证当锁文件存在但 PID 已失效时，会自动回收陈旧锁。"""

    manager = RuntimeTaskManager(Path(tmp_path))
    lock_path = Path(tmp_path) / "locks" / "demo.lock"
    pid_path = Path(tmp_path) / "pid" / "demo.json"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text("stale\n", encoding="utf-8")
    pid_path.write_text(
        '{"task_name":"demo","run_id":"old-run","run_mode":"scheduler","pid":999999,"started_at":"2026-03-01T00:00:00+08:00"}',
        encoding="utf-8",
    )

    payload = manager.acquire(task_name="demo", run_id="run-2", run_mode="scheduler")

    assert payload["run_id"] == "run-2"
    assert lock_path.exists()
    manager.release("demo")
