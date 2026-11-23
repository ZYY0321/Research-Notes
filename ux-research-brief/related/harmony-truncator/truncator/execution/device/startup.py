"""Application state preparation and bounded relaunch before route actions."""

import time
from truncator.common.storage import read, save


def process_identity(profile, hdc):
    """Identify a live process including its kernel start time (PID reuse safe)."""
    process = profile.get("process", profile["bundle"])
    pids = hdc("shell", "pidof", process).split()
    if len(pids) != 1 or not pids[0].isdigit():
        raise RuntimeError("Expected one running application process")
    pid = pids[0]
    stat = hdc("shell", "cat", "/proc/" + pid + "/stat")
    # comm is parenthesized and may itself contain spaces or parentheses.
    fields = stat.rsplit(")", 1)[-1].split()
    if not stat.startswith(pid + " (") or len(fields) < 20 or not fields[19].isdigit():
        raise RuntimeError("Application process start time is unavailable")
    return {
        "bundle": profile["bundle"],
        "process": process,
        "pid": int(pid),
        "start_ticks": int(fields[19]),
    }


def continuing_session(profile, recipe, hdc, previous, device, hap_sha256):
    """Validate continuation before executing any route or mutating device state."""
    if recipe.get("reset_app_data", False):
        raise ValueError("A continuing capture requires reset_app_data=false")
    record = read(previous / "capture.json")
    session = record.get("session", {})
    if (
        record.get("status") != "captured"
        or record.get("device") != device
        or record.get("hap_sha256") != hap_sha256
        or session.get("status") != "verified"
    ):
        raise ValueError(
            "Previous capture must identify the same device, HAP and live session"
        )
    current = process_identity(profile, hdc)
    if current != session["process"]:
        raise RuntimeError("Application process changed since previous capture")
    return current


def validate_startup(recipe):
    if not isinstance(recipe.get("reset_app_data", False), bool):
        raise ValueError("reset_app_data must be a boolean")
    attempts = recipe.get("launch_attempts", 2)
    if (
        isinstance(attempts, bool)
        or not isinstance(attempts, int)
        or not 1 <= attempts <= 3
    ):
        raise ValueError("launch_attempts must be an integer in [1,3]")


def launch_application(profile, recipe, hdc, attempt, state, sleep):
    hdc(
        "shell",
        "aa",
        "start",
        "-a",
        profile.get("ability", "EntryAbility"),
        "-b",
        profile["bundle"],
    )
    sleep(recipe.get("settle_seconds", 3))
    output = hdc("shell", "pidof", profile.get("process", profile["bundle"]))
    running = any(part.isdigit() for part in output.split())
    state["launches"].append({"process_running": running, "pid_output": output})
    save(attempt / "initial-state.json", state)
    return running


def retry_exited_application(profile, recipe, hdc, attempt, sleep=time.sleep):
    """Use the remaining launch budget after an initial observation times out."""
    state = read(attempt / "initial-state.json")
    limit = recipe.get("launch_attempts", 2)
    if len(state["launches"]) >= limit:
        return False
    output = hdc("shell", "pidof", profile.get("process", profile["bundle"]))
    if any(part.isdigit() for part in output.split()):
        return False
    state["launches"][-1]["exited_before_first_action"] = True
    while len(state["launches"]) < limit:
        if launch_application(profile, recipe, hdc, attempt, state, sleep):
            return True
    return False


def start_application(profile, recipe, hdc, attempt, sleep=time.sleep):
    validate_startup(recipe)
    bundle = profile["bundle"]
    hdc("shell", "aa", "force-stop", bundle)
    state = {
        "bundle": bundle,
        "data_policy": "clear" if recipe.get("reset_app_data", False) else "preserve",
        "launches": [],
    }
    if recipe.get("reset_app_data", False):
        output = hdc("shell", "bm", "clean", "-n", bundle, "-d")
        state["reset_output"] = output
        save(attempt / "initial-state.json", state)
        if (
            "success" not in output.lower()
            or "error" in output.lower()
            or "fail" in output.lower()
        ):
            raise RuntimeError("Application data reset failed: " + output)
    for _ in range(recipe.get("launch_attempts", 2)):
        if launch_application(profile, recipe, hdc, attempt, state, sleep):
            return
    raise RuntimeError("Application process exited before route replay")
