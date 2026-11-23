"""Resolve explicit operator selections and reject scope errors before execution."""

import math
from truncator.mutation.operators import REGISTRY, UX_OPERATORS, DEFAULT_CAMPAIGN_OPERATORS


def effective_page(application, page):
    result = {key: value for key, value in application.items() if key != "pages"}
    if any(key in page for key in ("operator", "operators", "cases")):
        for key in ("operator", "operators", "cases"):
            result.pop(key, None)
    result.update(page)
    return result


def selected_operators(page, mode):
    if "operator" in page and "operators" in page:
        raise ValueError("Specify operator or operators, not both")
    if mode != "combined":
        raise ValueError("Only combined campaign mode is supported; use max_total=1 for one target")
    if "cases" in page:
        raise ValueError("Combined pages use operator(s) and file filters, not cases")
    values = page.get("operators", [page["operator"]] if "operator" in page else list(DEFAULT_CAMPAIGN_OPERATORS))
    if not isinstance(values, list) or not values or any(not isinstance(v, str) for v in values):
        raise ValueError("operators must be a nonempty list of names")
    for name in values:
        if name not in REGISTRY:
            raise ValueError("Unknown construction operator: " + name)
        if name not in UX_OPERATORS:
            raise ValueError("Operator is outside UX-Agent truncation scope: " + name)
    if mode == "combined" and len(set(values)) != len(values):
        raise ValueError("Duplicate operators would distort candidate balance")
    return list(dict.fromkeys(values))


def validate_campaign(specification):
    applications = specification.get("applications")
    if not isinstance(applications, list) or not applications:
        raise ValueError("Campaign requires a nonempty applications list")
    audit = []
    for index, application in enumerate(applications):
        if not isinstance(application, dict):
            raise ValueError("Each campaign application must be an object")
        mode = application.get("mode", "combined")
        if mode != "combined":
            raise ValueError("Only combined campaign mode is supported")
        for key in ("max_total", "max_per_page"):
            value = application.get(key, 1)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(key + " must be a positive integer")
        area = application.get("max_area_ratio", 0.3)
        if isinstance(area, bool) or not isinstance(area, (int, float)) or not math.isfinite(area) or not 0 < area <= 1:
            raise ValueError("max_area_ratio must be in (0, 1]")
        if "instrument" in application and not isinstance(application["instrument"], bool):
            raise ValueError("instrument must be boolean")
        if "verify_recovery" in application and not isinstance(application["verify_recovery"], bool):
            raise ValueError("verify_recovery must be boolean")
        if "pages" in application and "cases" in application:
            raise ValueError("Combined applications use pages with operator(s), not cases")
        pages = application.get("pages", [application])
        if not isinstance(pages, list) or not pages:
            raise ValueError("pages must be a nonempty list")
        for page_index, page in enumerate(pages):
            if not isinstance(page, dict):
                raise ValueError("Each campaign page must be an object")
            if "pages" in application:
                application_only = {"profile", "baseline_run", "instrument", "verify_recovery",
                                    "max_total", "max_per_page", "max_area_ratio", "seed", "mode", "pages"}
                misplaced = sorted(application_only.intersection(page))
                if misplaced:
                    raise ValueError("Application-only fields cannot be set on a page: " + ", ".join(misplaced))
            names = selected_operators(effective_page(application, page), mode)
            audit.append({"application_index": index, "page_index": page_index, "mode": mode,
                          "operators": names})
    return {"pages": audit, "default_operators": list(DEFAULT_CAMPAIGN_OPERATORS),
            "label_policy": "Content and recovery labels are assigned from observed results and review."}
