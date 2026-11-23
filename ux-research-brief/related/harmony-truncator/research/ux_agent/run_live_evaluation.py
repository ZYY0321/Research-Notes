"""Restore immutable built variants, then run the original Agent on the live viewport."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

from truncator.execution.device.runtime import capture
from truncator.common.storage import read, save, digest
from truncator.review.review_evidence import capture_hashes
from truncator.review.review_policy import validate_observation_labels


def isolate_case(run, screen_id, recipe, observations, destination, expected_hap):
    profile = read(run/'profile.json')
    isolated = destination/screen_id/'run'
    isolated.mkdir(parents=True, exist_ok=True)
    for name in ('profile.json', 'build.json', 'plan.json'):
        if (run/name).exists(): shutil.copy2(run/name, isolated/name)
    hap = isolated/'project'/profile['hap']
    hap.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(run/'project'/profile['hap'], hap)
    if digest(hap.read_bytes()) != expected_hap:
        raise ValueError('Evaluation HAP differs from the reviewed capture')
    return {'id': screen_id, 'run': str(isolated), 'original_run': str(run),
            'recipe': recipe, 'observations': observations}


def prepare_controls(groups, destination):
    """Reuse completed control runs, sharing one model call for a shared frame."""
    screens = {}
    for group in groups:
        group = Path(group)
        result, definition = read(group/'control-results.json'), read(group/'control-group.json')
        if not result['complete']:
            raise ValueError('Control acquisition is not complete: ' + str(group))
        review = read(group/'evaluation-review.json')
        if not review.get('reviewer'):
            raise ValueError('Evaluation needs a visual reviewer')
        selector = definition['selector']
        for state in result['states']:
            capture_dir = Path(state['capture'])
            record = read(capture_dir/'capture.json')
            key = digest((capture_dir/'capture.json').read_bytes())
            screen = screens.setdefault(key, {'run': capture_dir.parent, 'record': record, 'observations': []})
            name = state['state']
            labels = review['states'][name]
            if labels['sha256'] != capture_hashes(capture_dir):
                raise ValueError('Evaluation labels belong to another capture')
            validate_observation_labels(labels['content_status'], labels['recovery_status'])
            if (name in {'clipped', 'scroll'} and result['behavior_checks'][name]['status'] != 'passed'
                    and labels['recovery_status'] not in {'inconclusive', 'not-tested'}):
                raise ValueError('Unresolved control evidence cannot receive a recovery verdict')
            screen['observations'].append({'screen_id': key, 'component': selector['type'],
                'selector': selector, 'control_group_id': definition['id'], 'control_state': name,
                'axis': result['direction']['axis'], 'content_status': labels['content_status'],
                'recovery_status': labels['recovery_status'], 'reviewer': review['reviewer'],
                'label_evidence': str(group/'evaluation-review.json'),
                'label_evidence_sha256': digest((group/'evaluation-review.json').read_bytes())})
    cases = [isolate_case(s['run'], key, s['record']['recipe'], s['observations'], destination,
                          s['record']['hap_sha256']) for key, s in screens.items()]
    save(destination/'cases.json', cases)
    return cases


def prepare_cases(project, destination):
    controls = read(project/'artifacts/ux-agent-commercial-20261118/manifest.json')
    apps = read(project/'artifacts/ux-agent-qwen-20261118-eval/real-app-manifest.json')
    runs = {}
    for group in [
        Path('E:/HarmonyDev/MutationRuns/directional-controls-20261117')/name for name in ('single','multi')
    ] + [Path('E:/HarmonyDev/MutationRuns/content-controls-20261118')/name for name in ('symbol','image','button-visible')]:
        result = read(group/'control-results.json')
        for state in result['states']:
            run = Path(state['capture']).parent if state['state']=='normal' else Path(state['batch']['run'])
            runs[read(run/'build.json')['hap_sha256']] = run
    for row in read(project/'artifacts/application-recovery-20261118/results.json'):
        run=Path(row['plan']).parent
        runs[read(run/'build.json')['hap_sha256']]=run
        baseline=Path(read(run/'plan.json')['geometry']['baseline_capture']).parent
        runs[read(baseline/'build.json')['hap_sha256']]=baseline
    # Later controlled re-runs have different built packages from their first trial.
    # Resolve by immutable HAP hash, never by a similarly named group directory.
    for base, dirs, files in os.walk('E:/HarmonyDev/MutationRuns'):
        if Path(base).resolve().is_relative_to(destination.resolve()):
            dirs.clear(); continue
        dirs[:] = [d for d in dirs if d not in {'project','source','node_modules','oh_modules','.git','report'} and not d.startswith('capture-')]
        if 'build.json' not in files or 'profile.json' not in files: continue
        run=Path(base)
        try:
            build=read(run/'build.json'); profile=read(run/'profile.json')
            if (run/'project'/profile['hap']).is_file(): runs[build['hap_sha256']]=run
        except (KeyError,ValueError,OSError): continue
    cases=[]
    for manifest in (controls,apps):
        for screen in manifest['screens']:
            record=read(Path(screen['capture'])/'capture.json')
            run=runs[record['hap_sha256']]
            cases.append(isolate_case(run, screen['id'], record['recipe'],
                [o for o in manifest['observations'] if o['screen_id']==screen['id']], destination, record['hap_sha256']))
    save(destination/'cases.json',cases)
    return cases


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--limit',type=int,default=26)
    parser.add_argument('--device',default='127.0.0.1:5555')
    parser.add_argument('--controls', type=Path, nargs='+', help='Completed control-group run directories')
    args=parser.parse_args()
    project=Path(__file__).resolve().parents[2]
    output=args.out.resolve(); output.mkdir(parents=True,exist_ok=True)
    cases=read(output/'cases.json') if (output/'cases.json').exists() else (
        prepare_controls(args.controls, output) if args.controls else prepare_cases(project,output))
    agent=Path('D:/Projects/UX-testing/UX-Agent-latest/HarmonyArena-fdu_agent')
    environment=os.environ.copy(); environment['HDC_TARGET']=args.device
    environment['PATH']='E:/HarmonyDev/DevEcoStudio/sdk/default/openharmony/toolchains;'+environment['PATH']
    for case in cases[:args.limit]:
        folder=output/case['id']; status=folder/'evaluation.json'
        if status.exists():
            print(case['id'],'recorded; preserving prior attempt',flush=True); continue
        result={'case':case,'status':'started'}; save(status,result)
        try:
            run=Path(case['run']); profile=read(run/'profile.json')
            initial=capture(profile,run,args.device,case['recipe'],output)
            result['initial_capture']=str(initial); save(status,result)
            completed=subprocess.run(['node',str(agent/'node_modules/tsx/dist/cli.mjs'),
                str(project/'research/ux_agent/live_ux_agent.mjs'),str(agent),str(folder/'agent')],
                env=environment,capture_output=True,text=True,encoding='utf-8',timeout=900)
            (folder/'agent.log').write_text(completed.stdout+'\n'+completed.stderr,encoding='utf-8')
            if completed.returncode: raise RuntimeError('Agent process failed; see agent.log')
            result['status']='complete'
        except Exception as error:
            result.update(status='error',error=str(error))
        save(status,result)
        print(case['id'],result['status'],result.get('error',''),flush=True)


if __name__=='__main__': main()
