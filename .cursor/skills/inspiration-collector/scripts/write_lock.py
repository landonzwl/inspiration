#!/usr/bin/env python3
"""Exclusive write lock. Readers must not acquire this lock."""

from __future__ import annotations

import atexit
import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path

from paths import WRITE_LOCK


class WriteLockError(RuntimeError):
    pass


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _read_lock_pid(path: Path) -> int | None:
    try:
        text = path.read_text(encoding="utf-8").strip()
        return int(text.split()[0])
    except (OSError, ValueError, IndexError):
        return None


def acquire(timeout_sec: float = 0.0, stale_sec: float = 3600.0) -> None:
    """Acquire exclusive lock. timeout_sec=0 → fail immediately if busy."""
    WRITE_LOCK.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + max(0.0, timeout_sec)
    while True:
        try:
            fd = os.open(str(WRITE_LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(f"{os.getpid()} {time.time():.3f}\n")
            atexit.register(release)
            return
        except FileExistsError:
            pid = _read_lock_pid(WRITE_LOCK)
            mtime = WRITE_LOCK.stat().st_mtime if WRITE_LOCK.exists() else 0
            stale = (time.time() - mtime) > stale_sec
            if pid is not None and not _pid_alive(pid) or stale:
                try:
                    WRITE_LOCK.unlink(missing_ok=True)
                    continue
                except OSError:
                    pass
            if time.monotonic() >= deadline:
                holder = f"pid={pid}" if pid is not None else "unknown"
                raise WriteLockError(
                    f"write in progress ({holder}); reads are allowed, retry writes later"
                )
            time.sleep(0.05)


def release() -> None:
    try:
        if not WRITE_LOCK.exists():
            return
        pid = _read_lock_pid(WRITE_LOCK)
        if pid is None or pid == os.getpid():
            WRITE_LOCK.unlink(missing_ok=True)
    except OSError:
        pass


@contextmanager
def write_lock(timeout_sec: float = 0.0):
    acquire(timeout_sec=timeout_sec)
    try:
        yield
    finally:
        release()


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "acquire"
    if cmd == "acquire":
        try:
            acquire()
            print(f"OK locked {WRITE_LOCK}")
            return 0
        except WriteLockError as e:
            print(f"BUSY {e}", file=sys.stderr)
            return 1
    if cmd == "release":
        release()
        print("OK released")
        return 0
    if cmd == "status":
        if WRITE_LOCK.exists():
            print(f"LOCKED {_read_lock_pid(WRITE_LOCK)}")
            return 0
        print("FREE")
        return 0
    print("usage: write_lock.py [acquire|release|status]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
