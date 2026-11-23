"""Publish complete exports atomically and retain interrupted attempts for diagnosis."""

from contextlib import contextmanager
from pathlib import Path
import uuid

from truncator.common.storage import read, save
from truncator.common.locking import lock


def export_state_path(destination):
    destination = Path(destination).resolve()
    return destination.with_name("." + destination.name + ".export-state.json")


@contextmanager
def export_transaction(runs, destination):
    destination = Path(destination).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    state_path = export_state_path(destination)
    with lock(state_path.with_suffix(".lock")):
        token = uuid.uuid4().hex
        if destination.exists():
            status = destination / "export-status.json"
            if not status.is_file() or read(status).get("complete") is not False:
                raise FileExistsError(
                    "Export destination already exists: " + str(destination)
                )
            # Preserve old incomplete exports without merging their files into a retry.
            archive = destination.with_name(
                "." + destination.name + ".incomplete-" + token
            )
            if archive.parent != destination.parent:
                raise ValueError("Incomplete export archive escapes destination parent")
            destination.rename(archive)
        staging = destination.with_name("." + destination.name + ".export-" + token)
        staging.mkdir()
        state = {
            "runs": str(Path(runs).resolve()),
            "destination": str(destination),
            "staging": str(staging),
            "status": "running",
            "complete": False,
        }
        save(state_path, state)
        save(staging / "export-attempt.json", state)
        try:
            yield staging
            if read(staging / "export-status.json").get("complete") is not True:
                raise RuntimeError("Export writer did not finish the dataset")
            state.update(status="complete", complete=True)
            save(staging / "export-attempt.json", state)
            staging.rename(destination)
        except BaseException as error:
            state.update(status="failed", complete=False, error=str(error))
            try:
                save(state_path, state)
                if staging.exists():
                    save(staging / "export-attempt.json", state)
            except OSError:
                pass  # A full disk must not hide the original copy/publish error.
            raise
        try:
            save(state_path, state)
        except OSError:
            pass  # The published directory contains the authoritative complete status.
