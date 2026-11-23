"""Native image format and portable evidence must survive the complete review path."""
import tempfile
import unittest
from pathlib import Path
from PIL import Image

from truncator.execution.device.acquisition import acquire
from truncator.common.capture_files import capture_image, evidence_files
from truncator.review.review_evidence import capture_hashes
from truncator.common.storage import save, digest, read


class CaptureImageTests(unittest.TestCase):
    def test_native_png_command_and_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            calls = []
            def hdc(*args):
                calls.append(args)
                if args[:2] == ('file', 'recv'):
                    Image.new('RGB', (20, 20), (111, 129, 142)).save(args[3])
            acquire(root, hdc, lambda: {})
            command = next(c for c in calls if c[:2] == ('shell', 'snapshot_display'))
            self.assertEqual(command[-2:], ('-t', 'png'))
            self.assertEqual(capture_image(root).name, 'snapshot.png')
            self.assertEqual(capture_image(root).read_bytes(), (root/'frames/0/snapshot.png').read_bytes())
            with Image.open(capture_image(root)) as image:
                self.assertEqual(image.format, 'PNG')
                self.assertEqual(image.getpixel((0, 0)), (111, 129, 142))

    def test_jpeg_payload_is_rejected_even_with_png_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def hdc(*args):
                if args[:2] == ('file', 'recv'):
                    Image.new('RGB', (20, 20), 'white').save(args[3], format='JPEG')
            with self.assertRaises(RuntimeError):
                acquire(root, hdc, lambda: {})
            self.assertFalse(capture_image(root).exists())
            self.assertEqual(read(root/'image-quality.json')['checks'][0]['measurement']['status'], 'decode_failed')
            self.assertTrue((root/'frames/0/snapshot.png').is_file())

    def test_ambiguous_primary_images_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ('snapshot.png', 'snapshot.jpeg'):
                Image.new('RGB', (20, 20)).save(root/name)
            with self.assertRaisesRegex(ValueError, 'ambiguous'):
                capture_image(root)

    def test_binding_accepts_native_or_historical_bytes_and_detects_changes(self):
        for name in ('snapshot.png', 'snapshot.jpeg'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                Image.new('RGB', (20, 20)).save(root/name)
                original = (root/name).read_bytes()
                save(root/'capture.json', {'screenshot_sha256': digest(original)})
                for tree in ('tree-before.json', 'tree-after.json'):
                    save(root/tree, {})
                self.assertEqual(set(capture_hashes(root)), set(evidence_files(root)))
                self.assertEqual((root/name).read_bytes(), original)
                (root/name).write_bytes(original + b'changed')
                with self.assertRaisesRegex(ValueError, 'screenshot changed'):
                    capture_hashes(root)

    def test_coverage_counts_observations_without_requiring_realism_grades(self):
        from truncator.review.datasets.dataset_coverage import summarize_coverage
        base = {'consensus': 'consistent', 'application_bundle': 'example.app', 'component': 'Text',
                'axis': 'vertical', 'mechanism': 'height-clip', 'label': 'positive',
                'evidence_sha256': {'screenshot': 'image', 'tree-before.json': 'before', 'tree-after.json': 'after'}}
        rows = [{**base, 'capture_sha256': str(i)} for i in range(3)]
        result = summarize_coverage(rows)
        self.assertEqual(result['target_states'], 3)
        self.assertNotIn('by_realism', result)
        self.assertEqual(result['verified_applications'], 1)
        rows[0]['consensus'] = 'conflicting'
        self.assertEqual(summarize_coverage(rows)['target_states'], 2)
