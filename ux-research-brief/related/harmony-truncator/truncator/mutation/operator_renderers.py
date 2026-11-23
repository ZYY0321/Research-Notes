"""Small source templates; no runtime measurement or file writes."""

import json
import re
from truncator.mutation.source_edits import (
    pinned, replace_attributes, vector, wrapper_layout,
    reject_layout_conflicts, reject_changed_padding_reference,
)
from truncator.common.validation import positive


def identity(site, p, resets=None):
    return replace_attributes(site, resets or {}, p.get("tracking_id"))


def text_limit(site, p, resets=None, *, overflow, resize):
    lines = p.get("lines", 1)
    if not isinstance(lines, int) or isinstance(lines, bool) or lines < 1:
        raise ValueError("lines must be a positive integer")
    desired = {"maxLines": str(lines), "textOverflow": "{ overflow: TextOverflow." + overflow + " }"}
    if resize:
        desired["width"] = str(positive(p.get("width", 80), "width"))
    return replace_attributes(site, {**desired, **(resets or {})}, p.get("tracking_id"))


def self_clip(site, p, resets=None, *, dimension):
    desired = {dimension: str(positive(p.get(dimension, 12), dimension)), "clip": "true"}
    if dimension == "width" and "preserve_height" in p:
        desired["height"] = str(positive(p["preserve_height"], "preserve_height"))
    return replace_attributes(site, {**desired, **(resets or {})}, p.get("tracking_id"))


def pinned_child(site, p, resets=None, *, translate=False, scale=False):
    desired = {**pinned(site, p), **(resets or {})}
    if translate:
        desired["translate"] = vector(p["x"], p["y"])
    if scale and "content_scale" in p:
        factor = positive(p["content_scale"], "content_scale")
        desired["scale"] = f"{{ x: {factor}, y: {factor}, centerX: '0%', centerY: '0%' }}"
    return replace_attributes(site, desired, p.get("tracking_id"))


def window_target(site, p, resets=None):
    return identity(site, p, resets) if p.get("move_parent") else pinned_child(site, p, resets, translate=True)


def container(site, p, resets=None, *, pin=True, scroll=False, migrate=True, translate=False):
    reject_changed_padding_reference(site, p)
    child_layout, suffix = wrapper_layout(site) if migrate else ({}, "")
    child_layout.update(resets or {})
    child = pinned_child(site, p, child_layout, translate=translate) if pin else identity(site, p, child_layout)
    if p.get("viewport_id"):
        suffix += ".id(" + json.dumps(p["viewport_id"]) + ")"
    width, height = positive(p.get("width", 80), "width"), positive(p.get("height", 12), "height")
    if scroll:
        direction = p.get("scroll_direction", "Horizontal")
        if direction not in {"Horizontal", "Vertical"}:
            raise ValueError("Scroll direction must be Horizontal or Vertical")
        dimension = "width" if direction == "Horizontal" else "height"
        if positive(p["child_" + dimension], "child extent") <= p[dimension]:
            raise ValueError("Scroll content must exceed the viewport")
        return ("Scroll() {\n" + child + "\n}.width(" + str(width)
                + ").height(" + str(height) + ").scrollable(ScrollDirection."
                + direction + ").scrollBar(BarState.Off).clip(true)" + suffix)
    return ("Row() {\n" + child + "\n}.width(" + str(width) + ").height(" + str(height)
            + ").alignItems(VerticalAlign.Top).justifyContent(FlexAlign.Start).clip(true)" + suffix)


def overlay(site, p, resets=None):
    color = p["color"]
    if not isinstance(color, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
        raise ValueError("Opaque overlay color must be #RRGGBB")
    layout, suffix = wrapper_layout(site)
    if p.get("viewport_id"):
        suffix += ".id(" + json.dumps(p["viewport_id"]) + ")"
    child = replace_attributes(site, {**pinned(site, p), **layout, **(resets or {}), "zIndex": "0"}, p.get("tracking_id"))
    block = ("Row() {}.width(" + str(positive(p["cover_width"], "cover_width"))
             + ").height(" + str(positive(p["cover_height"], "cover_height"))
             + ").position(" + vector(p["cover_x"], p["cover_y"]) + ")"
             + ".backgroundColor(" + json.dumps(color) + ").zIndex(1).hitTestBehavior(HitTestMode.None)")
    return ("Stack({ alignContent: Alignment.TopStart }) {\n" + child + "\n" + block
            + "\n}.width(" + str(positive(p.get("width", 80), "width"))
            + ").height(" + str(positive(p.get("height", 12), "height")) + ")" + suffix)


def preserved_slot(site, p, render):
    """Keep the original slot; only strategies that opt in may call this wrapper."""
    reject_layout_conflicts(site, p)
    resets, suffix = wrapper_layout(site)
    modified = render(site, p, resets)
    return ("Row() {\n" + modified + "\n}.width(" + str(positive(p["child_width"], "child_width"))
            + ").height(" + str(positive(p["child_height"], "child_height"))
            + ").alignItems(VerticalAlign.Top).justifyContent(FlexAlign.Start)" + suffix)
