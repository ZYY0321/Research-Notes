import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from truncator.execution.device.failure_evidence import observe_failure, validate_failure_evidence
from truncator.execution.device.runtime import capture
from truncator.common.storage import read, save, digest


class FailureEvidenceTests(unittest.TestCase):
    def observe(self, root, *, missing_before=False, snapshot_failure=False):
        calls = []
        dumps = 0

        def hdc(*args):
            nonlocal dumps
            calls.append(args)
            if 'dumpLayout' in args:
                dumps += 1
                if missing_before and dumps == 1:
                    raise RuntimeError('tree unavailable')
                return 'DumpLayout saved'
            if args[:2] == ('shell', 'cat'):
                return json.dumps({'attributes': {'text': 'other page'}})
            if 'snapshot_display' in args and snapshot_failure:
                raise RuntimeError('snapshot unavailable')
            if args[:2] == ('file', 'recv'):
                Image.new('RGB', (30, 20), 'white').save(args[-1])
            return ''

        result = observe_failure(root, hdc)
        return result, read(root / result['path']), calls

    def test_failure_pair_is_diagnostic_only_and_has_hashes_and_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            save(root / 'tree-before.json', {'checkpoint': 'original failure'})
            summary, record, calls = self.observe(root)
            self.assertEqual(record['status'], 'complete')
            self.assertFalse(record['sample_eligible'])
            self.assertTrue(record['trees_equal'])
            self.assertEqual(record['image_size_px'], [30, 20])
            self.assertFalse(list(root.rglob('capture.json')))
            self.assertEqual(read(root / 'tree-before.json'), {'checkpoint': 'original failure'})
            self.assertEqual(summary['sha256'], digest((root / summary['path']).read_bytes()))
            for name, checksum in record['files'].items():
                self.assertEqual(checksum, digest((root / 'failure-evidence' / name).read_bytes()))
            self.assertEqual([step['name'] for step in record['steps']],
                             ['tree-before', 'snapshot', 'tree-after', 'image-transfer'])
            index = next(i for i, call in enumerate(calls) if 'snapshot_display' in call)
            self.assertIn('dumpLayout', calls[index + 1])
            self.assertTrue(all(not set(call) & {'install', 'start', 'uiInput', 'force-stop', 'clean'} for call in calls))

    def test_diagnostic_image_is_not_exported_as_a_dataset_sample(self):
        from truncator.review.datasets.dataset import export_dataset
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            attempt = root / 'runs' / 'capture-failed'
            attempt.mkdir(parents=True)
            self.observe(attempt)
            self.assertEqual(export_dataset(root / 'runs', root / 'export'), 0)
            self.assertEqual(read(root / 'export' / 'manifest.json')['samples'], [])

    def test_diagnostic_verification_rejects_altered_image_and_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary, record, _ = self.observe(root)
            save(root / 'failure.json', {'error': 'missing target', 'diagnostics': summary})
            self.assertEqual(validate_failure_evidence(root), record)
            image = root / 'failure-evidence/snapshot.jpeg'
            original = image.read_bytes()
            image.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'file changed'):
                validate_failure_evidence(root)
            image.write_bytes(original)
            save(root / 'failure-evidence/evidence.json', {**record, 'sample_eligible': True})
            with self.assertRaisesRegex(ValueError, 'manifest changed'):
                validate_failure_evidence(root)

    def test_missing_tree_does_not_discard_the_available_screenshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, record, _ = self.observe(Path(tmp), missing_before=True)
            self.assertEqual(record['status'], 'partial')
            self.assertIn('snapshot.jpeg', record['files'])
            self.assertIn('tree-after.json', record['files'])
            self.assertIsNone(record['trees_equal'])

    def test_snapshot_failure_does_not_fetch_a_stale_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, record, calls = self.observe(Path(tmp), snapshot_failure=True)
            self.assertEqual(record['status'], 'partial')
            self.assertNotIn('snapshot.jpeg', record['files'])
            self.assertFalse(any(call[:2] == ('file', 'recv') for call in calls))

    def test_runtime_preserves_original_failure_even_if_diagnostics_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = {'hdc': 'mock', 'bundle': 'fixture', 'hap': 'app.hap'}
            save(root / 'profile.json', profile)
            save(root / 'build.json', {'hap_sha256': digest(b'hap')})
            (root / 'project').mkdir()
            (root / 'project/app.hap').write_bytes(b'hap')
            with patch('truncator.execution.device.runtime.command', return_value=('', {})), \
                 patch('truncator.execution.device.runtime.start_application'), \
                 patch('truncator.execution.device.runtime.replay_route', side_effect=RuntimeError('original checkpoint failure')), \
                 patch('truncator.execution.device.failure_evidence.observe_failure', side_effect=OSError('diagnostic disk error')):
                with self.assertRaisesRegex(RuntimeError, 'original checkpoint failure'):
                    capture(profile, root, 'device', {}, root)
            attempt = next(root.glob('capture-*'))
            failure = read(attempt / 'failure.json')
            self.assertEqual(failure['error'], 'original checkpoint failure')
            self.assertEqual(failure['diagnostics']['status'], 'unavailable')
            self.assertFalse((attempt / 'capture.json').exists())

    def test_hap_integrity_failure_does_not_observe_unrelated_device_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = {'hdc': 'mock', 'bundle': 'fixture', 'hap': 'app.hap'}
            save(root / 'profile.json', profile)
            save(root / 'build.json', {'hap_sha256': digest(b'old hap')})
            (root / 'project').mkdir()
            (root / 'project/app.hap').write_bytes(b'changed hap')
            with patch('truncator.execution.device.runtime.command') as command, \
                 patch('truncator.execution.device.failure_evidence.observe_failure') as observe:
                with self.assertRaisesRegex(ValueError, 'HAP changed'):
                    capture(profile, root, 'device', {}, root)
                command.assert_not_called()
                observe.assert_not_called()


if __name__ == '__main__':
    unittest.main()
