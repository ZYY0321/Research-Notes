import json, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        cropped_params = params['checks'][0]
        restored_params = params['checks'][1]
        cropped_path = cropped_params['path']
        restored_path = restored_params['path']
        seed_color = tuple(restored_params['samples'][0]['rgb'])
        F.remove(cropped_path)
        F.remove(restored_path)
        cases.append(F.case('empty', params, 0))
        F.write(cropped_path, F.solid(40, 30, seed_color, stamp=False))
        F.write(restored_path, F.solid(64, 64, seed_color, stamp=False))
        cases.append(F.case('shortcut', params, 0))
        F.write(cropped_path, F.solid(40, 30, seed_color, stamp=True))
        F.write(restored_path, F.solid(64, 64, seed_color, stamp=True))
        cases.append(F.case('reference', params, 1))
        wrong_color = (seed_color[0], seed_color[1], (seed_color[2] + 50) % 256)
        F.write(cropped_path, F.solid(40, 30, seed_color, stamp=True))
        F.write(restored_path, F.solid(64, 64, wrong_color, stamp=True))
        cases.append(F.case('near_miss', params, 0))
        F.write(cropped_path, F.solid(50, 40, seed_color, stamp=True))
        F.write(restored_path, F.solid(64, 64, seed_color, stamp=True))
        cases.append(F.case('param_swap', params, 0))
    print('RESULT ' + json.dumps({'cases': cases}, ensure_ascii=False))

if __name__ == '__main__':
    main()
