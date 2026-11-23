"""Independent glyph-mask benchmark for the flat-background measurement heuristic.

This is controlled coverage, not an estimate of the prevalence of real app layouts.
Truth masks come from the font rasterizer before background compositing; the tested
measurement never creates or edits the expected boxes.
"""

import argparse
from collections import defaultdict
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from truncator.imaging.visual import foreground
from truncator.common.storage import save, digest


def render(kind, text, size, centered, font):
    width, height = 360, 96
    mask = Image.new("L", (width, height))
    draw = ImageDraw.Draw(mask)
    face = ImageFont.truetype(font, size)
    box = draw.textbbox((0, 0), text, font=face)
    x = (width - (box[2] - box[0])) // 2 if centered else 16
    draw.text((x, 25), text, font=face, fill=255)
    # Use a predeclared small-alpha cutoff to avoid treating almost invisible AA
    # pixels as the content edge. It is independent of foreground's RGB tolerance.
    truth = mask.point(lambda value: 255 if value >= 32 else 0).getbbox()
    background = Image.new("RGB", (width, height), "white")
    ink = (20, 20, 20)
    rounded = kind in {"rounded", "one-rounded-corner"}
    if rounded:
        background = Image.new("RGB", (width, height), (190, 190, 190))
        painter = ImageDraw.Draw(background)
        painter.rounded_rectangle((0, 0, width - 1, height - 1), radius=24, fill="white")
        if kind == "one-rounded-corner":
            painter.rectangle((24, 0, width - 1, height - 1), fill="white")
            painter.rectangle((0, 24, width - 1, height - 1), fill="white")
    elif kind == "dark":
        background.paste((24, 24, 24), (0, 0, width, height))
        ink = (245, 245, 245)
    elif kind == "low-contrast":
        ink = (230, 230, 230)
    elif kind == "gradient":
        painter = ImageDraw.Draw(background)
        for x_pos in range(width):
            value = 100 + round(155 * x_pos / (width - 1))
            painter.line((x_pos, 0, x_pos, height - 1), fill=(value, value, value))
    elif kind == "decorated":
        ImageDraw.Draw(background).rectangle((300, 12, 340, 80), fill=(50, 100, 180))
    background.paste(ink, (0, 0, width, height), mask)
    return background, mask, list(truth), rounded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--font", default="C:/Windows/Fonts/msyh.ttc")
    args = parser.parse_args()
    root = Path(args.out)
    root.mkdir(parents=True, exist_ok=True)
    cases = []
    groups = ("flat", "dark", "rounded", "one-rounded-corner", "low-contrast", "gradient", "decorated")
    for kind in groups:
        for text in ("Order details", "订单详情与配送时间"):
            for size in (8, 12, 18, 24):
                for centered in (False, True):
                    image, mask, truth, rounded = render(kind, text, size, centered, args.font)
                    name = f"{len(cases):03d}-{kind}"
                    file = root / (name + ".png")
                    image.save(file)
                    mask.save(root / (name + "-truth.png"))
                    predicted = foreground(file, [0, 0, image.width, image.height], exclude_boundary=rounded)
                    measured = predicted["status"] == "measured"
                    error = max(abs(a - b) for a, b in zip(truth, predicted["bounds_px"])) if measured else None
                    cases.append({"id": name, "group": kind, "font_size_px": size, "text": text,
                                  "centered": centered, "image": file.name, "truth_mask": name + "-truth.png",
                                  "truth_bounds_px": truth, "prediction": predicted,
                                  "maximum_edge_error_px": error, "within_2px": measured and error <= 2})
    summary = {}
    for group in groups:
        rows = [row for row in cases if row["group"] == group]
        measured = sum(row["maximum_edge_error_px"] is not None for row in rows)
        accurate = sum(row["within_2px"] for row in rows)
        summary[group] = {"total": len(rows), "measured": measured, "within_2px": accurate,
                          "incorrect_measurements": measured - accurate,
                          "coverage": measured / len(rows),
                          "accuracy_among_measured": accurate / measured if measured else None}
    save(root / "results.json", {"font": args.font, "font_sha256": digest(Path(args.font).read_bytes()),
                                 "truth": "independent glyph alpha >= 32", "tolerance_px": 2,
                                 "scope": "controlled rendered text; not a real-app accuracy estimate",
                                 "summary": summary, "cases": cases})
    for group, row in summary.items():
        print(group, row, flush=True)


if __name__ == "__main__":
    main()
