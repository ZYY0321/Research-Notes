"""Paired native PNG/JPEG repeats around verified button recovery states."""
import argparse
import json
import tempfile
from pathlib import Path
from truncator.execution.device.commands import command
from truncator.common.locking import lock
from truncator.execution.device.runtime import capture
from truncator.common.storage import read, save, digest
from truncator.execution.device.acquisition import target_state
from research.controls.evidence import directional_swipe


def burst(profile, capture_dir, output, selectors, device):
    output.mkdir(parents=True)
    counter = 0
    def hdc(*args):
        nonlocal counter
        counter += 1
        return command([profile['hdc'], '-t', device, *args], output/f'command-{counter:03d}.log', timeout=60)[0]
    remote = '/data/local/tmp/encoding-' + digest(str(output))[:12]
    def tree():
        hdc('shell', 'uitest', 'dumpLayout', '-p', remote+'.json')
        return json.loads(hdc('shell', 'cat', remote+'.json'))
    rows = []
    with lock(Path(tempfile.gettempdir())/'harmony-truncator/locks'/('device-'+digest(device)[:16]+'.lock')):
        for index in range(3):
            before = tree()
            files = {}
            for extension in ('png', 'jpeg'):
                path = output / f'{index}.{extension}'
                args = ('-t', 'png') if extension == 'png' else ()
                hdc('shell', 'snapshot_display', '-f', remote+'.'+extension, *args)
                hdc('file', 'recv', remote+'.'+extension, str(path))
                files[extension] = {'path': str(path), 'sha256': digest(path.read_bytes())}
            after = tree()
            save(output/f'{index}-before.json', before)
            save(output/f'{index}-after.json', after)
            first, second = target_state(before, selectors), target_state(after, selectors)
            rows.append({'index': index, 'targets_stable': first[0] and second[0] and first[1] == second[1],
                         'files': files, 'targets': first[1]})
            save(output/'repeats.json', {'capture': str(capture_dir), 'samples': rows})
    if not all(r['targets_stable'] for r in rows):
        raise ValueError('Targets changed during encoding probe')


def run(root, output, device):
    output.mkdir(parents=True, exist_ok=False)
    single = read(root/'single/control-results.json')
    normal = Path(single['states'][0]['capture'])
    baseline = normal.parent
    profile = read(baseline/'profile.json')
    recipe = read(normal/'capture.json')['recipe']
    normal = capture(profile, baseline, device, recipe, output)
    targets = [{'selector': {'id': 'label-'+name}} for name in ('single', 'multi')]
    burst(profile, normal, output/'normal', targets, device)
    records = [{'name': 'normal', 'capture': str(normal), 'burst': str(output/'normal')}]
    save(output/'results.json', records)
    for name, state_name in (('single', 'clipped'), ('single', 'scroll'), ('multi', 'scroll')):
        result = read(root/name/'control-results.json')
        state = next(s for s in result['states'] if s['state'] == state_name)
        old_capture = Path(state['capture'])
        app = old_capture.parent
        plan, profile = read(app/'plan.json'), read(app/'profile.json')
        recipe = read(old_capture/'capture.json')['recipe']
        current = capture(profile, app, device, recipe, output)
        selector = plan['geometry']['mutated_selector']
        viewport = {'id': plan['parameters']['viewport_id']}
        axis = result['direction']['axis']
        steps = [('initial', None), ('forward', directional_swipe(viewport, axis))]
        if state_name == 'scroll':
            steps.extend([('orthogonal', directional_swipe(viewport, 'vertical' if axis == 'horizontal' else 'horizontal')),
                          ('return', directional_swipe(viewport, axis, True))])
        for stage, action in steps:
            if action:
                recipe = {'actions':[action], 'settle_seconds':2, 'checks':[{'selector':selector}],
                          'targets':[{'selector':selector}]}
                current = capture(profile, app, device, recipe, output, continue_from=current)
            label = name+'-'+state_name+'-'+stage
            burst(profile, current, output/label, [{'selector':selector}], device)
            records.append({'name':label, 'capture':str(current), 'burst':str(output/label),
                            'plan':str(app/'plan.json'), 'selector':selector, 'stage':stage, 'state':state_name})
            save(output/'results.json', records)
            print(label, '3 native PNG/JPEG pairs stable', flush=True)
    return records


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--device', default='127.0.0.1:5555')
    args = parser.parse_args()
    run(args.root, args.out, args.device)
