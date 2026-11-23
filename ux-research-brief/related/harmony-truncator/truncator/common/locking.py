"""Process-scoped OS locks, released by the kernel even after forced termination."""

from contextlib import contextmanager
from pathlib import Path
import json
import os
import time


def process_alive(pid):
    if not isinstance(pid, int) or pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.WaitForSingleObject.restype = wintypes.DWORD
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x00100000, False, pid)
        if not handle:
            return ctypes.get_last_error() != 87  # Invalid PID, otherwise conservative.
        try:
            return kernel.WaitForSingleObject(handle, 0) != 0
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


@contextmanager
def lock(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Keep the inode/file in place. Unlinking it would permit competing lock files.
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    with os.fdopen(descriptor, "r+b", buffering=0) as stream:
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise FileExistsError(
                "Lock is held by another process: " + str(path)
            ) from error
        try:
            try:
                owner = json.loads(stream.read().decode("utf-8"))
            except (ValueError, UnicodeError):
                owner = {}
            # Recognize valid lock records created by older releases.
            if (
                isinstance(owner, dict)
                and owner.get("protocol") != "kernel-v1"
                and process_alive(owner.get("pid"))
            ):
                raise FileExistsError(
                    "Legacy lock owner is still running: " + str(path)
                )
            metadata = {
                "protocol": "kernel-v1",
                "pid": os.getpid(),
                "time": time.time(),
            }
            stream.seek(0)
            stream.write(json.dumps(metadata).encode("utf-8"))
            stream.truncate()
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
