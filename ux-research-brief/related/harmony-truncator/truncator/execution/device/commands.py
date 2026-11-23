"""Logged subprocess execution shared by builds and device commands."""

from pathlib import Path
import subprocess
import time


def command(args, log, cwd=None, env=None, timeout=120):
    started = time.time()
    try:
        result = subprocess.run(
            [str(a) for a in args],
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        Path(log).write_bytes(error.stdout or b"")
        raise RuntimeError("Command timeout, log: " + str(log)) from error
    Path(log).write_bytes(result.stdout)
    output = result.stdout.decode("utf-8", errors="replace")
    if result.returncode or "[Fail]" in output:
        raise RuntimeError("Command failed, log: " + str(log))
    return output, {"seconds": time.time() - started, "returncode": result.returncode}
