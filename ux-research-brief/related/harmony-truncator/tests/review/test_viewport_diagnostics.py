import tempfile
import unittest
from pathlib import Path
from truncator.review.diagnostics import diagnose, assess_capture
from truncator.common.storage import save


class ViewportDiagnosticsTests(unittest.TestCase):
    def test_static_size_plan_requires_replanning_after_window_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            save(folder / 'geometry-observation.json', {
                'status': 'measured', 'image_comparison': 'screen_size_changed',
                'target': {'type': 'Text'}, 'bounds_equal': True,
                'clipped_edges_px': {'bottom': 12},
            })
            plan = {'operator': 'height-clip', 'geometry': {'baseline_capture': 'deliberately-unreadable'}}
            result = diagnose(plan, folder)
            self.assertIn('baseline_viewport_changed', result['flags'])
            self.assertEqual(result['severity'], 'unresolved')
            self.assertNotIn('foreground_pixel_ratio', result)
            self.assertEqual(assess_capture(folder)['next_action'], 'replan_for_current_viewport')

    def test_intentional_window_experiment_still_has_no_cross_size_pixel_ratio(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            save(folder / 'geometry-observation.json', {
                'status': 'measured', 'image_comparison': 'screen_size_changed',
                'target': {'type': 'Text'}, 'clipped_edges_px': {'right': 20},
            })
            result = diagnose({'operator': 'cache-viewport-width', 'geometry': {'baseline_capture': 'unreadable'}}, folder)
            self.assertNotIn('baseline_viewport_changed', result['flags'])
            self.assertNotIn('foreground_pixel_ratio', result)
