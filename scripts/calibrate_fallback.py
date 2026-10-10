"""Select a fallback threshold only from development predictions, never held-out test."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from actions.fallback import macro_f1, prediction_at_threshold


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('report')
    parser.add_argument('--out', default='results/nlu/calibration.json')
    args = parser.parse_args()
    report = json.loads(Path(args.report).read_text(encoding='utf-8'))
    if not report['dataset'].endswith('dev.yml'):
        raise ValueError('Threshold selection requires the development set.')
    gold = [row['intent'] for row in report['predictions']]
    source_threshold = report.get('fallback_threshold', 0.7)
    candidates = []
    for threshold in [0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9]:
        predicted = []
        for row in report['predictions']:
            predicted.append(prediction_at_threshold(row, threshold, source_threshold))
        candidates.append({'threshold': threshold, 'macro_f1': macro_f1(gold, predicted),
                           'ood_recall': sum(a == b == 'nlu_fallback' for a, b in zip(gold, predicted)) / gold.count('nlu_fallback')})
    # Ties favor the current threshold to avoid an unsubstantiated change.
    best = max(candidates, key=lambda c: (c['macro_f1'], -abs(c['threshold'] - 0.7)))
    output = {'dataset_sha256': report['dataset_sha256'], 'ambiguity_threshold': 0.1, 'candidates': candidates, 'selected': best}
    Path(args.out).write_text(json.dumps(output, indent=2), encoding='utf-8')
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
