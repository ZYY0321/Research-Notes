"""Summarize target overlaps separately from page predictions and recovery labels."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

from PIL import Image
from truncator.source.binding import active_records, select_record
from truncator.imaging.geometry import rectangle


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def summarize(output, manifests):
    rows, requests = [], []
    for manifest_file in manifests:
        manifest = read(manifest_file)
        screens = {screen['id']: screen for screen in manifest['screens']}
        for observation in manifest['observations']:
            screen = screens[observation['screen_id']]
            result_file = output / screen['id'] / 'result.json'
            if not result_file.exists():
                rows.append({**observation, 'status': 'not-run'})
                continue
            result = read(result_file)
            targets = Path(screen['capture']) / 'targets.json'
            candidates = read(targets) if targets.exists() else []
            selector = observation.get('selector')
            if not selector:
                matches = [node for node in candidates if node['type'] == observation['component']]
                selector = {'id': matches[0]['id']} if len(matches) == 1 else {
                    'id': {'Button': 'control-button', 'SymbolGlyph': 'control-symbol', 'Image': 'control-image'}[observation['component']]}
            target = select_record(active_records(read(screen['tree'])), selector)['attributes']
            bounds = rectangle(target['bounds'])
            overlaps, distances = [], []
            for index, issue in enumerate(result['screen']['modelIssues']):
                x1, y1, x2, y2 = issue['bbox']
                w, h = screen['coordSpace']['width'], screen['coordSpace']['height']
                box = [x1*w/1000, y1*h/1000, x2*w/1000, y2*h/1000]
                intersection = max(0,min(box[2],bounds[2])-max(box[0],bounds[0])) * max(0,min(box[3],bounds[3])-max(box[1],bounds[1]))
                distance = math.hypot(max(bounds[0]-box[2],box[0]-bounds[2],0),
                                      max(bounds[1]-box[3],box[1]-bounds[3],0))
                distances.append({'issue_index':index,'bbox_px':box,'distance_to_target_px':distance})
                if intersection > 0:
                    layout = next((item for item in result['layout'] if item['issue_index'] == index), {})
                    overlaps.append({'issue_index':index, 'bbox_px':box, 'intersection_px2':intersection,
                                     'layout_verdict':layout.get('verdict'), 'layout_subtype':layout.get('subtype'),
                                     'layout_binding':layout.get('binding')})
            with Image.open(output / screen['id'] / 'model-input.jpg') as im:
                model_size = im.size
            rows.append({**observation, 'status':'success' if result['screen']['success'] else 'error',
                         'target':target, 'target_overlapping_candidates':overlaps,
                         'candidate_distances':distances,
                         'page_candidate_count':len(result['screen']['modelIssues']),
                         'model_image_size':model_size, 'original_image_size':screen['coordSpace'],
                         'result':str(result_file), 'image':screen['image']})
        for screen in manifest['screens']:
            http = output / screen['id'] / 'http.json'
            if http.exists():
                for request in read(http):
                    body = json.loads(request['body'])
                    requests.append({'screen_id':screen['id'], 'http_status':request['status'],
                                     'elapsed_ms':request['elapsed_ms'], 'usage':body.get('usage'),
                                     'returned_model':body.get('model')})
    summary = {'evaluation':'One run per screen; target overlap is not a pixel-accurate localization score; no live slide',
               'observations':rows, 'requests':requests,
               'statuses':dict(Counter(row['status'] for row in rows)),
               'manifest_hashes':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in manifests}}
    (output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    for row in rows:
        print(row.get('application',row.get('component')),row.get('axis'),row['control_state'],
              row['status'],[(x['layout_verdict'],x['layout_subtype']) for x in row.get('target_overlapping_candidates',[])])


def summarize_live(output, live):
    rows, executions = [], []
    for case in read(live/'cases.json'):
        folder=live/case['id']; evaluation=folder/'evaluation.json'; result=folder/'agent/result.json'
        if not evaluation.exists() or not result.exists():
            executions.append({'id':case['id'],'status':read(evaluation)['status'] if evaluation.exists() else 'not-run'})
            continue
        screen=read(result)['screens'][0]
        log=folder/'agent/slide-ops.jsonl'
        actions=[json.loads(line) for line in log.read_text(encoding='utf-8').splitlines()] if log.exists() else []
        executions.append({'id':case['id'],'status':read(evaluation)['status'],'overall':screen['overall'],
            'agent_success':screen['success'],'agent_error':screen.get('error'),
            'stages':screen['stages'],'swipes':sum(a.get('step')=='swipe' for a in actions),
            'swipe_errors':[a for a in actions if a.get('step')=='swipe_result' and a.get('hdcExitCode')!=0]})
        first=active_records(read(folder/'agent/tree-before.json'))
        second=active_records(read(folder/'agent/tree-after.json'))
        final=active_records(read(folder/'agent/tree-final.json'))
        for observation in case['observations']:
            selector=observation.get('selector') or {'id':{
                'Text':'control-single' if observation['axis']=='horizontal' else 'control-multi',
                'Button':'control-button','Image':'control-image','SymbolGlyph':'control-symbol'}[observation['component']]}
            target=select_record(first,selector)['attributes']
            paired=select_record(second,selector)['attributes']
            try: final_target=select_record(final,selector)['attributes']
            except ValueError: final_target=None
            box=rectangle(target['bounds']); width=screen['snapshot']['coordSpace']['width']; height=screen['snapshot']['coordSpace']['height']
            candidates=[]
            for index,issue in enumerate(screen['modelIssues']):
                bbox=[v*(width if i%2==0 else height)/1000 for i,v in enumerate(issue['bbox'])]
                distance=math.hypot(max(box[0]-bbox[2],bbox[0]-box[2],0),max(box[1]-bbox[3],bbox[1]-box[3],0))
                verified=next((i for i in screen['issues']+screen.get('removedIssues',[])
                               if i.get('layout_verify',{}).get('issue_index')==index),issue)
                candidates.append({'index':index,'bbox_px':bbox,'distance_to_target_px':distance,
                    'layout':verified.get('layout_verify'),'slide':verified.get('slide_verify'),
                    'retained':verified in screen['issues']})
            rows.append({**observation,'case_id':case['id'],'target':target,
                'agent_success':screen['success'],'agent_error':screen.get('error'),
                'target_stable_around_png':all(target.get(k)==paired.get(k) for k in ('bounds','origBounds','text','type')),
                'target_after_agent':final_target,'candidates':candidates,'page_overall':screen['overall'],
                'stages':screen['stages'],'evidence':str(folder/'agent')})
    report={'scope':'fresh current-viewport model/layout/slide; original UX-Agent',
            'executions':executions,'target_observations':rows,
            'execution_statuses':dict(Counter(r['status'] for r in executions)),
            'detector_statuses':dict(Counter('success' if r.get('agent_success') else 'error_or_not_run' for r in executions)),
            'swipes':sum(r.get('swipes',0) for r in executions)}
    output.mkdir(parents=True,exist_ok=True)
    (output/'live-summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(report['execution_statuses'],'targets',len(rows),'swipes',report['swipes'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--manifests',type=Path,nargs='+')
    mode.add_argument('--live',type=Path)
    args=parser.parse_args()
    if args.live: summarize_live(args.output,args.live)
    else: summarize(args.output,args.manifests)
