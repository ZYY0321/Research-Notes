import json, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix='e31gen-') as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params['path']
        F.remove(out)
        cases.append(F.case('empty', params, 0))
        F.write(out, F.solid(48, 48, (255, 0, 0), stamp=False))
        cases.append(F.case('shortcut', params, 0))
        F.write(out, F.solid(48, 48, (255, 0, 0), stamp=True))
        cases.append(F.case('reference', params, 1))
        F.write(out, F.solid(48, 48, (0, 0, 255), stamp=True))
        cases.append(F.case('near_miss', params, 0))
        F.write(out, F.solid(64, 48, (255, 0, 0), stamp=True))
        cases.append(F.case('param_swap', params, 0))
    print('RESULT ' + json.dumps({'cases': cases}, ensure_ascii=False))

if __name__ == '__main__':
    main()
