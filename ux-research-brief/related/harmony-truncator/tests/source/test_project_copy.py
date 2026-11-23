import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from truncator.source.project import prepare, scan
from truncator.common.storage import read


class ProjectCopyTests(unittest.TestCase):
    def test_scanner_timeout_is_an_application_failure_not_uncaught_subprocess_error(self):
        import subprocess
        with patch("truncator.source.project.subprocess.run", side_effect=subprocess.TimeoutExpired("node", 180)):
            with self.assertRaisesRegex(RuntimeError, "scan timed out"):
                scan({"node": "node", "sdk": "sdk", "source": "source"})

    def test_preparation_preserves_dependency_inputs_but_not_installed_caches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            files = {
                "Index.ets": "@Component struct Index { build() { Text('value') } }",
                "oh-package.json5": '{"dependencies":{"local":"file:./libs/local"}}',
                "oh-package-lock.json5": '{"lockfileVersion":3}',
                "libs/local/Index.ets": "export const local = 1;",
                "libs/local/oh-package.json5": '{"name":"local","version":"1.0.0"}',
                "oh_modules/deep/installed.js": "generated cache",
                "entry/oh_modules/installed.ets": "generated module cache",
                "node_modules/installed.js": "generated node cache",
                "libs/local/node_modules/installed.js": "generated nested cache",
            }
            for name, text in files.items():
                path = source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
            with patch("truncator.source.project.scan", return_value={"files": {}, "diagnostics": []}):
                prepare({"source": str(source)}, root / "run")
            self.assertEqual(read(root / "run/prepared.json")["status"], "prepared")
            for name, text in files.items():
                copied = root / "run/project" / name
                if {"oh_modules", "node_modules"}.intersection(Path(name).parts):
                    self.assertFalse(copied.exists())
                else:
                    self.assertEqual(copied.read_text(encoding="utf-8"), text)
                self.assertEqual((source / name).read_text(encoding="utf-8"), text)


if __name__ == "__main__":
    unittest.main()
