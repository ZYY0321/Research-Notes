"""Read project manifests and create an explicit local toolchain profile."""

import json
from pathlib import Path
import json5
from truncator.common.storage import read


def load_campaign(filename):
    """Resolve referenced files against the campaign file, not the shell directory."""
    filename = Path(filename).resolve()
    specification = read(filename)
    applications = specification.get("applications", [])
    if not isinstance(applications, list):
        return specification  # The campaign policy owns structural validation.
    for application in applications:
        if not isinstance(application, dict):
            continue
        pages = application.get("pages", [])
        for item in [application, *(pages if isinstance(pages, list) else [])]:
            if not isinstance(item, dict):
                continue
            for key in ("profile", "recipe", "baseline_run"):
                if key not in item:
                    continue
                if not isinstance(item[key], str) or not item[key].strip():
                    raise ValueError(key + " must be a nonempty path")
                path = Path(item[key])
                item[key] = str((path if path.is_absolute() else filename.parent / path).resolve())
    return specification


def profile_from_source(source, studio, module=None):
    source, studio = Path(source).resolve(), Path(studio).resolve()
    build = json5.loads(
        (source / "build-profile.json5").read_text(encoding="utf-8-sig")
    )
    app = json5.loads((source / "AppScope/app.json5").read_text(encoding="utf-8-sig"))[
        "app"
    ]
    entries = []
    for item in build["modules"]:
        manifest = source / item["srcPath"] / "src/main/module.json5"
        if manifest.exists():
            description = json5.loads(manifest.read_text(encoding="utf-8-sig"))[
                "module"
            ]
            if description.get("type") == "entry" and (
                module is None or item["name"] == module
            ):
                entries.append((item, description))
    if len(entries) != 1:
        raise ValueError("Select an unambiguous entry module with --module")
    entry, description = entries[0]
    ability = description.get("mainElement")
    if not ability:
        raise ValueError("Entry module has no mainElement")
    build["app"]["signingConfigs"] = []
    for product in build["app"]["products"]:
        product.pop("signingConfig", None)
        product.update(compatibleSdkVersion="6.0.1(21)", targetSdkVersion="6.1.0(23)")
    sdk = (studio / "sdk").as_posix()
    return {
        "source": str(source),
        "studio": studio.as_posix(),
        "sdk": sdk,
        "node": (studio / "tools/node/node.exe").as_posix(),
        "hdc": sdk + "/default/openharmony/toolchains/hdc.exe",
        "bundle": app["bundleName"],
        "ability": ability,
        "hap": str(
            Path(entry["srcPath"])
            / "build/default/outputs/default"
            / (entry["name"] + "-default-unsigned.hap")
        ),
        "files": {
            "local.properties": "hwsdk.dir=" + sdk + "\n",
            "build-profile.json5": json.dumps(build, ensure_ascii=False, indent=2),
        },
    }
