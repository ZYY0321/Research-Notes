"""Choose and persist one buildable source baseline for a campaign application."""

from pathlib import Path
import time

from truncator.execution.build import build
from truncator.source.instrumentation import instrument
from truncator.source.project import prepare, scan
from truncator.common.storage import digest, read, save


def prepare_baseline(profile, baseline):
    """Resume a prepared baseline; quarantine interrupted preparation in place."""
    baseline = Path(baseline)
    if baseline.exists():
        saved = baseline / "profile.json"
        if saved.exists() and read(saved) != profile:
            raise ValueError("Baseline profile changed")
        if not (baseline / "prepared.json").exists():
            if (baseline / "build.json").exists() or list(baseline.glob("capture-*/capture.json")):
                raise ValueError("Prepared record missing from a completed baseline")
            backup = baseline.with_name(baseline.name + "-incomplete-" + str(time.time_ns()))
            baseline.rename(backup)
    if not baseline.exists():
        prepare(profile, baseline)
    if not (baseline / "build.json").exists():
        build(profile, baseline)
    if profile.get("hap"):
        hap = baseline / "project" / profile["hap"]
        if digest(hap.read_bytes()) != read(baseline / "build.json")["hap_sha256"]:
            raise ValueError("Baseline HAP differs from saved build record")


def prepare_application(profile, application, folder):
    """Instrument by default; fall back once if instrumentation or its build fails.

    A saved source decision is immutable on resume. Original and instrumented
    baseline directories are separate, so fallback never reuses the wrong HAP.
    """
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    state_path = folder / "source-choice.json"
    enabled = application.get("instrument", True)
    if not isinstance(enabled, bool):
        raise ValueError("instrument must be boolean")
    request = {"profile": profile, "instrument": enabled,
               "baseline_run": application.get("baseline_run")}
    if state_path.exists():
        state = read(state_path)
        if state["request"] != request:
            raise ValueError("Campaign source selection changed; use a new run directory")
        chosen, baseline = state["profile"], Path(state["baseline"])
        catalog = scan(chosen)
        if catalog["files"] != state["source_files"]:
            raise ValueError("Selected campaign source changed; use a new run directory")
        prepare_baseline(chosen, baseline)
        return chosen, catalog, baseline

    chosen = profile
    reason = None
    baseline = Path(application.get("baseline_run", folder / "baseline-original"))
    # Explicit existing baselines and already instrumented profiles have their own
    # source identity. Do not silently generate an incompatible second copy.
    mode = "existing" if application.get("baseline_run") or profile.get("instrumentation") else "original"
    if enabled and mode == "original":
        trace = folder / ("instrumented-" + str(time.time_ns()))
        try:
            candidate = instrument(profile, trace)
            candidate_baseline = folder / ("baseline-" + trace.name)
            prepare_baseline(candidate, candidate_baseline)
            chosen, baseline, mode = candidate, candidate_baseline, "instrumented"
        except (ValueError, OSError, RuntimeError, KeyError) as error:
            reason = {"stage": "instrumentation_or_build", "error": str(error), "attempt": str(trace)}
            save(folder / "instrumentation-failure.json", reason)
            mode = "original-fallback"
    if mode != "instrumented":
        prepare_baseline(chosen, baseline)
    catalog = scan(chosen)
    save(state_path, {"request": request, "mode": mode, "profile": chosen,
                      "baseline": str(baseline.resolve()), "source_files": catalog["files"],
                      "fallback": reason})
    save(folder / "effective-profile.json", chosen)
    return chosen, catalog, baseline
