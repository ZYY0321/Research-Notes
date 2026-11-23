"""One authoritative image per capture; new acquisitions are native PNG.

Historical JPEG captures stay readable without converting or rewriting evidence.
"""
from pathlib import Path

SNAPSHOT_NAME = "snapshot.png"
TREE_FILES = ("tree-before.json", "tree-after.json")


def capture_image(folder):
    folder = Path(folder)
    candidates = [
        folder / name
        for name in (SNAPSHOT_NAME, "snapshot.jpeg")
        if (folder / name).is_file()
    ]
    if len(candidates) > 1:
        raise ValueError("Capture contains ambiguous PNG and JPEG evidence")
    return candidates[0] if candidates else folder / SNAPSHOT_NAME


def evidence_files(folder):
    return ("capture.json", capture_image(folder).name, *TREE_FILES)
