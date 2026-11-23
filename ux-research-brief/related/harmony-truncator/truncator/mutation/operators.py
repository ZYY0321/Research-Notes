"""Deterministic ArkUI edits. All numbers are vp unless explicitly named otherwise."""

import json
from pathlib import Path
from truncator.common.storage import digest
from truncator.mutation.operator_strategies import strategy_for

REGISTRY = json.loads(
    Path(__file__).with_name("operators.json").read_text(encoding="utf-8")
)
OPERATORS = list(REGISTRY)
TEXT_OPERATORS = [
    name for name, spec in REGISTRY.items() if spec["mechanism_family"] == "self_text"
]
CONTENT_OPERATORS = [name for name in REGISTRY if name not in TEXT_OPERATORS]
FOREGROUND_OPERATORS = {
    name for name, spec in REGISTRY.items() if spec.get("foreground_calibration", False)
}
UX_OPERATORS = [name for name, spec in REGISTRY.items()
                if spec["task_role"] != "out_of_scope"]
# Edit default_campaign/default_reason in operators.json to change the default pool.
DEFAULT_CAMPAIGN_OPERATORS = [
    name for name, spec in REGISTRY.items()
    if spec.get("default_campaign", False) and name in UX_OPERATORS
]


def mutate(site, operator, parameters):
    if (
        site["repeated"]
        and site.get("probe", {}).get("key_expression")
        and "instance_key" in parameters
    ):
        if not isinstance(parameters["instance_key"], str):
            raise ValueError("Instance key must be text")
        modified = mutate({**site, "repeated": False}, operator, parameters)
        condition = (
            "("
            + site["probe"]["key_expression"]
            + ") === "
            + json.dumps(parameters["instance_key"])
        )
        return (
            "if ("
            + condition
            + ") {\n"
            + modified
            + "\n} else {\n"
            + site["snippet"]
            + "\n}"
        )
    if site["repeated"] and site.get("probe") and "instance_index" in parameters:
        index = parameters["instance_index"]
        if isinstance(index, bool) or not isinstance(index, int) or index < 0:
            raise ValueError("Loop instance index must be a nonnegative integer")
        modified = mutate({**site, "repeated": False}, operator, parameters)
        return (
            "if ("
            + site["probe"]["index_name"]
            + " === "
            + str(index)
            + ") {\n"
            + modified
            + "\n} else {\n"
            + site["snippet"]
            + "\n}"
        )
    return _mutate_single(site, operator, parameters)


def _mutate_single(site, operator, parameters):
    if operator not in site["operators"]:
        raise ValueError("Operator not applicable to " + site["component"])
    if site["repeated"]:
        raise ValueError("Repeated source site requires instance selection")
    if digest(site["snippet"]) != site["sha256"]:
        raise ValueError("Corrupt source-site record")
    return strategy_for(operator).rewrite(site, parameters)
