import json, tempfile
import evaluation
import fixturelib as F


def make_jpeg(width, height, color):
    candidates = []
    solid = getattr(F, "solid", None)
    if solid is not None:
        candidates.append(lambda: solid(width, height, color, fmt="jpeg"))
        candidates.append(lambda: solid(width, height, color, kind="jpeg"))
    for name in ("jpeg", "solid_jpeg", "jpeg_solid"):
        fn = getattr(F, name, None)
        if fn is not None:
            candidates.append(lambda fn=fn: fn(width, height, color))
    for attempt in candidates:
        try:
            data = attempt()
            if isinstance(data, (bytes, bytearray)) and bytes(data[:2]) == b"\xff\xd8":
                return bytes(data)
        except Exception:
            pass
    import io
    from PIL import Image
    img = Image.new("RGB", (width, height), tuple(color))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=95)
    return buf.getvalue()


def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        width, height = params["width"], params["height"]
        color = (200, 10, 10)
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, b"not really a jpeg file")
        cases.append(F.case("shortcut", params, 0))
        F.write(out, make_jpeg(width, height, color))
        cases.append(F.case("reference", params, 1))
        F.write(out, F.solid(width, height, color, rgba=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, make_jpeg(height, width, color))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
