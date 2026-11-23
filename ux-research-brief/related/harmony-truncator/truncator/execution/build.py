"""Verify prepared sources, install dependencies and build one HAP."""

from pathlib import Path
import os
import time
from truncator.execution.device.commands import command
from truncator.common.storage import read, save, digest, event
from truncator.common.locking import lock


def install_dependencies(args, attempt, run, env, retries=1):
    """Retry recognized transient network failures, retaining each command log."""
    if isinstance(retries, bool) or not isinstance(retries, int) or not 0 <= retries <= 2:
        raise ValueError("dependency_retries must be an integer from 0 to 2")
    transient = ("ECONNRESET", "ETIMEDOUT", "EAI_AGAIN", "ECONNREFUSED", "ENETUNREACH")
    for number in range(retries + 1):
        log = attempt / ("dependencies.log" if number == 0 else f"dependencies-retry-{number}.log")
        try:
            command(args, log, run / "project", env, 180)
            return
        except RuntimeError:
            output = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
            reason = next((code for code in transient if code in output), None)
            if number == retries or reason is None:
                raise
            event(run, "dependency-retry", number=number + 1, reason=reason, log=str(log))
            time.sleep(1 + number)


def build(profile, run):
    run = Path(run)
    if read(run / "profile.json") != profile or not (run / "prepared.json").exists():
        raise ValueError("Run is not prepared with this profile")
    for relative, expected in read(run / "post-scan.json")["files"].items():
        if digest((run / "project" / relative).read_bytes()) != expected:
            raise ValueError("Source changed after preparation: " + relative)
    with lock(run / "build.lock"):
        env = os.environ.copy()
        env["JAVA_HOME"] = profile["studio"] + "/jbr"
        env["DEVECO_SDK_HOME"] = profile["sdk"]
        env["PATH"] = (
            str(Path(profile["node"]).parent) + os.pathsep + env.get("PATH", "")
        )
        attempt = run / ("build-" + str(time.time_ns()))
        attempt.mkdir()
        args = [
            profile["node"],
            profile["studio"] + "/tools/hvigor/bin/hvigorw.js",
            "--mode",
            "module",
            "-p",
            "product=" + profile.get("product", "default"),
            "assembleHap",
            "--no-daemon",
        ]
        event(run, "build-start", command=args)
        try:
            dependency_args = [
                profile["node"],
                profile["studio"] + "/tools/ohpm/bin/pm-cli.js",
                "install",
            ]
            install_dependencies(dependency_args, attempt, run, env,
                                 profile.get("dependency_retries", 1))
            _, result = command(
                args,
                attempt / "build.log",
                run / "project",
                env,
                profile.get("build_timeout", 600),
            )
            hap = run / "project" / profile["hap"]
            if not hap.is_file():
                raise RuntimeError("Expected HAP missing: " + str(hap))
            result["hap_sha256"] = digest(hap.read_bytes())
            result["attempt"] = attempt.name
            save(run / "build.json", result)
            event(run, "built", **result)
        except Exception as error:
            event(run, "build-failed", error=str(error))
            raise
