import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from truncator.execution.build import install_dependencies


class DependencyRecoveryTests(unittest.TestCase):
    def test_transient_network_failure_retries_with_distinct_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            logs = []

            def run(args, log, *rest):
                logs.append(log)
                log.write_text("ECONNRESET" if len(logs) == 1 else "installed")
                if len(logs) == 1:
                    raise RuntimeError("Command failed")

            with patch("truncator.execution.build.command", side_effect=run), patch("truncator.execution.build.time.sleep"):
                install_dependencies(["ohpm"], root, root, {})
            self.assertEqual(len(logs), 2)
            self.assertNotEqual(logs[0], logs[1])
            self.assertEqual(logs[0].read_text(), "ECONNRESET")

    def test_unrecognized_and_persistent_errors_stop_with_bounded_attempts(self):
        for message, expected in (("Invalid dependency version", 1), ("ETIMEDOUT", 2)):
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                def fail(args, log, *rest):
                    log.write_text(message)
                    raise RuntimeError("Command failed")
                with patch("truncator.execution.build.command", side_effect=fail) as command, patch("truncator.execution.build.time.sleep"):
                    with self.assertRaises(RuntimeError):
                        install_dependencies(["ohpm"], root, root, {})
                self.assertEqual(command.call_count, expected)
