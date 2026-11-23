"""Independently exercise injected viewports even when the Agent has no candidates."""
import argparse
from pathlib import Path

from truncator.execution.device.runtime import capture
from truncator.common.storage import read, save
from research.controls.evidence import (
    evidence_identity, directional_swipe, interaction_measurement,
    validate_interaction, validate_control_behavior, validate_visual_recovery,
    refresh_visual_interactions,
)


def verify_saved(output):
    """Preserve original results and recompute checks from immutable captures."""
    verified = []
    for folder in sorted(output.iterdir()):
        if not (folder / 'result.json').is_file():
            continue
        result = read(folder / 'result.json')
        try:
            for state in result['states']:
                identity = evidence_identity(state['capture'])
                if any(state[key] != value for key, value in identity.items()):
                    raise ValueError('Initial capture evidence changed')
            for action in result['interactions']:
                validate_interaction(action)
            refresh_visual_interactions(result)
            states = {state['state'] for state in result['states']}
            validate_control_behavior(result, states)
            validate_visual_recovery(result, states & {'scroll'})
            result.update(status='passed')
            result.pop('error', None)
        except (ValueError, KeyError, OSError) as error:
            result.update(status='inconclusive', error=str(error))
        save(folder / 'verification.json', result)
        verified.append(result)
        print(result['case']['id'], result['status'], result.get('error', ''), flush=True)
    save(output / 'verification.json', verified)
    return verified


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--live',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--verify-only', action='store_true')
    args=parser.parse_args()
    if args.verify_only:
        rows = verify_saved(args.out)
        raise SystemExit(0 if len(rows) == 10 and all(row['status'] == 'passed' for row in rows) else 1)
    cases=read(args.live/'cases.json')
    if not all((args.live/case['id']/'evaluation.json').exists() and
               read(args.live/case['id']/'evaluation.json')['status'] in {'complete','error'} for case in cases):
        raise RuntimeError('Wait for the Agent device run to finish before probing')
    args.out.mkdir(parents=True,exist_ok=True)
    results=[]
    for case in cases:
        observation=case['observations'][0]
        if 'control_group_id' not in observation or observation['control_state'] not in {'clipped','scroll'}: continue
        state=observation['control_state']; output=args.out/case['id']
        if (output/'result.json').exists():
            results.append(read(output/'result.json')); continue
        output.mkdir(parents=True,exist_ok=True)
        run=Path(case['run']); profile=read(run/'profile.json'); plan=read(run/'plan.json')
        axis=observation['axis']; viewport={'id':plan['parameters']['viewport_id']}
        result={'case':case,'direction':{'axis':axis},'states':[],'interactions':[],'status':'started'}
        save(output/'result.json',result)
        try:
            initial=capture(profile,run,'127.0.0.1:5555',case['recipe'],output)
            result['states']=[{'state':state,**evidence_identity(initial)}]
            previous=initial
            stages=[('forward',axis,False)]
            if state=='scroll': stages.extend([('orthogonal','vertical' if axis=='horizontal' else 'horizontal',False),('return',axis,True)])
            for stage,direction,reverse in stages:
                gesture=directional_swipe(viewport,direction,reverse)
                recipe={'actions':[gesture],'settle_seconds':2,
                        'checks':[{'selector':plan['geometry']['mutated_selector']}],
                        'targets':[{'selector':plan['geometry']['mutated_selector']}]}
                action={'state':state,'stage':stage,'actions':[gesture],'before':evidence_identity(previous)}
                result['interactions'].append(action);save(output/'result.json',result)
                current=capture(profile,run,'127.0.0.1:5555',recipe,output,continue_from=previous)
                measurement=interaction_measurement(initial,current,plan)
                action.update(status='captured',**evidence_identity(current),
                              measurement=measurement,
                              action_measurement=measurement if previous==initial else interaction_measurement(previous,current,plan))
                validate_interaction(action)
                previous=current; save(output/'result.json',result)
                print(observation['component'],axis,state,stage,action['measurement']['relative_delta_xy_px'],flush=True)
            validate_control_behavior(result,{state})
            if state=='scroll': validate_visual_recovery(result,{state})
            result['status']='passed'
        except Exception as error:
            result.update(status='inconclusive',error=str(error))
        save(output/'result.json',result);results.append(result)
        save(args.out/'summary.json',results)
        print(case['id'],result['status'],result.get('error',''),flush=True)


if __name__=='__main__': main()
