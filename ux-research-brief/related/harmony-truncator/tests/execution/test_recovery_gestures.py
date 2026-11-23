import unittest
from truncator.execution.device.recovery_gestures import plan_swipe
from truncator.execution.device.replay import resolve_action, action_arguments, action_matches


def tree(*obstacles, clickable=False):
    return {"attributes":{"id":"viewport","bounds":"[0,0][400,600]","clickable":str(clickable).lower()},
            "children":[{"attributes":{"id":"target","bounds":"[310,30][390,60]"}},
                        *[{"attributes":{"id":str(i),"bounds":box,"clickable":"true"}} for i,box in enumerate(obstacles)]]}


class RecoveryGestureTests(unittest.TestCase):
    def plan(self,value,axis='horizontal',reverse=False):
        return plan_swipe(value,{'id':'target'},{'id':'viewport'},axis,reverse)

    def test_target_near_top_does_not_swipe_center_product(self):
        result=self.plan(tree('[0,200][400,500]'))
        self.assertEqual(result['status'],'planned')
        self.assertEqual(result['pixel_from'][1],45)
        self.assertLess(result['pixel_to'][0],result['pixel_from'][0])

    def test_clickable_target_uses_nearby_clear_track(self):
        result=self.plan(tree('[300,30][400,60]'))
        self.assertEqual(result['status'],'planned')
        self.assertTrue(result['pixel_from'][1]<22 or result['pixel_from'][1]>68
                        or max(result['pixel_from'][0],result['pixel_to'][0])<292)

    def test_clickable_ancestor_does_not_fall_back_to_center(self):
        self.assertEqual(self.plan(tree(clickable=True))['status'],'unavailable')

    def test_return_reverses_direction_and_vertical_stays_vertical(self):
        for axis in ('horizontal','vertical'):
            first=self.plan(tree(),axis);back=self.plan(tree(),axis,True)
            cross=1 if axis=='horizontal' else 0
            along=1-cross
            self.assertLess(first['pixel_to'][along],first['pixel_from'][along])
            self.assertGreater(back['pixel_to'][along],back['pixel_from'][along])
            self.assertEqual(first['pixel_from'][cross],first['pixel_to'][cross])

    def test_live_resolution_uses_new_obstacle_observation(self):
        action={'kind':'swipe','selector':{'id':'viewport'},'recovery_target':{'id':'target'},'axis':'horizontal'}
        resolved,plan=resolve_action(action,tree())
        self.assertEqual(action_arguments(resolved,'[0,0][400,600]')[1:3],list(map(str,plan['pixel_from'])))
        with self.assertRaisesRegex(ValueError,'unavailable'):
            resolve_action(action,tree(clickable=True))

    def test_unrelated_container_cannot_receive_target_probe(self):
        with self.assertRaisesRegex(ValueError,'match once'):
            plan_swipe(tree(),{'id':'target'},{'id':'elsewhere'},'horizontal')

    def test_contextual_anchor_ignores_other_page_containers(self):
        value={'children':[tree(),{'attributes':{'id':'viewport','bounds':'[0,700][400,900]'}}]}
        action={'kind':'swipe','selector':{'id':'viewport'},'recovery_target':{'id':'target'},'axis':'horizontal'}
        self.assertEqual(len(action_matches(value,action)),1)
        self.assertEqual(action_matches(value,action)[0]['bounds'],'[0,0][400,600]')

    def test_swipe_ends_stay_out_of_screen_edge_band(self):
        result=self.plan(tree())
        inset=result['screen_inset_px']
        for point in (result['pixel_from'],result['pixel_to']):
            self.assertGreaterEqual(point[0],inset)
            self.assertLessEqual(point[0],400-inset)

    def test_vertical_probe_limits_travel_to_keep_target_observable(self):
        result=self.plan(tree(),'vertical')
        self.assertLessEqual(abs(result['pixel_from'][1]-result['pixel_to'][1]),52)
