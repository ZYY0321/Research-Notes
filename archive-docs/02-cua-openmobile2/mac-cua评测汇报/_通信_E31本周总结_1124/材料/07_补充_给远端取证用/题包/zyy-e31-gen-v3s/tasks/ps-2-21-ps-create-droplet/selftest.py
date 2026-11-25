import json, os, plistlib, shutil, tempfile
import evaluation
import fixturelib as F


def reset(path):
    if os.path.lexists(path):
        if os.path.isdir(path) and not os.path.islink(path):
            shutil.rmtree(path)
        else:
            os.remove(path)


def write_app(path, info, exe):
    reset(path)
    macos = os.path.join(path, "Contents", "MacOS")
    os.makedirs(macos)
    with open(os.path.join(macos, exe), "wb") as handle:
        handle.write(b"\x00")
    with open(os.path.join(path, "Contents", "Info.plist"), "wb") as handle:
        plistlib.dump(info, handle)


def main():
    results = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(dict(evaluation.PARAMS), directory)
        out = params["path"]
        if not str(out).startswith(directory):
            raise SystemExit("path escaped the temp directory")
        reset(out)
        results.append(F.case("empty", params, 0))
        F.write(out, b"Photoshop")
        results.append(F.case("shortcut", params, 0))
        write_app(out, {"CFBundlePackageType": "APPL", "CFBundleSignature": "8BIM", "CFBundleExecutable": "Droplet", "CFBundleName": "E31 Droplet"}, "Droplet")
        results.append(F.case("reference", params, 1))
        write_app(out, {"CFBundlePackageType": "APPL", "CFBundleExecutable": "Helper", "CFBundleName": "Helper"}, "Helper")
        results.append(F.case("near_miss", params, 0))
        write_app(out, {"CFBundlePackageType": "BNDL", "CFBundleSignature": "8BIM", "CFBundleExecutable": "Droplet", "CFBundleName": "Photoshop"}, "Droplet")
        results.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": results}, ensure_ascii=False))


if __name__ == "__main__":
    main()
