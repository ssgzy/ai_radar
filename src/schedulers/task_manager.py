"""运行时任务锁与 PID 管理。"""

from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from src.utils.file_ops import ensure_dir, read_json, write_json
from src.utils.time_utils import now_local_iso


class TaskLockError(RuntimeError):
    """表示某个调度任务已经在运行。"""


class RuntimeTaskManager:
    """负责调度模式下的运行锁和 PID 元信息。"""

    def __init__(self, runtime_root: Path) -> None:
        self.runtime_root = runtime_root
        self.lock_dir = ensure_dir(runtime_root / "locks")
        self.pid_dir = ensure_dir(runtime_root / "pid")

    @contextmanager
    def guard(self, task_name: str, run_id: str, run_mode: str) -> Iterator[dict[str, str | int]]:
        """获取运行锁并在退出时自动释放。"""

        payload = self.acquire(task_name=task_name, run_id=run_id, run_mode=run_mode)
        try:
            yield payload
        finally:
            self.release(task_name)

    def acquire(self, task_name: str, run_id: str, run_mode: str) -> dict[str, str | int]:
        """尝试获取运行锁。"""

        lock_path = self.lock_dir / f"{task_name}.lock"
        pid_path = self.pid_dir / f"{task_name}.json"
        payload = {
            "task_name": task_name,
            "run_id": run_id,
            "run_mode": run_mode,
            "pid": os.getpid(),
            "started_at": now_local_iso(),
            "lock_path": str(lock_path),
            "pid_path": str(pid_path),
        }

        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as error:
            existing = read_json(pid_path, {})
            if self._is_stale_lock(existing):
                self._clear_stale_lock(lock_path=lock_path, pid_path=pid_path)
                fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            else:
                raise TaskLockError(
                    f"调度任务已在运行：task={task_name} pid={existing.get('pid', '未知')} run_id={existing.get('run_id', '未知')}"
                ) from error

        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(f"{run_id}\n")
        write_json(pid_path, payload)
        return payload

    def release(self, task_name: str) -> None:
        """释放运行锁。"""

        lock_path = self.lock_dir / f"{task_name}.lock"
        pid_path = self.pid_dir / f"{task_name}.json"
        if lock_path.exists():
            lock_path.unlink()
        if pid_path.exists():
            pid_path.unlink()

    def _is_stale_lock(self, payload: dict) -> bool:
        """判断当前锁是否已经陈旧。"""

        pid = payload.get("pid")
        if not isinstance(pid, int):
            return True
        if not self._pid_is_running(pid):
            return True

        started_at = payload.get("started_at")
        if not isinstance(started_at, str):
            return False

        try:
            started_at_dt = datetime.fromisoformat(started_at)
        except ValueError:
            return False

        # 仅做保守兜底：如果记录时间距今超过 7 天，直接视为陈旧锁。
        return (datetime.now().astimezone() - started_at_dt).total_seconds() > 7 * 24 * 3600

    def _pid_is_running(self, pid: int) -> bool:
        """检查某个 PID 当前是否仍存活。"""

        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    def _clear_stale_lock(self, lock_path: Path, pid_path: Path) -> None:
        """清理已经判定为陈旧的锁文件。"""

        if lock_path.exists():
            lock_path.unlink()
        if pid_path.exists():
            pid_path.unlink()
