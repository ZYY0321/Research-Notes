import tempfile
import unittest
from pathlib import Path

from truncator.source.project import scan, prepare
from truncator.mutation.mutations import plans
from truncator.common.storage import read, digest

PROFILE = Path(__file__).resolve().parents[2] / "profiles/apps/ohbill.json"


@unittest.skipUnless(PROFILE.exists(), "Local SDK profile required")
class PaddingScanTests(unittest.TestCase):
    def scan_style(self, root, body, expression, constants=""):
        (root / "constants.ets").write_text(constants, encoding="utf8")
        source = "import Const from './constants';\n" + body + '''
@Entry
@Component
struct Index {
  build() { Column() { Text('sample')''' + expression + ''' } }
}
'''
        (root / "Index.ets").write_text(source, encoding="utf8")
        catalog = scan({**read(PROFILE), "source": str(root)})
        self.assertEqual(catalog["diagnostics"], [])
        return next(s["padding"] for s in catalog["sites"] if s["component"] == "Text")

    def test_shared_style_resolves_imported_readonly_percent_and_binds_dependency(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.scan_style(root,
                '@Extend(Text) function shared() { .padding({ top: Const.P, bottom: Const.P }) }',
                '.shared()', "export default class Const { static readonly P: string = '1.5%'; }")
            self.assertEqual(result["value"], {"top": "1.5%", "bottom": "1.5%"})
            self.assertEqual(result["via"], ["shared"])
            self.assertEqual(result["dependencies"], {"constants.ets": digest((root / "constants.ets").read_bytes())})

    def test_last_direct_padding_overrides_shared_style(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.scan_style(Path(tmp),
                '@Extend(Text) function shared() { .padding(20) }', '.shared().padding({ bottom: 3 })')
            self.assertEqual(result["value"], {"bottom": 3})
            self.assertEqual(result["via"], [])

    def test_dynamic_padding_and_mutable_constants_remain_unresolved(self):
        for expression, constants in (
            ('.padding(getPadding())', ''),
            ('.padding(Const.P)', 'export default class Const { static P: number = 5; }'),
        ):
            with self.subTest(expression=expression), tempfile.TemporaryDirectory() as tmp:
                result = self.scan_style(Path(tmp), '', expression, constants)
                self.assertEqual(result["status"], "unresolved")

    def test_static_parameterized_style_is_resolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.scan_style(Path(tmp),
                '@Extend(Text) function shared(amount: number) { .padding(amount) }', '.shared(10)')
            self.assertEqual(result["value"], 10)

    def test_imported_style_resolves_actual_padding(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.scan_style(Path(tmp), "import { shared } from './constants';",
                '.shared()', '@Extend(Text) export function shared() { .padding(12) }')
            self.assertEqual(result["value"], 12)

    def test_changed_imported_padding_constant_is_rejected_before_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'source'
            source.mkdir()
            self.scan_style(source,
                '@Extend(Text) function shared() { .padding(Const.P) }', '.shared()',
                'export default class Const { static readonly P: number = 5; }')
            profile = {**read(PROFILE), 'source': str(source)}
            catalog = scan(profile)
            target = next(s for s in catalog['sites'] if s['component'] == 'Text')
            plan = plans(catalog, 0, 1, 'height-clip', {'height': 12}, site_id=target['id'])[0]
            (source / 'constants.ets').write_text('export default class Const { static readonly P: number = 20; }')
            with self.assertRaisesRegex(ValueError, 'Style dependency changed'):
                prepare(profile, root / 'run', plan)
            self.assertFalse((root / 'run').exists())


if __name__ == '__main__':
    unittest.main()
