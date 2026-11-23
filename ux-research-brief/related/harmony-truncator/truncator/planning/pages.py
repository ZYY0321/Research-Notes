"""Resolve page identity independently of replay timing and capture settings."""

EXECUTION_OPTIONS = {
    "settle_seconds",
    "poll_interval",
    "selector_timeout",
    "checkpoint_timeout",
    "launch_attempts",
    "image_check",
    "allowed_severity",
}
ACTION_TIMING = {"wait", "selector_timeout", "checkpoint_timeout", "stable_samples"}


def page_id(page):
    return page.get("page_id") or page["recipe"].get("page_id") or page["name"]


def route_identity(recipe):
    """Legacy matching keeps navigation, data reset and checkpoints significant."""
    identity = {
        k: v for k, v in recipe.items() if k not in EXECUTION_OPTIONS | {"page_id"}
    }
    for key in ("setup_actions", "actions"):
        if key in identity:
            identity[key] = [
                {k: v for k, v in action.items() if k not in ACTION_TIMING}
                for action in identity[key]
            ]
    return identity


def resolve_page(plan, recipe):
    pages = plan.get("pages", [])
    identifier = recipe.get("page_id")
    if "page_id" in recipe and (
        not isinstance(identifier, str) or not identifier.strip()
    ):
        raise ValueError("page_id must be a nonempty string")
    if identifier is not None:
        matches = [page for page in pages if page_id(page) == identifier]
        if not matches:
            raise ValueError("Unknown page_id: " + identifier)
    else:
        matches = [page for page in pages if page["recipe"] == recipe]
        if not matches:
            identity = route_identity(recipe)
            matches = [
                page for page in pages if route_identity(page["recipe"]) == identity
            ]
    if len(matches) > 1:
        raise ValueError("Ambiguous page identity; specify page_id")
    return matches[0] if matches else None
