import unittest
from truncator.planning.layout_impact import compare_layout


def node(identifier, box):
    return {"attributes": {"id": identifier, "type": "Text", "bounds": box}}


class LayoutImpactTests(unittest.TestCase):
    def test_target_expanding_beyond_reserved_region_is_reported(self):
        result = compare_layout(
            [node("target", [0, 0, 100, 20])],
            [node("target", [0, 0, 100, 200])],
            [[0, 0, 100, 20]],
        )
        self.assertEqual(result["outside_expected_count"], 1)

    def test_records_moved_and_missing_unrelated_nodes(self):
        before = [
            node("target", [0, 0, 100, 20]),
            node("other", [0, 200, 100, 240]),
            node("missing", [0, 300, 100, 340]),
        ]
        after = [node("target", [0, 0, 50, 20]), node("other", [0, 220, 100, 260])]
        result = compare_layout(before, after, [[0, 0, 100, 20]])
        self.assertEqual(len(result["changes"]), 3)
        self.assertEqual(result["outside_expected_count"], 2)

    def test_duplicate_ids_and_small_motion_do_not_create_false_pairing(self):
        before = [
            node("same", [0, 0, 10, 10]),
            node("same", [0, 20, 10, 30]),
            node("small", [0, 50, 10, 60]),
        ]
        after = [node("same", [0, 0, 10, 10]), node("small", [1, 50, 11, 60])]
        result = compare_layout(before, after, [])
        self.assertEqual(result["changes"], [])
        self.assertEqual(result["ambiguous_ids"], [["same", "Text"]])
