"""Adversarial sanity check for every task's verifier: does "the agent did
literally nothing" correctly fail?

This directly answers the single most important correctness question about a
verifier, without running any agent and without needing to understand each
task's specific business logic: **if ``last_obs`` is byte-for-byte identical
to ``init_obs`` (no tool call, no GUI write, no answer), must every task's
``check_goals`` report failure?**

Any task where this negative-control fixture reports success is a leaking
verifier -- it would inflate a run's success rate independent of what the
agent actually did, and any conclusion drawn from that number (tool vs GUI
comparison, SR calibration, RL reward signal) would be unreliable. This is
exactly the class of bug the user is most worried about: "验证任务可完成是
可以用的" -- we need proof the verifier *requires* completion, not just that
successful runs happen to score high.

This is a necessary-but-not-sufficient check: passing it proves the verifier
is not trivially-satisfiable; it does NOT prove the verifier is not
over-strict (see 04-难度升级与跨App设计备忘.md §0's ctrip_v4_07/dianping_v4_07
false-negative cases, which need a *positive*, differently-phrased fixture
instead -- that is the next script to write, see the design memo for scope).

Usage:
    python bench_env/task/hybrid_tools_selfbuilt_v1/verifier_noop_audit.py [suite_name ...]
    # defaults to hybrid_tools_selfbuilt_v4
"""

from __future__ import annotations

import copy
import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any

MOBILEGYM_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(MOBILEGYM_ROOT))

from bench_env.env.base import Observation  # noqa: E402
from bench_env.task.judge import JudgeInput  # noqa: E402

# Same source-of-truth mapping used by tool_state_consistency_audit.py.
APP_DEFAULTS = {
    "ctrip": "apps/Ctrip/data/defaults.json",
    "taobao": "apps/Taobao/data/defaults.json",
    "jingdong": "apps/Jingdong/data/defaults.json",
    "dianping": "apps/Dianping/data/defaults.json",
    "kapi": "apps/Kapi/data/defaults.json",
    "broadcast": "apps/Broadcast/data/defaults.json",
    "dida": "apps/Dida/data/defaults.json",
    "slack": "apps/Slack/data/defaults.json",
    "mail": "apps/Mail/data/defaults.json",
    "googledrive": "apps/GoogleDrive/data/defaults.json",
}

# defs/specs_<app>.py modules to scan per suite. Every file in a suite's
# defs/ directory that defines SPECS + (optionally) EXTRA_CHECKS is covered.
SUITE_DEFS_DIR = "defs"


def _load_app_state(app: str) -> dict[str, Any]:
    if app in APP_DEFAULTS:
        return json.loads((MOBILEGYM_ROOT / APP_DEFAULTS[app]).read_text(encoding="utf-8"))
    # Apps without a defaults.json in APP_DEFAULTS (e.g. "notes", "daysmatter")
    # get an empty-but-present placeholder: correct for the no-op test, since
    # init == curr regardless of what's inside; goals only care about the
    # *diff* between them, which is empty either way.
    return {}


def _build_judge_input(spec, no_op: bool) -> JudgeInput:
    del no_op  # reserved for a future positive-fixture variant
    apps_state = {app: _load_app_state(app) for app in spec.apps}
    init_obs = Observation(state={"apps": copy.deepcopy(apps_state)}, route={"app": spec.apps[0] if spec.apps else "", "path": "/"})
    last_obs = Observation(state={"apps": copy.deepcopy(apps_state)}, route={"app": spec.apps[0] if spec.apps else "", "path": "/"})
    return JudgeInput(init_obs=init_obs, last_obs=last_obs, answer=None)


def _build_positive_fixture_or_none(spec) -> JudgeInput | None:
    """Auto-derive an "obviously correct" fixture: synthesize a brand-new note
    for every ``notes_note`` goal (title/fields matched exactly, content just
    the literal concatenation of that goal's own ``contains`` tokens), then
    additionally apply this task's hand-built ``POSITIVE_FIXTURES`` mutator
    (if any) to satisfy its ``extra_check``. Returns None only when a task has
    goal kinds this harness cannot auto-satisfy (non-``notes_note``) AND no
    registered fixture -- i.e. truly not covered yet.

    This does NOT prove the verifier accepts realistically-phrased answers
    (that needs task-specific fixtures, see the design memo) -- it proves the
    weaker but still load-bearing property that the verifier's own
    contains/not_contains/fields/state-diff conditions are *mutually
    satisfiable at all* (e.g. would catch a typo'd token that is
    simultaneously in both ``contains`` and ``not_contains``, or a state-diff
    condition that no realizable state could ever match).
    """
    has_fixture = spec.task_id in POSITIVE_FIXTURES
    if not all(g.kind == "notes_note" for g in spec.goals) and not has_fixture:
        return None
    apps_state = {app: _load_app_state(app) for app in spec.apps}
    init_apps = copy.deepcopy(apps_state)
    curr_apps = copy.deepcopy(apps_state)
    curr_apps.setdefault("notes", {}).setdefault("notes", [])
    init_apps.setdefault("notes", {}).setdefault("notes", [])
    for idx, g in enumerate(spec.goals):
        if g.kind != "notes_note":
            continue
        v = g.values
        contains = list(v.get("contains") or [])
        note = {
            "id": f"__positive_fixture_{spec.task_id}_{idx}",
            "title": v.get("title", ""),
            "content": " ".join(str(token) for token in contains),
            **dict(v.get("fields") or {}),
        }
        curr_apps["notes"]["notes"].append(note)
    if has_fixture:
        POSITIVE_FIXTURES[spec.task_id](init_apps, curr_apps)
    init_obs = Observation(state={"apps": init_apps}, route={"app": "notes", "path": "/"})
    last_obs = Observation(state={"apps": curr_apps}, route={"app": "notes", "path": "/"})
    return JudgeInput(init_obs=init_obs, last_obs=last_obs, answer=None)


# ---------------------------------------------------------------------------
# Hand-built positive fixtures for every task registered in some suite's
# EXTRA_CHECKS (state-diff verifiers with task-specific business logic that
# cannot be inferred generically the way notes_note's contains/fields can).
# Each entry was derived by reading the exact extra_check closure for that
# task_id (see the four `specs_*.py` files this was sourced from) and is a
# ``(apps_init, apps_curr) -> None`` mutator that makes the closure's own
# condition true. This is the other half of the "验证任务可完成是可以用的"
# guarantee: not just "no-op fails", but "the actual right state change
# passes", proven per-task rather than assumed from a passing agent run.
# ---------------------------------------------------------------------------

def _epoch_ms(year: int, month: int, day: int) -> float:
    import datetime as _dt
    return _dt.datetime(year, month, day, tzinfo=_dt.timezone.utc).timestamp() * 1000


def _set(apps: dict, app: str, field: str, value: Any) -> None:
    apps.setdefault(app, {})[field] = value


def _append(apps: dict, app: str, field: str, row: dict[str, Any]) -> None:
    apps.setdefault(app, {}).setdefault(field, [])
    apps[app][field] = list(apps[app][field] or []) + [row]


def _patch_by_id(apps: dict, app: str, field: str, item_id: str, **patch: Any) -> None:
    rows = list(apps.get(app, {}).get(field) or [])
    apps.setdefault(app, {})[field] = [
        {**row, **patch} if isinstance(row, dict) and str(row.get("id")) == item_id else row
        for row in rows
    ]


POSITIVE_FIXTURES: dict[str, Any] = {
    # -- v1 --
    "broadcast_03_bubble_addqueue": lambda i, c: (_set(i, "broadcast", "queueIds", []), _set(c, "broadcast", "queueIds", ["e_42_bubble"])),
    "broadcast_08_openclaw_addqueue": lambda i, c: (_set(i, "broadcast", "queueIds", []), _set(c, "broadcast", "queueIds", ["e_42_openclaw"])),
    "broadcast_09_minimax_dual_addqueue": lambda i, c: (_set(i, "broadcast", "queueIds", []), _set(c, "broadcast", "queueIds", ["e_latetalk_minimax", "e_crossing_minimax"])),
    "dianping_05_favorite_night_snack": lambda i, c: (_set(i, "dianping", "favoriteShopIds", []), _set(c, "dianping", "favoriteShopIds", ["wuyuesi"])),
    "dianping_06_coffee_voucher_draft": lambda i, c: _set(c, "dianping", "pendingCheckout", {"shopId": "luckin", "dealId": "lk1", "qty": 3}),
    "dianping_07_bbq_party_voucher_draft": lambda i, c: _set(c, "dianping", "pendingCheckout", {"shopId": "bbqking", "dealId": "bb1", "qty": 2}),
    "dianping_08_favorite_top_score_pick": lambda i, c: (_set(i, "dianping", "favoriteShopIds", []), _set(c, "dianping", "favoriteShopIds", ["sushiya"])),
    "jingdong_05_appliance_guobu_addcart": lambda i, c: _set(c, "jingdong", "cart", [{"itemId": "i_hairdryer", "qty": 1}]),
    "jingdong_06_xianyonghoufu_cheapest_addcart": lambda i, c: _set(c, "jingdong", "cart", [{"itemId": "i_huangtao", "qty": 1}]),
    "jingdong_07_phone_cheap_unique_addcart": lambda i, c: _set(c, "jingdong", "cart", [{"itemId": "i_powerbank", "qty": 2}]),
    "jingdong_08_cup_prepare_checkout": lambda i, c: _set(c, "jingdong", "cart", [{"itemId": "i_cup", "qty": 1}]),
    "kapi_06_fruit_rebuy_addbill": lambda i, c: _set(c, "kapi", "bills", [{"id": "new1", "type": "expense", "categoryId": "c_fruit", "amount": 23.8}]),
    "kapi_07_transport_cheaper_rebill": lambda i, c: _set(c, "kapi", "bills", [{"id": "new1", "type": "expense", "categoryId": "c_transport", "amount": 12.5}]),
    "luckin_01_cheapest_classic_addcart": lambda i, c: _set(c, "luckin", "cart", [{"productId": "lemon-tea", "quantity": 1}]),
    "luckin_08_addcart_two_items": lambda i, c: _set(c, "luckin", "cart", [{"productId": "coconut-latte", "quantity": 1}, {"productId": "cloud-latte", "quantity": 1}]),
    "luckin_09_grape_latte_custom_addcart_notool": lambda i, c: _set(c, "luckin", "cart", [{"productId": "grape-latte", "quantity": 1}]),
    "taobao_03_yunshang_cheap_addcart": lambda i, c: _set(c, "taobao", "cart", [{"id": "new1", "itemId": "i_tee", "qty": 1}]),
    "taobao_07_cheapest_item_addcart": lambda i, c: _set(c, "taobao", "cart", [{"id": "new1", "itemId": "i_cable", "qty": 2}]),
    "taobao_12_giftbox_addcart": lambda i, c: _set(c, "taobao", "cart", [{"id": "new1", "itemId": "i_giftbox", "qty": 1}]),
    # -- v2 --
    "crossapp_01_ctrip_flight_to_daysmatter_countdown": lambda i, c: (_set(i, "daysmatter", "events", []), _set(c, "daysmatter", "events", [{"id": "new1", "title": "无锡出发倒计时", "targetDate": _epoch_ms(2026, 6, 20)}])),
    "crossapp_03_taobao_order_to_kapi_relog": lambda i, c: _set(c, "kapi", "bills", [{"id": "new1", "categoryName": "购物", "amount": 75.2}]),
    # -- v3 --
    # The auto-synthesized positive note only joins this goal's `contains` tokens
    # ("硅谷101 4.8"), which deliberately no longer include the bare "10" (see
    # specs_memory.py's _memory_03_standalone_count_check docstring) -- append the
    # actual count so the extra_check's "standalone 10" requirement is satisfiable.
    "memory_03_broadcast_followed_detour": lambda i, c: [
        n.__setitem__("content", n.get("content", "") + " 共10个")
        for n in (c.get("notes", {}).get("notes") or [])
        if n.get("title") == "关注节目核对"
    ],
    "memory_04_ctrip_daysmatter_detour": lambda i, c: (_set(i, "daysmatter", "events", []), _set(c, "daysmatter", "events", [{"id": "new1", "title": "无锡出发倒计时", "targetDate": _epoch_ms(2026, 6, 20)}])),
    "state_01_taobao_hoodie_exact_sku_addcart": lambda i, c: _set(c, "taobao", "cart", [{"id": "new1", "itemId": "i_hoodie", "skuDesc": "雾蓝色 尺码:L", "qty": 2}]),
    "state_02_kapi_bill_multifield": lambda i, c: _set(c, "kapi", "bills", [{"id": "new1", "categoryName": "购物", "amount": 128.5, "note": "网购日用品", "date": _epoch_ms(2026, 6, 10)}]),
    "state_03_daysmatter_event_multifield": lambda i, c: (_set(i, "daysmatter", "events", []), _set(c, "daysmatter", "events", [{"id": "new1", "title": "驾照考试", "targetDate": _epoch_ms(2026, 9, 1), "reminder": "weekly"}])),
    # -- v4 --
    "broadcast_v4_04_state_add_shortest_followed_episode": lambda i, c: (_set(i, "broadcast", "queueIds", []), _set(c, "broadcast", "queueIds", ["e_espresso_today"])),
    "broadcast_v4_05_state_add_highcount_lowrating": lambda i, c: (_set(i, "broadcast", "queueIds", []), _set(c, "broadcast", "queueIds", ["e_zhenbu_career"])),
    "broadcast_v4_06_state_add_saved_inprogress": lambda i, c: (_set(i, "broadcast", "queueIds", []), _set(c, "broadcast", "queueIds", ["e_42_vanity"])),
    "dianping_v4_03_state_seafood_setmeal_checkout": lambda i, c: _set(c, "dianping", "pendingCheckout", {"shopId": "wangheli", "dealId": "vh2", "qty": 2}),
    "dianping_v4_04_state_dessert_cake_checkout": lambda i, c: _set(c, "dianping", "pendingCheckout", {"shopId": "pangpang", "dealId": "pp1", "qty": 2}),
    "dianping_v4_05_state_sukiyaki_setmeal_checkout": lambda i, c: _set(c, "dianping", "pendingCheckout", {"shopId": "sushiya", "dealId": "su1", "qty": 3}),
    "jingdong_v4_05_monitor_guobu_addcart": lambda i, c: _set(c, "jingdong", "cart", [{"itemId": "i_monitor", "qty": 1, "skuDesc": "27寸"}]),
    "jingdong_v4_06_cart_checkout_select": lambda i, c: _set(c, "jingdong", "cart", [
        {"itemId": "i_wangzai", "checked": True}, {"itemId": "i_toothpaste", "checked": True},
        {"itemId": "i_dumpling", "checked": False}, {"itemId": "i_thinkbook", "checked": False},
    ]),
    "jingdong_v4_07_keyboard_addcart": lambda i, c: _set(c, "jingdong", "cart", [{"itemId": "i_keyboard", "qty": 3, "skuDesc": "青轴"}]),
    "kapi_v4_03_bbq_bill_multifield": lambda i, c: _set(c, "kapi", "bills", [{"id": "new1", "type": "expense", "categoryName": "烧烤", "amount": 156.0, "note": "烧烤", "date": _epoch_ms(2026, 6, 18)}]),
    "kapi_v4_04_hotpot_category_bill": lambda i, c: _set(c, "kapi", "bills", [{"id": "new1", "type": "expense", "categoryName": "火锅", "amount": 88.0, "note": "聚餐", "date": _epoch_ms(2026, 6, 20)}]),
    "kapi_v4_05_invest_income_bill": lambda i, c: _set(c, "kapi", "bills", [{"id": "new1", "type": "income", "categoryName": "投资收益", "amount": 350.0, "note": "分红", "date": _epoch_ms(2026, 6, 22)}]),
    "luckin_v4_02_state_new_address_multifield": lambda i, c: (_set(i, "luckin", "addresses", []), _set(c, "luckin", "addresses", [{
        "id": "new1", "name": "王芳", "phone": "13800001111", "region": "海蓝市 高新区",
        "detail": "智谷科技园B座", "tag": "公司", "isDefault": False,
    }])),
    "luckin_v4_03_state_coupon_inflate": lambda i, c: _set(c, "luckin", "coupons", [{"id": "c02", "claimed": True, "amount": 11.0}]),
    "luckin_v4_04_state_favorite_instant_products": lambda i, c: _set(c, "luckin", "favorites", ["instant-02", "instant-03"]),
    "taobao_v4_04_jacket_exact_sku_addcart_state_direct": lambda i, c: _set(c, "taobao", "cart", [{"id": "new1", "itemId": "i_jacket", "skuDesc": "薄雾蓝 尺码:L", "qty": 3}]),
    "taobao_v4_05_lanjing_single_line_checkout_state_direct": lambda i, c: _set(c, "taobao", "checkout", {
        "shopId": "s_lanjing", "lines": [{"itemId": "i_earbuds", "price": 399, "qty": 1}], "sourceCartLineIds": ["c2"],
    }),
    "taobao_v4_06_qfs_multiline_checkout_state_direct": lambda i, c: _set(c, "taobao", "checkout", {
        "shopId": "s_qfs", "lines": [{"itemId": "i_bodywash", "price": 217, "qty": 1}, {"itemId": "i_giftbox", "price": 260, "qty": 1}],
    }),
    # -- newapps_v2 (yayayacc: Dida / Slack / Mail / Google Drive) --
    "dida_n2_03_create_life_task": lambda i, c: _append(c, "dida", "tasks", {
        "id": "__new_dida", "title": "准备组会材料", "listId": "life", "priority": "medium", "dueTs": 1,
    }),
    "dida_n2_04_complete_buy_groceries": lambda i, c: _patch_by_id(c, "dida", "tasks", "t4", completed=True),
    "drive_n2_02_star_survey_docx": lambda i, c: _set(
        c, "googledrive", "starredIds",
        list((c.get("googledrive") or {}).get("starredIds") or []) + ["i_paper2"],
    ),
    "drive_n2_03_create_acl_drafts": lambda i, c: c.setdefault("googledrive", {}).setdefault("items", {}).__setitem__(
        "folder_acl_drafts",
        {"id": "folder_acl_drafts", "name": "ACL drafts", "kind": "folder", "parentId": None},
    ),
    "drive_n2_04_move_survey_into_2026": lambda i, c: (
        c.setdefault("googledrive", {}).setdefault("items", {}).setdefault("i_paper2", {"id": "i_paper2"}).__setitem__(
            "parentId", "f_sub2026"
        )
    ),
    "mail_n2_02_flag_confhub_comment": lambda i, c: _patch_by_id(c, "mail", "mails", "m-confhub-3", isFlagged=True),
    "mail_n2_03_mark_nimbus_read": lambda i, c: _patch_by_id(c, "mail", "mails", "m-nimbus-1", isRead=True),
    "mail_n2_04_prepare_phd_followup": lambda i, c: _append(c, "mail", "mails", {
        "id": "__new_draft", "folder": "drafts", "subject": "Follow-up on PhD Application 2027 Fall",
        "to": [{"address": "lin.group@gmail.com"}],
        "body": [{"kind": "p", "text": "Thank you for considering my application."}],
    }),
    "slack_n2_01_education_mention_pin": lambda i, c: _patch_by_id(c, "slack", "messages", "m_edu_10", pinned=True),
    "slack_n2_03_dm_linxiao": lambda i, c: _append(c, "slack", "messages", {
        "id": "__new_dm", "convId": "d_lin", "text": "第三章练习方案我看过，可以拆。",
    }),
    "slack_n2_04_create_release_notes": lambda i, c: _append(c, "slack", "conversations", {
        "id": "__new_ch", "kind": "channel", "name": "release-notes", "isPrivate": False,
    }),
    "slack_n2_08_thread_reply": lambda i, c: _append(c, "slack", "messages", {
        "id": "__new_th", "convId": "c_education", "text": "收到，按这版推进。", "threadParentId": "m_edu_3",
    }),
}


def audit_suite(suite_module_name: str) -> list[dict[str, Any]]:
    from bench_env.task.hybrid_tools_v1.verifier import evaluate_goals

    defs_pkg = f"bench_env.task.{suite_module_name}.{SUITE_DEFS_DIR}"
    defs_dir = MOBILEGYM_ROOT / "bench_env" / "task" / suite_module_name.split(".")[-1] / SUITE_DEFS_DIR
    findings: list[dict[str, Any]] = []
    if not defs_dir.exists():
        print(f"[skip] no {defs_dir}")
        return findings
    for py_file in sorted(defs_dir.glob("specs_*.py")):
        mod_name = f"{defs_pkg}.{py_file.stem}"
        module = importlib.import_module(mod_name)
        specs = getattr(module, "SPECS", [])
        extra_checks = getattr(module, "EXTRA_CHECKS", {})
        for item in specs:
            judge_input = _build_judge_input(item, no_op=True)
            try:
                checks = evaluate_goals(item.goals, judge_input)
                extra_fn = extra_checks.get(item.task_id)
                if extra_fn is not None:
                    checks.extend(extra_fn(judge_input))
            except Exception as exc:  # noqa: BLE001
                findings.append({
                    "task_id": item.task_id,
                    "status": "ERROR",
                    "detail": f"{type(exc).__name__}: {exc}",
                })
                continue
            all_passed = bool(checks) and all(c["passed"] for c in checks)
            if all_passed:
                findings.append({
                    "task_id": item.task_id,
                    "status": "LEAK",
                    "detail": "no-op (identical init/last state, no answer) still reports ALL checks passed",
                    "checks": checks,
                })
            elif not checks:
                findings.append({
                    "task_id": item.task_id,
                    "status": "NO_CHECKS",
                    "detail": "spec.goals is empty and no extra_check registered -- nothing is actually verified",
                })

            positive_input = _build_positive_fixture_or_none(item)
            if positive_input is not None:
                pos_checks = evaluate_goals(item.goals, positive_input)
                extra_fn = extra_checks.get(item.task_id)
                if extra_fn is not None:
                    pos_checks.extend(extra_fn(positive_input))
                if not all(c["passed"] for c in pos_checks):
                    findings.append({
                        "task_id": item.task_id,
                        "status": "UNSATISFIABLE",
                        "detail": "constructed 'correct' fixture (note + hand-built state mutation) still fails -- verifier condition is self-contradictory or fixture is wrong",
                        "checks": pos_checks,
                    })
            elif item.task_id in extra_checks and item.task_id not in POSITIVE_FIXTURES:
                findings.append({
                    "task_id": item.task_id,
                    "status": "NO_POSITIVE_FIXTURE",
                    "detail": "has an extra_check but no hand-built POSITIVE_FIXTURES entry yet -- only the no-op half is verified for this task",
                })
    return findings


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suite_names", nargs="*", default=["hybrid_tools_selfbuilt_v4"])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    suite_names = args.suite_names
    all_findings: list[dict[str, Any]] = []
    total_tasks = 0
    for suite_name in suite_names:
        defs_dir = MOBILEGYM_ROOT / "bench_env" / "task" / suite_name / SUITE_DEFS_DIR
        for py_file in sorted(defs_dir.glob("specs_*.py")) if defs_dir.exists() else []:
            mod = importlib.import_module(f"bench_env.task.{suite_name}.{SUITE_DEFS_DIR}.{py_file.stem}")
            total_tasks += len(getattr(mod, "SPECS", []))
        findings = audit_suite(suite_name)
        all_findings.extend(findings)

    print(f"suites: {suite_names}")
    print(f"total tasks scanned: {total_tasks}")
    leaks = [f for f in all_findings if f["status"] == "LEAK"]
    no_checks = [f for f in all_findings if f["status"] == "NO_CHECKS"]
    errors = [f for f in all_findings if f["status"] == "ERROR"]
    unsatisfiable = [f for f in all_findings if f["status"] == "UNSATISFIABLE"]
    no_fixture = [f for f in all_findings if f["status"] == "NO_POSITIVE_FIXTURE"]
    print(f"LEAK (no-op passes -- critical): {len(leaks)}")
    print(f"NO_CHECKS (nothing verified): {len(no_checks)}")
    print(f"UNSATISFIABLE (constructed correct fixture still fails): {len(unsatisfiable)}")
    print(f"NO_POSITIVE_FIXTURE (extra_check without a hand-built positive fixture yet): {len(no_fixture)}")
    print(f"ERROR (harness/verifier crashed): {len(errors)}")
    for f in all_findings:
        print(json.dumps({k: v for k, v in f.items() if k != "checks"}, ensure_ascii=False))
    report = {
        "suites": suite_names,
        "total_tasks_scanned": total_tasks,
        "leaks": len(leaks),
        "no_checks": len(no_checks),
        "unsatisfiable": len(unsatisfiable),
        "no_positive_fixture": len(no_fixture),
        "errors": len(errors),
        "findings": all_findings,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 1 if (leaks or no_checks or errors or unsatisfiable) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
