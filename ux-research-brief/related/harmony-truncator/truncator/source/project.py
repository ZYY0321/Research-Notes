"""SDK scanning and isolated project preparation."""

from pathlib import Path
import difflib
import json
import shutil
import subprocess
from truncator.common.storage import save, digest, contained, event
from truncator.mutation.mutations import mutation_patches, apply_patches
from truncator.planning.composition import validate_plan
from truncator.source.source_attributes import style_dependencies

ROOT = Path(__file__).resolve().parent


def scan(profile):
    try:
        result = subprocess.run(
            [profile["node"], str(ROOT / "scan.cjs"), profile["sdk"], profile["source"]],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("SDK source scan timed out after 180 seconds: " + profile["source"]) from error
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace"))
    return json.loads(result.stdout)


def prepare(profile, run, plan=None):
    run = Path(run).resolve()
    source = Path(profile["source"]).resolve()
    if plan:
        if Path(plan["source_root"]).resolve() != source:
            raise ValueError("Plan belongs to a different source project")
        validate_plan(plan)
        for member in plan.get("mutations", [plan]):
            sites = [member["site"]] + [r["site"] for r in member.get("related_sites", [])]
            for site in sites:
                for relative, expected in style_dependencies(site).items():
                    if digest(contained(source, relative).read_bytes()) != expected:
                        raise ValueError("Style dependency changed since scan: " + relative)
    if run.is_relative_to(source) or source.is_relative_to(run):
        raise ValueError("Source and run directories must be disjoint")
    run.mkdir(parents=True, exist_ok=False)
    save(run / "profile.json", profile)
    event(run, "prepare-start", source=str(source))
    try:
        shutil.copytree(
            source,
            run / "project",
            symlinks=False,
            ignore=shutil.ignore_patterns(
                ".git", ".hvigor", "build", ".idea", "screenshots", "oh_modules", "node_modules"
            ),
        )
        # Local toolchain paths are environment adaptations, recorded independently of mutation.
        adaptations = []
        for relative, value in profile.get("files", {}).items():
            path = contained(run / "project", relative)
            previous = path.read_text(encoding="utf-8") if path.exists() else None
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(value, encoding="utf-8")
            adaptations.append({"file": relative, "before": previous, "after": value})
        save(run / "adaptations.json", adaptations)
        if plan:
            patches = plan["patches"] if "mutations" in plan else mutation_patches(plan)
            file_hashes = plan["file_hashes"] if "file_hashes" in plan else {
                plan["site"]["file"]: plan["file_sha256"]
            }
            staged, diffs = {}, []
            for relative in sorted({e["file"] for e in patches}):
                path = contained(run / "project", relative)
                original = path.read_bytes().decode("utf-8")
                if digest(original) != file_hashes[relative]:
                    raise ValueError("Source changed since scan: " + relative)
                updated = apply_patches(
                    original, [e for e in patches if e["file"] == relative]
                )
                staged[path] = updated
                diffs.extend(
                    difflib.unified_diff(
                        original.splitlines(True),
                        updated.splitlines(True),
                        fromfile="a/" + relative,
                        tofile="b/" + relative,
                    )
                )
            # Validate every patch before writing any file in the isolated copy.
            for path, updated in staged.items():
                path.write_bytes(updated.encode("utf-8"))
            save(run / "plan.json", plan)
            (run / "mutation.diff").write_text(
                "".join(diffs),
                encoding="utf-8",
            )
        copied_profile = {**profile, "source": str(run / "project")}
        parsed = scan(copied_profile)
        save(run / "post-scan.json", parsed)
        if plan and any(
            d["file"] in {e["file"] for e in patches} for d in parsed["diagnostics"]
        ):
            raise ValueError("Mutation introduced parse diagnostics")
        save(run / "prepared.json", {"status": "prepared", "baseline": plan is None})
        event(run, "prepared", baseline=plan is None)
    except Exception as error:
        event(run, "prepare-failed", error=str(error))
        raise
