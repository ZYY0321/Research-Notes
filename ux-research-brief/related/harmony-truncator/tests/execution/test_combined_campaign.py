import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from truncator.execution.campaign import campaign
from truncator.common.storage import read, save


class CombinedCampaignTests(unittest.TestCase):
    def run_fixture(self, root, build_fails=False):
        save(root / 'profile.json', {})
        pages = []
        for index in range(3):
            recipe = root / f'recipe-{index}.json'
            save(recipe, {'page': index})
            pages.append({'name': str(index), 'recipe': str(recipe)})
        spec = {'applications': [{'profile': str(root / 'profile.json'),
                                 'operators': ['height-clip', 'fixed-parent-clip'], 'pages': pages}]}
        catalog = {'sites': [{'id': 'target', 'operators': ['height-clip', 'fixed-parent-clip']}]}
        combined = {'id': 'combined', 'pages': [{'name': str(i), 'mutation_ids': ['selected']} for i in range(3)]}
        capture_dir = root / 'capture'
        save(capture_dir / 'tree-before.json', {})
        def run_batch(profile, plans, destination, device=None, recipe=None):
            return [{'plan': str(plans[0]), 'run': str(root / 'run'),
                     'status': 'failed' if build_fails else 'captured' if device else 'built'}]
        with patch('truncator.execution.campaign.prepare_application', return_value=({}, catalog, root / 'baseline')) as prepare, \
             patch('truncator.execution.campaign.latest_capture', return_value=capture_dir), \
             patch('truncator.execution.campaign.bind_candidates', return_value={'bindings': [{'site': 'target'}]}), \
             patch('truncator.execution.campaign.load_baseline') as load, \
             patch('truncator.execution.campaign.plan_from_baseline', return_value=[{'id': 'candidate'}]) as plan, \
             patch('truncator.execution.campaign.select_combination', return_value=([{'id': 'selected'}], {})), \
             patch('truncator.execution.campaign.compose', return_value=combined), \
             patch('truncator.execution.campaign.batch', side_effect=run_batch) as batch, \
             patch('truncator.review.reporting.evidence.generate_report'):
            results = campaign(spec, root / 'output', 'device')
        prepare.assert_called_once()
        self.assertEqual(load.call_count, 3)  # one per target/page, reused by both operators
        self.assertEqual(plan.call_count, 6)
        return results, batch.call_count

    def test_one_source_preparation_and_shared_package_for_three_routes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            results, calls = self.run_fixture(root)
            self.assertEqual(results[0]['status'], 'captured')
            self.assertEqual(calls, 4)  # one build-only batch, then three captures
            queue = read(root / 'output/review-queue.json')['applications']
            self.assertEqual(len(queue), 1)
            self.assertEqual(len(queue[0]['page_captures']), 3)

    def test_build_failure_is_not_repeated_for_each_page(self):
        with tempfile.TemporaryDirectory() as directory:
            results, calls = self.run_fixture(Path(directory), build_fails=True)
            self.assertEqual(calls, 1)
            self.assertEqual(results[0]['status'], 'failed')
            self.assertTrue(all(page['status'] == 'failed' for page in results[0]['pages']))
