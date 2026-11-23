"""Regression coverage for instance isolation and delayed replay observations."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image

from truncator.source.binding import bind_candidates
from truncator.source.instrumentation import instrument
from truncator.mutation.operators import mutate
from truncator.source.project import scan
from truncator.planning.planning import geometry_plans
from truncator.execution.device.runtime import capture
from truncator.common.storage import digest, read, save
from truncator.execution.device.waiting import wait_for_tree

PROFILE = Path(__file__).resolve().parents[2] / "profiles/apps/ohbill.json"


def node(identifier, bounds="[0,0][100,50]", text="content"):
    return {
        "attributes": {"id": identifier, "type": "Text", "bounds": bounds, "text": text}
    }


class InstanceTests(unittest.TestCase):
    def test_instance_if_consumes_expression_semicolon_and_keeps_comments(self):
        from truncator.mutation.mutations import plans, mutation_patches, apply_patches
        for suffix in (";", " /* retain this comment */ ;", ""):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as directory:
                original = Path(directory) / "source"
                original.mkdir()
                (original / "Index.ets").write_text(
                    "@Entry @Component struct Index { build() { Column() {\n"
                    "ForEach(['a', 'b'], (item: string, index: number) => {\n"
                    "Text(item).width(100)" + suffix + "\n}, (value: string) => value)\nText('untouched');\n} } }",
                    encoding="utf-8")
                profile = instrument({**read(PROFILE), "source": str(original)}, Path(directory) / "traced")
                catalog = scan(profile)
                site = next(s for s in catalog["sites"] if s["repeated"])
                self.assertEqual(site.get("statement_suffix", ""), suffix)
                source = (Path(profile["source"]) / "Index.ets").read_bytes().decode("utf-8")
                for selection in ({"instance_key": "a"}, {"instance_index": 0}):
                    if "instance_index" in selection:
                        site["probe"]["index_name"] = "index"
                    plan = plans(catalog, 0, 1, "height-clip", {"height": 12, **selection}, site_id=site["id"])[0]
                    edits = mutation_patches(plan)
                    rewritten = apply_patches(source, edits)
                    self.assertEqual(edits[0]["before"], site["snippet"] + suffix)
                    self.assertEqual(edits[0]["end"], site["end"] + len(suffix))
                    self.assertNotIn("};", rewritten)
                    if "comment" in suffix:
                        self.assertIn("/* retain this comment */", rewritten)
                    untouched = next(s for s in catalog["sites"] if not s["repeated"])
                    self.assertIn(untouched["snippet"] + ";", rewritten)

    def test_loop_uses_existing_item_key_instead_of_position(self):
        self.check_instance(
            """build() {
  Column() {
    ForEach(['a', 'b'], (item: string, index: number) => {
      Text(item).width(100)
    }, (value: string) => value)
  }
}""",
            "b",
            ["encodeURIComponent(String(item))"],
        )

    def test_loop_uses_existing_object_key(self):
        self.check_instance(
            """build() {
  Column() {
    ForEach([], (item: Product, index: number) => {
      Text(item.name).width(100)
    }, (value: Product) => value.id.toString())
  }
}""",
            "42",
            ["encodeURIComponent(String(item.id))"],
        )

    def test_global_builder_is_explicitly_excluded_until_call_sites_are_supported(self):
        source = """@Builder
function cell(label: string) { Text(label) }
@Entry
@Component
struct Index { build() { Column() { cell('a'); cell('b') } } }
"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "original"
            original.mkdir()
            (original / "Index.ets").write_text(source, encoding="utf-8")
            profile = instrument(
                {**read(PROFILE), "source": str(original)}, root / "traced"
            )
            self.assertEqual(scan(profile)["diagnostics"], [])
            mapping = read(root / "traced/source-map.json")
            self.assertEqual(mapping["entries"], [])
            self.assertEqual(
                mapping["skipped"][0]["reason"], "global_builder_scope_unsupported"
            )

    def check_instance(self, body, key, expected_parts, declarations=""):
        source = (
            declarations + "\n@Entry\n@Component\nstruct Index {\n" + body + "\n}\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "original"
            original.mkdir()
            (original / "Index.ets").write_text(source, encoding="utf-8")
            profile = instrument(
                {**read(PROFILE), "source": str(original)}, root / "traced"
            )
            catalog = scan(profile)
            self.assertEqual(catalog["diagnostics"], [])
            site = catalog["sites"][0]
            expression = site["probe"]["key_expression"]
            for part in expected_parts:
                self.assertIn(part, expression)
            identifier = site["probe"]["prefix"] + key
            tree = [node(identifier), node(site["probe"]["prefix"] + "different")]
            bindings = bind_candidates(catalog, tree)["bindings"]
            self.assertEqual(bindings[0]["instance_key"], key)
            self.assertEqual(
                bind_candidates(catalog, [node(identifier), node(identifier)])[
                    "bindings"
                ],
                [],
            )
            baseline = root / "baseline"
            baseline.mkdir()
            Image.new("RGB", (200, 100), "white").save(baseline / "snapshot.jpeg")
            save(
                baseline / "capture.json",
                {
                    "screenshot_sha256": digest(
                        (baseline / "snapshot.jpeg").read_bytes()
                    )
                },
            )
            save(baseline / "tree-before.json", tree)
            save(baseline / "tree-after.json", tree)
            plan = geometry_plans(
                catalog, baseline, bindings[0], "height-clip", 1, [12], edge="bottom"
            )[0]
            self.assertEqual(plan["parameters"]["instance_key"], key)
            self.assertEqual(plan["geometry"]["mutated_selector"]["id"], identifier)
            replacement = mutate(
                site, "height-clip", {"height": 12, "instance_key": key}
            )
            self.assertIn("=== " + json.dumps(key), replacement)
            self.assertIn("else {\n" + site["snippet"], replacement)
            path = Path(profile["source"]) / "Index.ets"
            before = path.read_bytes().decode("utf-8")
            path.write_bytes(
                (before[: site["start"]] + replacement + before[site["end"] :]).encode(
                    "utf-8"
                )
            )
            self.assertEqual(scan(profile)["diagnostics"], [])
            self.assertEqual(
                (original / "Index.ets").read_text(encoding="utf-8"), source
            )

    def test_builder_prefers_declared_object_key_over_index_parameter(self):
        self.check_instance(
            """@Builder
cell(item: Product, index: number) { Text(item.name).width(100) }
build() { Column() { this.cell({ id: 'a', name: 'A' }, 0); this.cell({ id: 'b', name: 'B' }, 1) } }
""",
            "b",
            ["encodeURIComponent(String(item.id))"],
            "interface Product { id: string; name: string }",
        )

    def test_nested_loop_combines_both_indices(self):
        self.check_instance(
            """build() {
  Column() {
    ForEach([1,2], (group: number, outer: number) => {
      ForEach([1,2], (item: number) => {
        Text('nested ' + group + item).width(100)
      })
    })
  }
}""",
            "1|0",
            ["String(outer)", "String(__truncatorIndex_"],
        )

    def test_builder_encodes_scalar_key(self):
        self.check_instance(
            """@Builder
cell(label: string, position: number) {
  Text(label).width(100)
}
build() { Column() { this.cell('a|b', 0); this.cell('c', 1) } }""",
            "a%7Cb|0",
            [
                "encodeURIComponent(String(label))",
                "encodeURIComponent(String(position))",
            ],
        )

    def test_builder_with_loop_combines_call_and_loop_keys(self):
        self.check_instance(
            """@Builder
cell(label: string) {
  ForEach([1,2], (item: number, index: number) => { Text(label + item).width(100) })
}
build() { Column() { this.cell('a'); this.cell('b') } }""",
            "a|1",
            ["encodeURIComponent(String(label))", "String(index)"],
        )

    def test_unsupported_scopes_remain_unmodified(self):
        source = """@Entry
@Component
struct Index {
  @Builder
  cell() { Text('shared') }
  build() {
    Column() {
      ForEach([1,2], (item: number, index: number) => {
        ForEach([1,2], (item: number, index: number) => { Text('shadowed') })
      })
      ForEach([1,2], item => { Text('unparenthesized') })
      this.cell()
      this.cell()
    }
  }
}
"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "original"
            original.mkdir()
            (original / "Index.ets").write_text(source, encoding="utf-8")
            profile = instrument(
                {**read(PROFILE), "source": str(original)}, root / "traced"
            )
            mapping = read(root / "traced/source-map.json")
            self.assertEqual(len(mapping["entries"]), 0)
            self.assertEqual(len(mapping["skipped"]), 3)
            self.assertEqual(
                (Path(profile["source"]) / "Index.ets").read_text(encoding="utf-8"),
                source,
            )
            self.assertEqual(
                bind_candidates(scan(profile), [node("", text="shared")])["bindings"],
                [],
            )

    def test_single_call_builder_chain_keeps_normal_instrumentation(self):
        source = """@Entry
@Component
struct Index {
  @Builder
  leaf() { Text('single') }
  @Builder
  parent() { this.leaf() }
  build() { Column() { this.parent() } }
}
"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "original"
            original.mkdir()
            (original / "Index.ets").write_text(source, encoding="utf-8")
            profile = instrument(
                {**read(PROFILE), "source": str(original)}, root / "traced"
            )
            catalog = scan(profile)
            self.assertFalse(catalog["sites"][0]["repeated"])
            self.assertEqual(len(read(root / "traced/source-map.json")["entries"]), 1)


class FakeClock:
    def __init__(self):
        self.now = 0

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds

    def wait(self, *args, **kwargs):
        return wait_for_tree(*args, **kwargs, clock=self.clock, sleep=self.sleep)


class WaitingTests(unittest.TestCase):
    def test_delayed_node_and_moving_bounds_require_consecutive_samples(self):
        clock = FakeClock()
        observations = iter(
            [None, "position1", "position2", None, "position2", "position2"]
        )
        tree, result = clock.wait(
            lambda: next(observations),
            lambda t: (t is not None, t),
            timeout=5,
            stable_samples=2,
        )
        self.assertEqual(tree, "position2")
        self.assertTrue(result["ready"])
        self.assertEqual(len(result["polls"]), 6)

    def test_timeout_is_bounded_and_preserves_last_observation(self):
        clock = FakeClock()
        tree, result = clock.wait(
            lambda: [1, 2], lambda t: (len(t) == 1, t), timeout=1.2, interval=0.5
        )
        self.assertEqual(tree, [1, 2])
        self.assertFalse(result["ready"])
        self.assertEqual(clock.now, 1.2)

    def test_invalid_wait_settings(self):
        for kwargs in (
            {"timeout": -1},
            {"interval": 0},
            {"stable_samples": True},
            {"timeout": float("inf")},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                FakeClock().wait(lambda: None, lambda t: (True, None), **kwargs)

    def test_capture_recovers_exit_before_first_action(self):
        self.test_capture_waits_for_target_and_checkpoint_dispatches_once(late_exit=True)

    def test_capture_waits_for_target_and_checkpoint_dispatches_once(self, late_exit=False):
        clock = FakeClock()
        commands = []
        pids = iter(["123", "", "456"] if late_exit else ["123"])
        needs_recovery = late_exit
        final = [node("done")]
        observations = iter(
            [
                [],
                [node("button", "[0,0][90,50]")],
                [node("button")],
                [node("button")],
                [],
                final,
                final,
            ]
        )

        def command(args, log, **kwargs):
            commands.append(args)
            if "dumpLayout" in args:
                output = "DumpLayout saved"
            elif "cat" in args and args[-1].startswith("/proc/"):
                pid = "456" if late_exit else "123"
                output = pid + " (sample) S " + "0 " * 18 + "100"
            elif "cat" in args:
                output = json.dumps(next(observations))
            elif "clean" in args:
                output = "clean bundle data files successfully."
            elif "pidof" in args:
                output = next(pids, "456" if late_exit else "123")
            else:
                output = ""
            Path(log).write_text(output, encoding="utf-8")
            return output, {"seconds": 0, "returncode": 0}

        def acquire(attempt, *args):
            (attempt / "snapshot.jpeg").write_bytes(b"test snapshot")
            save(attempt / "tree-before.json", final)
            save(attempt / "tree-after.json", final)
            return final, final

        def wait(*args, **kwargs):
            nonlocal needs_recovery
            if needs_recovery:
                needs_recovery = False
                return [], {"ready": False, "polls": [], "elapsed": 10}
            return clock.wait(*args, **kwargs)

        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            profile = {"hdc": "mock", "bundle": "sample", "hap": "app.hap"}
            save(run / "profile.json", profile)
            (run / "project").mkdir()
            (run / "project/app.hap").write_bytes(b"hap")
            save(run / "build.json", {"hap_sha256": digest(b"hap")})
            recipe = {
                "settle_seconds": 0,
                "reset_app_data": True,
                "setup_actions": [
                    {
                        "type": "click",
                        "field": "id",
                        "equals": "button",
                        "wait": 0,
                        "checks": [{"field": "id", "equals": "done"}],
                    }
                ],
                "checks": [{"field": "id", "equals": "done"}],
            }
            with patch("truncator.execution.device.runtime.command", command), patch(
                "truncator.execution.device.runtime.wait_for_tree", wait
            ), patch("truncator.execution.device.runtime.time.sleep", clock.sleep), patch(
                "truncator.execution.device.acquisition.acquire", acquire
            ):
                attempt = capture(profile, run, "test-wait-device", recipe, run)
            replay = read(attempt / "replay.json")[0]
            self.assertEqual(replay["status"], "checkpoint_passed")
            self.assertEqual(replay["phase"], "setup")
            self.assertEqual(
                read(attempt / "initial-state.json")["data_policy"], "clear"
            )
            clean_index = next(i for i, c in enumerate(commands) if "clean" in c)
            start_index = next(i for i, c in enumerate(commands) if "start" in c)
            self.assertLess(clean_index, start_index)
            self.assertEqual(len(replay["location_wait"]["polls"]), 4)
            self.assertEqual(len(replay["checkpoint_wait"]["polls"]), 2)
            self.assertEqual(sum("uiInput" in c for c in commands), 1)
            self.assertEqual(sum("clean" in c for c in commands), 1)
            self.assertEqual(sum("start" in c for c in commands), 2 if late_exit else 1)
            if late_exit:
                self.assertEqual(len(replay["location_wait"]["startup_waits"]), 2)
                self.assertTrue(
                    read(attempt / "initial-state.json")["launches"][0]["exited_before_first_action"]
                )
            self.assertTrue(read(attempt / "page-wait.json")["ready"])
