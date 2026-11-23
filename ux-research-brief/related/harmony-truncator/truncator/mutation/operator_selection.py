"""Operator-specific cut selection; shared rules are composed by the strategy table."""

from dataclasses import dataclass, field
from pathlib import Path
import math
import re
from truncator.source.binding import select_record
from truncator.source.source_attributes import numeric_attribute
from truncator.imaging.geometry import rectangle
from truncator.imaging.visual import content_penetration, adjacent_background

# Engineering priors shared across applications; unchanged from baseline-rules-v9.
FOREGROUND_CUT = (0.15, 0.30, 0.20)
COMPONENT_CUT = (0.25, 0.45, 0.35)
RETAINED_TEXT_WIDTH = (0.55, 0.75, 0.65)


@dataclass(frozen=True)
class SelectionContext:
    baseline: object
    edge: str
    image_path: Path
    measurement: dict | None
    bands: list
    occluder: dict | None = None
    color: str | None = None

    @property
    def box(self): return self.baseline.bounds
    @property
    def horizontal(self): return self.edge in {"left", "right"}
    @property
    def extent(self): return self.box[2] - self.box[0] if self.horizontal else self.box[3] - self.box[1]
    @property
    def measured(self): return self.measurement is not None and self.measurement["status"] == "measured"
    @property
    def content(self): return self.measurement["bounds_px"] if self.measured else self.box
    @property
    def edge_content(self):
        content = list(self.content)
        if self.bands and not self.horizontal:
            band = self.bands[0] if self.edge == "top" else self.bands[-1]
            content[1], content[3] = band
        return content


@dataclass
class Selection:
    cuts: list[float]
    fraction: float
    rule: str
    line_limit: int | None = None
    alignment_bounds: list | None = None
    color: str | None = None
    padding_measurement: dict | None = None
    overlay_measurement: dict | None = None
    overlay_color_source: str | None = None
    assumptions: list[str] = field(default_factory=list)


def initial_selection(context):
    low, high, fraction = FOREGROUND_CUT if context.measured else COMPONENT_CUT
    cuts = [content_penetration(context.box, context.edge_content, context.edge, value)
            for value in (low, high, fraction)]
    is_text = context.baseline.site["component"] == "Text"
    rule = (("edge-line-with-padding" if is_text else "flat-image-foreground")
            if context.measured else "component-relative")
    return Selection(cuts, fraction, rule, color=context.color)


def unchanged(context: SelectionContext, choice: Selection) -> None:
    """Use the common foreground/component cut without an operator override."""


def height(context: SelectionContext, choice: Selection) -> None:
    if context.measured:
        choice.padding_measurement = text_padding(context.baseline)
        bottom = choice.padding_measurement["pixels"]["bottom"]
        choice.cuts = [cut - bottom for cut in choice.cuts]
        choice.rule = "text-content-height-with-padding"
        choice.assumptions.append("text_layout_after_height_change_requires_render_review")


def whitespace(context: SelectionContext, choice: Selection) -> None:
    if not context.measured:
        raise ValueError("Whitespace control requires measurable baseline foreground")
    padding = {"right": context.box[2] - context.content[2], "bottom": context.box[3] - context.content[3]}
    if context.edge not in padding or padding[context.edge] < 4:
        raise ValueError("Whitespace control requires at least four pixels of trailing whitespace")
    choice.cuts = [padding[context.edge] * value for value in (0.25, 0.50, 0.50)]
    choice.fraction = 0.50
    choice.rule = "trailing-whitespace-only"
    choice.assumptions.append("baseline_content_completeness_requires_review")


def retained_width(context: SelectionContext, choice: Selection) -> None:
    if not context.measured:
        return
    try:
        padding = numeric_attribute(context.baseline.site, "padding", ["top", "right", "bottom", "left"])
        padding_width = (padding["left"] + padding["right"]) * context.baseline.density
    except ValueError:
        padding_width = 0
        choice.assumptions.append("dynamic_padding_unresolved")
    width = context.content[2] - context.content[0]
    low, high, choice.fraction = RETAINED_TEXT_WIDTH
    choice.cuts = [context.extent - padding_width - width * value for value in (high, low, choice.fraction)]
    choice.rule = "retained-visible-text-width"


def line_count(context: SelectionContext, choice: Selection) -> None:
    if len(context.bands) < 2:
        raise ValueError("Line-only truncation requires at least two measurable baseline text rows")
    choice.fraction = 0.60
    choice.line_limit = min(len(context.bands) - 1, max(1, math.ceil(len(context.bands) * choice.fraction)))
    choice.cuts = [context.box[3] - context.bands[-2][1], context.box[3] - context.bands[0][1],
                   context.box[3] - context.bands[choice.line_limit - 1][1]]
    choice.rule = "visible-row-count"


def sibling(context: SelectionContext, choice: Selection) -> None:
    choice.alignment_bounds = context.content if context.measured else None
    if context.occluder:
        cover = rectangle(select_record(context.baseline.records, context.occluder["selector"])["attributes"]["bounds"])
        thickness = cover[2] - cover[0] if context.horizontal else cover[3] - cover[1]
        content = context.edge_content
        extent = content[2] - content[0] if context.horizontal else content[3] - content[1]
        padding = choice.cuts[2] - choice.fraction * extent
        choice.cuts = [min(cut, padding + thickness * 0.80) for cut in choice.cuts]
        choice.rule = "sibling-capacity-and-content"


def overlay(context: SelectionContext, choice: Selection) -> None:
    if context.color is None:
        choice.overlay_measurement = (context.measurement if context.measured else adjacent_background(
            context.image_path, context.box, context.edge, context.baseline.density))
        choice.color = "#" + "".join(f"{value:02X}" for value in choice.overlay_measurement["background_rgb"])
        choice.overlay_color_source = "baseline_flat_region" if context.measured else "baseline_adjacent_strip"
    else:
        choice.overlay_color_source = "explicit"


def text_padding(baseline):
    """Resolve source padding in the preserved slot's coordinate system."""
    source = baseline.site.get("padding")
    if source is None:
        value = numeric_attribute(baseline.site, "padding", ["top", "right", "bottom", "left"])
        source = {"status": "resolved", "value": value, "scope": "direct-literal"}
    if source["status"] == "unresolved":
        raise ValueError("Self-height calibration needs resolved padding: " + source["reason"])
    value = source.get("value", 0)
    if not isinstance(value, dict):
        value = {edge: value for edge in ("top", "right", "bottom", "left")}
    if set(value) - {"top", "right", "bottom", "left"}:
        raise ValueError("Unsupported padding sides for self-height calibration")
    width = baseline.bounds[2] - baseline.bounds[0]
    resolved = {}
    for edge in ("top", "right", "bottom", "left"):
        length = value.get(edge, 0)
        if isinstance(length, (float, int)) and not isinstance(length, bool):
            pixels = length * baseline.density
        elif isinstance(length, str):
            match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*(%|vp|px)\s*", length)
            if not match:
                raise ValueError("Unresolved padding unit for self-height calibration")
            pixels = float(match[1]) * {"%": width / 100, "vp": baseline.density, "px": 1}[match[2]]
        else:
            raise ValueError("Unresolved padding value for self-height calibration")
        if not math.isfinite(pixels) or pixels < 0:
            raise ValueError("Invalid padding for self-height calibration")
        resolved[edge] = pixels
    return {"source": source, "pixels": resolved, "percentage_reference_width_px": width}
