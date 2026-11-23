import copy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from PIL import Image, ImageDraw
from research.ux_agent.target_evaluation import evaluate_row, summarize
from truncator.planning.parameter_policy import control_direction
from truncator.imaging.content_identity import compare_visible


class TargetEvaluationTests(unittest.TestCase):
    def row(self, box=(91, 12, 105, 28)):
        return {'component': 'Text', 'axis': 'horizontal', 'content_status': 'clipped',
                'recovery_status': 'not-recovered', 'target_stable_around_png': True, 'agent_success': True,
                'target': {'id': 'a', 'bounds': '[10,10][100,30]'},
                'candidates': [{'bbox_px': list(box), 'retained': True, 'layout': None}]}

    def test_wrong_side_of_same_target_is_localization_failure(self):
        result = evaluate_row(self.row((10, 12, 20, 28)), 'right', 4)
        self.assertTrue(result['candidate_target_hit'])
        self.assertEqual(result['failure_stage'], 'wrong_edge')
        self.assertEqual(result['outcome'], 'FN')

    def test_edge_candidate_and_layout_suppression_are_separate(self):
        row = self.row()
        self.assertEqual(evaluate_row(row, 'right', 4)['outcome'], 'TP')
        row['candidates'][0].update(retained=False, layout={'verdict': 'ok'})
        self.assertEqual(evaluate_row(row, 'right', 4)['failure_stage'], 'layout_suppression')

    def test_whole_page_box_does_not_count_as_localized_target(self):
        self.assertEqual(evaluate_row(self.row((0, 0, 1000, 1000)), 'right')['failure_stage'], 'other_target')

    def test_whole_target_box_is_not_precise_edge_localization(self):
        self.assertEqual(evaluate_row(self.row((10, 10, 100, 30)), 'right', 4)['failure_stage'], 'wrong_edge')

    def test_recoverable_clipping_is_final_negative(self):
        row = self.row()
        row['recovery_status'] = 'recovered'
        self.assertEqual(evaluate_row(row, 'right')['outcome'], 'FP')
        row['candidates'][0]['retained'] = False
        self.assertEqual(evaluate_row(row, 'right')['outcome'], 'TN')

    def test_unknown_recovery_and_unstable_capture_are_unscored(self):
        row = self.row()
        row['recovery_status'] = 'unknown'
        self.assertEqual(evaluate_row(row, 'right')['outcome'], 'unscored')
        row['recovery_status'] = 'not-recovered'
        row['target_stable_around_png'] = False
        self.assertEqual(evaluate_row(row, 'right')['outcome'], 'unscored')

    def test_text_scope_excludes_image_controls(self):
        text = evaluate_row(self.row(), 'right')
        picture = copy.deepcopy(text)
        picture['component'] = 'Image'
        metrics = summarize([text, picture])
        self.assertEqual(metrics['text_scope']['observations'], 1)
        self.assertEqual(metrics['nontext_controls']['observations'], 1)

    def test_detector_error_is_not_a_true_negative(self):
        row = self.row()
        row.update(content_status='complete', recovery_status='not-applicable', agent_success=False, candidates=[])
        result = evaluate_row(row)
        self.assertEqual(result['outcome'], 'unscored')
        self.assertEqual(result['failure_stage'], 'detector_error_or_unverified')


class ButtonDirectionTests(unittest.TestCase):
    def infer(self, lines, kind='Button', text='label', axis='auto'):
        with tempfile.TemporaryDirectory() as tmp:
            image = Image.new('RGB', (200, 120), 'white')
            draw = ImageDraw.Draw(image)
            for y in lines:
                draw.rectangle((25, y, 170, y + 14), fill='black')
            image.save(Path(tmp) / 'snapshot.jpeg', quality=100)
            baseline = SimpleNamespace(capture_dir=Path(tmp), bounds=[0, 0, 200, 120], density=1,
                site={'component': kind}, target={'attributes': {'text': text}})
            return control_direction(baseline, axis)

    def test_multiline_button_uses_rendered_rows(self):
        result = self.infer([25, 65])
        self.assertEqual(result['axis'], 'vertical')
        self.assertEqual(result['basis'], 'rendered_text_rows')

    def test_single_line_and_explicit_override(self):
        self.assertEqual(self.infer([45])['axis'], 'horizontal')
        result = self.infer([25, 65], axis='horizontal')
        self.assertEqual(result['axis'], 'horizontal')
        self.assertTrue(result['explicit_override'])

    def test_image_and_empty_button_are_not_read_as_text_rows(self):
        self.assertEqual(self.infer([25, 65], kind='Image')['axis'], 'horizontal')
        self.assertEqual(self.infer([25, 65], text='')['axis'], 'horizontal')


class PixelUncertaintyTests(unittest.TestCase):
    def compare(self, lost_color):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reference = Image.new('RGB', (80, 60), 'white')
            ImageDraw.Draw(reference).rectangle((15, 15, 25, 40), fill='black')
            current = reference.copy()
            reference.putpixel((50, 25), (lost_color,) * 3)
            reference.save(root / 'reference.png')
            current.save(root / 'current.png')
            return compare_visible(root / 'reference.png', root / 'current.png',
                                   [0, 0, 80, 60], [0, 0, 80, 60], [0, 0, 80, 60], text=True)

    def test_weak_ink_disagreement_is_unknown_not_accepted(self):
        result = self.compare(205)
        self.assertEqual(result['status'], 'unknown')
        self.assertEqual(result['reason'], 'low_contrast_ink_disagreement')
        self.assertEqual(result['missing_pixels'], 1)

    def test_one_high_contrast_missing_pixel_is_still_different(self):
        self.assertEqual(self.compare(100)['status'], 'different')
