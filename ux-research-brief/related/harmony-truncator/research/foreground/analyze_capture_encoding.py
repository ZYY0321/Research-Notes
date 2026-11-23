"""Compare repeated native encodings in target coordinates, without changing thresholds."""
import argparse
from collections import Counter
from pathlib import Path
from PIL import Image
from truncator.common.storage import read, save
from truncator.source.binding import active_records, select_record
from truncator.imaging.geometry import rectangle
from truncator.imaging.content_identity import compare_visible


def attributes(folder, index, selector):
    return select_record(active_records(read(folder / f'{index}-before.json')), selector)['attributes']


def analyze(root, out):
    records = read(root / 'results.json')
    reference = Path(records[0]['burst'])
    results = []
    for row in records[1:]:
        folder = Path(row['burst'])
        name = row['name'].split('-')[0]
        selector = {'id': 'label-' + name}
        comparisons = []
        for i in range(3):
            a = attributes(reference, i, selector)
            for j in range(3):
                b = attributes(folder, j, row['selector'])
                for encoding in ('png', 'jpeg'):
                    with Image.open(folder / f'{j}.{encoding}') as image:
                        assert image.format == ('PNG' if encoding == 'png' else 'JPEG')
                    measurement = compare_visible(reference / f'{i}.{encoding}', folder / f'{j}.{encoding}',
                        rectangle(a['origBounds']), rectangle(b['origBounds']), rectangle(b['bounds']), text=True)
                    comparisons.append({'reference_repeat': i, 'current_repeat': j, 'encoding': encoding,
                                        'measurement': measurement})
        results.append({'name': row['name'], 'comparisons': comparisons,
                        'status_counts': {enc: dict(Counter(c['measurement']['status'] for c in comparisons
                                                           if c['encoding'] == enc)) for enc in ('png', 'jpeg')}})
    save(out, {'input': str(root), 'native_pairs': sum(len(read(Path(r['burst']) / 'repeats.json')['samples']) for r in records),
               'all_targets_stable': all(s['targets_stable'] for r in records
                                        for s in read(Path(r['burst']) / 'repeats.json')['samples']),
               'states': results})
    for row in results:
        print(row['name'], row['status_counts'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    analyze(args.root, args.out)
