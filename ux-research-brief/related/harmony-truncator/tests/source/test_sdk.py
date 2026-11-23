"""SDK contract checks against real ArkUI syntax, including UTF-16 source offsets."""

import tempfile
import unittest
from pathlib import Path
from truncator.source.project import scan
from truncator.common.storage import read, digest
from truncator.mutation.operators import mutate
from truncator.source.instrumentation import instrument
from truncator.source.binding import bind_candidates

PROFILE = Path(__file__).resolve().parents[2] / "profiles/apps/ohbill.json"


@unittest.skipUnless(PROFILE.exists(), "Local SDK profile required")
class SdkTests(unittest.TestCase):
    def test_instrumented_loop_binds_instances_and_only_mutates_one_index(self):
        source = """@Entry
@Component
struct Index {
  build() {
    Column() {
      ForEach([1, 2], (item: number) => {
        Text('item ' + item).width(100)
      })
      Text('existing').id('keep-me')
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
                {**read(PROFILE), "source": str(original)}, root / "instrumented"
            )
            catalog = scan(profile)
            site = next(s for s in catalog["sites"] if s.get("probe"))
            self.assertIn("__truncatorIndex_", site["probe"]["index_name"])
            tree = {
                "children": [
                    {
                        "attributes": {
                            "id": site["probe"]["prefix"] + str(i),
                            "type": "Text",
                            "bounds": f"[0,{i*100}][100,{i*100+50}]",
                        }
                    }
                    for i in range(2)
                ]
            }
            bindings = bind_candidates(catalog, tree)["bindings"]
            self.assertEqual([b["instance_index"] for b in bindings], [0, 1])
            replacement = mutate(
                site, "height-clip", {"height": 12, "instance_index": 1}
            )
            self.assertIn(" === 1)", replacement)
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
            self.assertIn(".id('keep-me')", before)

    def test_unicode_chain_and_repeated_instance(self):
        source = """@Entry
@Component
struct Index {
  build() {
    Column() {
      Text("中文😀").width(240).fontSize(24)
      ForEach([1,2], (item: number) => {
        Text("重复" + item).width(100)
      })
    }
  }
}
"""
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "Index.ets").write_bytes(
                source.replace("\n", "\r\n").encode()
            )
            profile = {**read(PROFILE), "source": directory}
            catalog = scan(profile)
            self.assertEqual(catalog["diagnostics"], [])
            self.assertEqual(len(catalog["sites"]), 2)
            raw = Path(directory, "Index.ets").read_bytes().decode()
            for site in catalog["sites"]:
                self.assertEqual(raw[site["start"] : site["end"]], site["snippet"])
                self.assertEqual(digest(site["snippet"]), site["sha256"])
            site = next(s for s in catalog["sites"] if "😀" in s["snippet"])
            changed = mutate(site, "line-clip", {"width": 30})
            self.assertIn(".width(30)", changed)
            self.assertTrue(
                next(s for s in catalog["sites"] if "重复" in s["snippet"])["repeated"]
            )
