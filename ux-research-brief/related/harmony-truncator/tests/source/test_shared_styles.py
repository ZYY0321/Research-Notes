"""Style expansion must affect actual rewrites, not only padding metadata."""

import tempfile
import unittest
from pathlib import Path

from truncator.source.project import scan, prepare
from truncator.mutation.operators import mutate
from truncator.mutation.mutations import plans
from truncator.source.source_attributes import numeric_attribute
from truncator.common.storage import read

PROFILE = Path(__file__).resolve().parents[2] / "profiles/apps/ohbill.json"


class SharedStyleTests(unittest.TestCase):
    def fixture(self, root, declarations, chain, extra=None, component="Text"):
        for name, code in (extra or {}).items():
            (root / name).write_text(code, encoding="utf-8")
        (root / "Index.ets").write_text(
            declarations + "\n@Component struct Index { build() { Column() { "
            + component + "('hello')" + chain + " } } }", encoding="utf-8")
        profile = {**read(PROFILE), "source": str(root)}
        catalog = scan(profile)
        self.assertEqual(catalog["diagnostics"], [])
        site = next(s for s in catalog["sites"] if s["file"] == "Index.ets" and s["component"] == component)
        return profile, catalog, site

    def test_imported_margin_moves_to_wrapper_and_clip_override_follows_style(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, _, site = self.fixture(root, "import { shared } from './styles';", ".width(300).shared(9)",
                {"styles.ets": "@Extend(Text) export function shared(n: number) { .margin({ left: n }).width(240).clip(false) }"})
            self.assertEqual(numeric_attribute(site, "margin", ["left"]), {"left": 9})
            result = mutate(site, "fixed-parent-clip", {
                "child_width": 240, "child_height": 30, "width": 150, "height": 30})
            self.assertIn('.shared(9).width(240)', result)
            self.assertIn('.margin(0)', result)
            self.assertTrue(result.endswith('.margin({"left":9})'))
            self.assertIn('styles.ets', site["styles"]["dependencies"])
            self_clip = mutate(site, "height-clip", {"height": 10})
            self.assertTrue(self_clip.endswith('.height(10).clip(true)'))

    def test_hidden_weight_is_rejected_before_rewrite(self):
        with tempfile.TemporaryDirectory() as directory:
            _, _, site = self.fixture(Path(directory),
                '@Extend(Text) function shared() { .layoutWeight(1) }', '.shared()')
            with self.assertRaisesRegex(ValueError, 'layoutWeight'):
                mutate(site, "fixed-parent-clip", {"child_width": 200, "child_height": 30})

    def test_component_type_selects_right_same_named_extend(self):
        with tempfile.TemporaryDirectory() as directory:
            _, _, site = self.fixture(Path(directory),
                '@Extend(Text) function shared() { .padding(3) }\n'
                '@Extend(Button) function shared() { .padding(15) }', '.shared()')
            self.assertEqual(site["padding"]["value"], 3)

    def test_duplicate_wrong_type_and_dynamic_styles_are_rejected(self):
        declarations = [
            '@Extend(Text) function shared() { .padding(3) }\n@Extend(Text) function shared() { .padding(4) }',
            '@Extend(Button) function shared() { .padding(3) }',
            '@Extend(Text) function shared() { if (true) { .padding(3) } }',
        ]
        for code in declarations:
            with self.subTest(code=code), tempfile.TemporaryDirectory() as directory:
                _, _, site = self.fixture(Path(directory), code, '.shared()')
                with self.assertRaisesRegex(ValueError, 'shared style'):
                    mutate(site, 'height-clip', {"height": 10})

    def test_same_style_name_in_other_file_does_not_shadow_import(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, _, site = self.fixture(root, "import { shared as chosen } from './a';", ".chosen()", {
                "a.ets": '@Extend(Text) export function shared() { .padding(4) }',
                "b.ets": '@Extend(Text) export function shared() { .padding(99) }',
            })
            self.assertEqual(site["padding"]["value"], 4)
            self.assertNotIn('b.ets', site["styles"]["dependencies"])

    def test_changed_margin_dependency_is_rejected_even_without_padding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            profile, catalog, site = self.fixture(source, "import { shared } from './styles';", ".shared()", {
                "styles.ets": '@Extend(Text) export function shared() { .margin(4) }'})
            plan = plans(catalog, 0, 1, 'height-clip', {"height": 10}, site_id=site['id'])[0]
            (source / 'styles.ets').write_text('@Extend(Text) export function shared() { .margin(40) }')
            with self.assertRaisesRegex(ValueError, 'Style dependency changed'):
                prepare(profile, root / 'run', plan)
