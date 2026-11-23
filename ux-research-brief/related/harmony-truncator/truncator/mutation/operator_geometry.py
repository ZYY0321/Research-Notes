"""Mechanism-specific geometry in px, converted to ArkUI vp parameters."""

from dataclasses import dataclass
from truncator.imaging.geometry import crossing_translation, overlap_translation, rectangle
from truncator.source.binding import background_color
from truncator.source.source_attributes import numeric_attribute, effective_attributes


@dataclass(frozen=True)
class Context:
    baseline: object
    relations: object
    cut: float
    edge: str
    color: str | None
    alignment: list | None = None

    @property
    def box(self): return self.baseline.bounds
    @property
    def density(self): return self.baseline.density
    @property
    def width(self): return self.box[2] - self.box[0]
    @property
    def height(self): return self.box[3] - self.box[1]
    @property
    def parent(self): return self.relations.parent_bounds
    @property
    def site(self): return self.baseline.site


def unchanged(c, p):
    pass


def resize(c, p, *, dimension):
    extent = c.width if dimension == "width" else c.height
    p[dimension] = (extent - c.cut) / c.density


def viewport(c, p, *, scroll=False):
    if c.edge not in {"right", "bottom"}:
        raise ValueError("Parent resize uses right/bottom; use translate-clip for left/top")
    resize(c, p, dimension="width" if c.edge == "right" else "height")
    if scroll:
        p["scroll_direction"] = "Horizontal" if c.edge == "right" else "Vertical"
        identifier = "truncator_viewport_" + c.site["id"]
        if any(r["attributes"].get("id") == identifier for r in c.baseline.records):
            raise ValueError("Generated viewport ID collides with a baseline node")
        p["viewport_id"] = identifier


def translate(c, p):
    dx, dy = crossing_translation(c.box, c.parent, c.edge, c.cut)
    p.update(x=dx / c.density, y=dy / c.density)


def frozen_viewport(c, p):
    if c.edge != "right":
        raise ValueError("Frozen viewport width uses the right edge")
    p.update(viewport_width=(c.parent[2] - c.parent[0]) / c.density,
             width_factor=1, expand_container=len(c.relations.sites) > 1)


def mismatched_viewport(c, p):
    if c.edge != "right":
        raise ValueError("Viewport width mismatch uses the right edge")
    offset = c.box[0] - c.parent[0]
    if offset <= 0:
        raise ValueError("Proportional width planning requires a target offset from the viewport left")
    factor = (c.parent[2] - c.parent[0] - c.width + c.cut) / offset
    if factor <= 1:
        raise ValueError("Viewport width mismatch requires a larger viewport")
    p.update(viewport_width=(c.parent[2] - c.parent[0]) * factor / c.density,
             width_factor=factor, expand_container=len(c.relations.sites) > 1)


def window(c, p):
    target = c.baseline.target
    window_id = target["attributes"].get("hostWindowId")
    roots = [node for node in target["ancestors"] if window_id
             and node["attributes"].get("hostWindowId") == window_id
             and node["attributes"].get("type") == "root"]
    if len(roots) != 1:
        raise ValueError("Window clipping requires one same-window root ancestor")
    bounds = rectangle(roots[0]["attributes"]["bounds"])
    dx, dy = crossing_translation(c.box, bounds, c.edge, c.cut)
    parent_site = c.relations.sites[0]["site"]
    previous = numeric_attribute(parent_site, "translate", ["x", "y"])
    p.update(x=previous["x"] + dx / c.density, y=previous["y"] + dy / c.density,
             window_bounds_px=bounds, host_window_id=window_id,
             move_parent=True, translation_delta_px=[dx, dy])
    if any(a["name"] == "translate" for a in effective_attributes(parent_site)):
        p["replace_layout"] = True


def grow(c, p):
    if c.edge not in {"right", "bottom"}:
        raise ValueError("Child growth uses right/bottom")
    dimension, index = ("width", 0) if c.edge == "right" else ("height", 1)
    extent = c.width if index == 0 else c.height
    p["child_" + dimension] = (max(extent, c.parent[index + 2] - c.parent[index]) + 2 * c.cut) / c.density


def overlay(c, p):
    color = c.color if c.color is not None else background_color(c.baseline.target)
    horizontal = c.edge in {"top", "bottom"}
    p.update(color=color, cover_width=(c.width if horizontal else c.cut) / c.density,
             cover_height=(c.cut if horizontal else c.height) / c.density,
             cover_x=(c.width - c.cut) / c.density if c.edge == "right" else 0,
             cover_y=(c.height - c.cut) / c.density if c.edge == "bottom" else 0)


def sibling(c, p, *, positioned=False):
    cover_site = next(item["site"] for item in c.relations.sites if item["role"] == "occluder")
    cover = c.relations.occluder_bounds
    aim = c.alignment or c.box
    padding = ({"left": aim[0] - c.box[0], "right": c.box[2] - aim[2],
                "top": aim[1] - c.box[1], "bottom": c.box[3] - aim[3]}[c.edge]
               if c.alignment is not None else 0)
    dx, dy = overlap_translation(aim, cover, c.edge, max(0.001, c.cut - padding))
    if positioned:
        margin = numeric_attribute(cover_site, "margin", ["top", "right", "bottom", "left"])
        dx += cover[0] - c.parent[0] - margin["left"] * c.density
        dy += cover[1] - c.parent[1] - margin["top"] * c.density
    else:
        old = numeric_attribute(cover_site, "translate", ["x", "y"])
        dx += old["x"] * c.density
        dy += old["y"] * c.density
    p.update(x=dx / c.density, y=dy / c.density,
             z_index=max(float(c.baseline.target["attributes"].get("zIndex") or 0),
                         float(c.relations.occluder["attributes"].get("zIndex") or 0)) + 1)
    if any(a["name"] in {"translate", "position"} for a in effective_attributes(cover_site)):
        p["replace_layout"] = True


def stabilize_text(c, p, *, preserve_height=False):
    if c.site["component"] != "Text":
        raise ValueError("Image self resizing may rescale content; choose fixed-content clipping")
    p["preserve_slot"] = True
    if preserve_height:
        p["preserve_height"] = c.height / c.density


def stabilize_parent(c, p):
    if c.site["component"] == "Image":
        raise ValueError("Unpinned Image may rescale; choose fixed-content clipping")


def stabilize_growth(c, p):
    available = c.parent[2] - c.box[0] if c.edge == "right" else c.parent[3] - c.box[1]
    extent = c.width if c.edge == "right" else c.height
    factor = (available + c.cut) / extent
    if not 1 < factor <= 3:
        raise ValueError("Content growth requires a local parent and a scale in (1, 3]")
    p.update(freeze_parent=True, parent_width=(c.parent[2] - c.parent[0]) / c.density,
             parent_height=(c.parent[3] - c.parent[1]) / c.density,
             child_width=c.width / c.density, child_height=c.height / c.density,
             content_scale=factor)
