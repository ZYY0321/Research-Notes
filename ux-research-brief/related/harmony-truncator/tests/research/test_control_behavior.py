"""Reject action evidence that cannot support directional control labels."""
import copy
import unittest
import tempfile
from pathlib import Path

from research.controls.evidence import validate_control_behavior, validate_interaction, evidence_identity
from truncator.common.storage import save, digest, read


def group(axis='horizontal'):
    index=0 if axis=='horizontal' else 1
    result={'direction':{'axis':axis},'states':[{'state':'scroll','capture':'initial'}], 'interactions':[]}
    previous='initial'
    for name,position,step in [('forward',-40,-40),('orthogonal',-40,0),('return',1,41)]:
        moving=1-index if name=='orthogonal' else index
        start,end=[0.5,0.5],[0.5,0.5]
        start[moving],end[moving]=(0.15,0.85) if name=='return' else (0.85,0.15)
        displacement=[0,0]; displacement[index]=position
        change=[0,0]; change[index]=step
        m={'same_content':True,'same_extent':True,'relative_delta_xy_px':displacement,
           'viewport_delta_xy_px':[0,0],'foreground_coverage':{'status':'covered'}}
        result['interactions'].append({'state':'scroll','stage':name,'status':'captured',
            'before':{'capture':previous},'capture':name,
            'actions':[{'kind':'swipe','from':start,'to':end}],
            'measurement':m,'action_measurement':{**m,'relative_delta_xy_px':change}})
        previous=name
    return result


class ControlBehaviorTests(unittest.TestCase):
    def test_declared_gesture_must_equal_actual_capture_recipe(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            gesture={'kind':'swipe','selector':{'id':'viewport'},'from':[.8,.5],'to':[.2,.5]}
            session={'status':'verified','process':{'pid':12,'start_ticks':100}}
            for name in ('before','after'):
                folder=root/name; folder.mkdir()
                (folder/'snapshot.jpeg').write_bytes(b'frame')
                for tree in ('tree-before.json','tree-after.json'): save(folder/tree,{})
                save(folder/'capture.json',{'screenshot_sha256':digest(b'frame'),'hap_sha256':'hap',
                    'session':session,'recipe':{'actions':[gesture]}})
            previous=evidence_identity(root/'before')
            record=read(root/'after/capture.json')
            record['continued_from']={'capture':previous['capture'],'capture_sha256':previous['sha256']['capture.json']}
            save(root/'after/capture.json',record)
            action={**evidence_identity(root/'after'),'before':previous,'actions':[gesture]}
            attrs={'id':'viewport','bounds':'[0,0][100,100]'}
            save(root/'after/action-before-000.json',{'attributes':attrs})
            save(root/'after/replay.json',[{'index':0,'phase':'route','action':gesture,
                'status':'dispatched','location_wait':{'ready':True},'matches':[attrs],
                'arguments':['swipe','80','50','20','50','600']}])
            validate_interaction(action)
            action['actions']=[{'kind':'swipe','from':[.5,.8],'to':[.5,.2]}]
            with self.assertRaisesRegex(ValueError,'recipe actions'): validate_interaction(action)

    def test_both_axes_allow_one_pixel_return_rounding(self):
        for axis in ('horizontal','vertical'):
            validate_control_behavior(group(axis),{'scroll'})

    def test_missing_return_is_not_a_complete_directional_trial(self):
        result=group(); result['interactions'].pop()
        with self.assertRaisesRegex(ValueError,'sequence'):
            validate_control_behavior(result,{'scroll'})

    def test_wrong_axis_cannot_support_recovery(self):
        result=group('vertical')
        result['interactions'][0]['actions']=group()['interactions'][0]['actions']
        with self.assertRaisesRegex(ValueError,'axis'):
            validate_control_behavior(result,{'scroll'})

    def test_stage_cannot_restart_from_an_earlier_frame(self):
        result=group(); result['interactions'][-1]['before']['capture']='initial'
        with self.assertRaisesRegex(ValueError,'preceding'):
            validate_control_behavior(result,{'scroll'})

    def test_orthogonal_motion_and_failed_return_are_rejected(self):
        for stage,field in [(1,'action_measurement'),(2,'measurement')]:
            result=group(); result['interactions'][stage][field]['relative_delta_xy_px']=[8,0]
            with self.assertRaises(ValueError): validate_control_behavior(result,{'scroll'})

    def test_content_switch_and_viewport_motion_are_rejected(self):
        for field,value in [('same_content',False),('viewport_delta_xy_px',[0,40])]:
            result=group(); result['interactions'][0]['measurement'][field]=value
            with self.assertRaises(ValueError): validate_control_behavior(result,{'scroll'})

    def test_static_control_needs_missing_content_and_no_motion(self):
        result=group(); result['states']=[{'state':'clipped','capture':'initial'}]
        action=result['interactions'][0]; result['interactions']=[action]; action['state']='clipped'
        action['measurement']['relative_delta_xy_px']=[0,0]
        action['measurement']['foreground_coverage']={'status':'incomplete'}
        validate_control_behavior(result,{'clipped'})
        bad=copy.deepcopy(result); bad['interactions'][0]['measurement']['foreground_coverage']['status']='covered'
        with self.assertRaisesRegex(ValueError,'missing content'):
            validate_control_behavior(bad,{'clipped'})


if __name__=='__main__': unittest.main()
