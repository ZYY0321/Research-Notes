"""Operator strategies: cut selection, parameterization, stability and rendering.

Adding a selection rule or template uses this table instead of extending name
switches in the shared entry points. Geometry and wrappers remain reusable functions.
"""

from dataclasses import dataclass
from functools import partial
from typing import Callable

import truncator.mutation.operator_geometry as geometry
import truncator.mutation.operator_renderers as render
import truncator.mutation.operator_selection as selection
from truncator.source.source_attributes import effective_attributes


@dataclass(frozen=True)
class OperatorStrategy:
    parameterize: Callable
    render: Callable
    stabilize: Callable = geometry.unchanged
    supports_slot: bool = False
    resolve_image_ratio: bool = True
    relation: str | None = None
    expand_viewport_parent: bool = False
    select: Callable[[selection.SelectionContext, selection.Selection], None] = selection.unchanged
    measure_any_component: bool = False

    def parameters(self, context, stabilize=False):
        c = context
        p = {"child_width": c.width / c.density, "child_height": c.height / c.density,
             "width": c.width / c.density, "height": c.height / c.density, "lines": 1}
        if c.baseline.tracking_id:
            p["tracking_id"] = c.baseline.tracking_id
        self.parameterize(c, p)
        if stabilize:
            self.stabilize(c, p)
            if (self.resolve_image_ratio and c.site["component"] == "Image"
                    and any(a["name"] == "aspectRatio" for a in effective_attributes(c.site))):
                p["resolved_aspect_ratio"] = c.width / c.height
        return p

    def rewrite(self, site, parameters):
        if parameters.get("preserve_slot"):
            if not self.supports_slot:
                raise ValueError("Slot preservation requires a self clipping operator")
            return render.preserved_slot(site, parameters, self.render)
        return self.render(site, parameters)


STRATEGIES = {
    "line-clip": OperatorStrategy(partial(geometry.resize, dimension="width"),
        partial(render.text_limit, overflow="Clip", resize=True), geometry.stabilize_text, True, select=selection.retained_width),
    "ellipsis-width": OperatorStrategy(partial(geometry.resize, dimension="width"),
        partial(render.text_limit, overflow="Ellipsis", resize=True), geometry.stabilize_text, True, select=selection.retained_width),
    "ellipsis-lines": OperatorStrategy(geometry.unchanged,
        partial(render.text_limit, overflow="Ellipsis", resize=False), geometry.stabilize_text, True, select=selection.line_count),
    "height-clip": OperatorStrategy(partial(geometry.resize, dimension="height"),
        partial(render.self_clip, dimension="height"), geometry.stabilize_text, True, select=selection.height),
    "width-clip": OperatorStrategy(partial(geometry.resize, dimension="width"),
        partial(render.self_clip, dimension="width"), partial(geometry.stabilize_text, preserve_height=True), True, select=selection.retained_width),
    "parent-clip": OperatorStrategy(geometry.viewport,
        partial(render.container, pin=False, migrate=False), geometry.stabilize_parent),
    "fixed-parent-clip": OperatorStrategy(geometry.viewport, render.container),
    "scroll-recovery": OperatorStrategy(partial(geometry.viewport, scroll=True), partial(render.container, scroll=True)),
    "whitespace-clip": OperatorStrategy(geometry.viewport, render.container, select=selection.whitespace),
    "translate-clip": OperatorStrategy(geometry.translate, partial(render.container, translate=True)),
    "ancestor-translate-clip": OperatorStrategy(geometry.translate, partial(render.pinned_child, translate=True), relation="clipping_parent"),
    "child-overflow-clip": OperatorStrategy(geometry.grow, partial(render.pinned_child, scale=True), geometry.stabilize_growth, relation="clipping_parent"),
    "window-edge-clip": OperatorStrategy(geometry.window, render.window_target, relation="window_parent"),
    "viewport-width-mismatch": OperatorStrategy(geometry.mismatched_viewport, render.identity, relation="viewport", expand_viewport_parent=True),
    "freeze-viewport-width": OperatorStrategy(geometry.frozen_viewport, render.identity, relation="viewport", expand_viewport_parent=True),
    "cache-viewport-width": OperatorStrategy(geometry.frozen_viewport, render.identity, relation="viewport"),
    "overlay-occlusion": OperatorStrategy(geometry.overlay, render.overlay, select=selection.overlay, measure_any_component=True),
    "sibling-translate-occlusion": OperatorStrategy(geometry.sibling, render.identity, resolve_image_ratio=False, relation="sibling", select=selection.sibling),
    "sibling-position-occlusion": OperatorStrategy(partial(geometry.sibling, positioned=True), render.identity, resolve_image_ratio=False, relation="positioned_sibling", select=selection.sibling),
}


def strategy_for(operator):
    try:
        return STRATEGIES[operator]
    except KeyError as error:
        raise ValueError("Unknown construction operator: " + str(operator)) from error
