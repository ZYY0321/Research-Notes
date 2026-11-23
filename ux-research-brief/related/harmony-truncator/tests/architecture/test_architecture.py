"""Keep offline review consumers independent of device execution."""

from pathlib import Path
import subprocess
import sys
import unittest


class ReviewArchitectureTests(unittest.TestCase):
    def test_operator_capabilities_cover_registry_without_research_dependencies(self):
        from truncator.mutation.operators import REGISTRY, UX_OPERATORS, DEFAULT_CAMPAIGN_OPERATORS
        from truncator.mutation.operator_strategies import STRATEGIES
        self.assertEqual(set(REGISTRY), set(STRATEGIES))
        for name in REGISTRY:
            self.assertIn(REGISTRY[name]["task_role"], {"out_of_scope", "normal_control", "truncation_candidate"})
        self.assertEqual(len(UX_OPERATORS), 16)
        self.assertEqual(len(DEFAULT_CAMPAIGN_OPERATORS), 12)
        self.assertTrue({"scroll-recovery", "whitespace-clip", "width-clip", "line-clip"} <= set(DEFAULT_CAMPAIGN_OPERATORS))
        self.assertNotIn("cache-viewport-width", DEFAULT_CAMPAIGN_OPERATORS)

    def test_every_core_module_imports_without_research_tools(self):
        # Block research imports at the interpreter boundary, including lazy imports.
        result = subprocess.run([sys.executable, "-c", '''
import importlib, importlib.abc, pkgutil, sys
class NoResearch(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'research' or fullname.startswith('research.'):
            raise AssertionError('Core imported optional research: ' + fullname)
sys.meta_path.insert(0, NoResearch())
import truncator
for module in pkgutil.walk_packages(truncator.__path__, 'truncator.'):
    importlib.import_module(module.name)
from truncator.__main__ import create_parser
from truncator.review.datasets.dataset import export_dataset
from pathlib import Path
import tempfile, json
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root/'runs').mkdir()
    assert export_dataset(root/'runs', root/'out') == 0
    assert (root/'out/balance.json').exists()
assert 'case-review' not in create_parser().format_help()
assert 'dataset-audit' in create_parser().format_help()
'''], cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_offline_consumers_do_not_import_execution_modules(self):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys; import truncator.review.reporting.evidence; import truncator.review.datasets.delivery; import truncator.review.reporting.review_ui; import truncator.review.review_evidence; import truncator.common.capture_files; import truncator.imaging.content_transition; import truncator.review.datasets.dataset; "
                "assert not set(sys.modules).intersection({"
                "'truncator.execution.curation', 'truncator.execution.workflow', "
                "'truncator.execution.device.runtime', 'truncator.execution.build'})",
            ],
            cwd=Path(__file__).resolve().parents[2],
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

