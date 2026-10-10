"""Save a reviewable evaluation summary without requiring the Rasa runtime."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_report(path):
    report = json.loads(Path(path).read_text(encoding='utf-8'))
    if 'dataset_sha256' in report and digest(report['dataset']) != report['dataset_sha256']:
        raise ValueError(f"Dataset changed since evaluation: {report['dataset']}")
    return report


def metrics(report):
    return {**{key: report[key] for key in ('dataset', 'dataset_sha256', 'count', 'hard_or_ood_count')},
            'macro_f1_intent': report['intents']['macro avg']['f1-score'],
            'entity_exact_span': report['entity_exact_span']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--final', default='results/nlu/final.json')
    parser.add_argument('--dev', default='results/nlu/dev-final.json')
    parser.add_argument('--baseline', default='results/nlu/baseline.json')
    parser.add_argument('--core', default='results/core/story_report.json')
    parser.add_argument('--out', default='docs/evaluation/week4-summary.json')
    parser.add_argument('--date', required=True, help='Evaluation date in YYYY-MM-DD, local to the reviewer')
    args = parser.parse_args()
    final, dev = [load_report(path) for path in (args.final, args.dev)]
    baseline = load_report(args.baseline) if Path(args.baseline).exists() else None
    model = Path(final['model'])
    labels = final['confusion_labels']
    summary = {
        'evaluated_at': args.date,
        'limitations': [
            'Authored examples, not an independent real-user dataset.',
            'Evaluation errors have been reviewed; subsequent runs are regression checks, not blind evaluation.',
            'No exact text overlap with training; semantic similarity is not ruled out.',
            'Baseline lacks bat_dau_lai, bo_sung_tra_cuu and huy_tra_cuu; scope differs.',
            'Fresh training can produce different weights and metrics.',
        ],
        'final_model': {'path': final['model'], 'sha256': digest(model), 'bytes': model.stat().st_size},
        'final_config': {'path': 'config.yml', 'sha256': digest('config.yml')},
        'training_files': {str(path.as_posix()): digest(path) for path in sorted(Path('data').glob('*.yml'))},
        'runtime_code_sha256': {str(path.as_posix()): digest(path)
                                for directory in ('actions', 'components')
                                for path in sorted(Path(directory).glob('*.py'))},
        'reports_sha256': {path: digest(path) for path in (args.final, args.dev, args.baseline, args.core)
                           if Path(path).exists()},
        'baseline': metrics(baseline) if baseline else None,
        'final': metrics(final), 'development_final': metrics(dev),
        'fallback_threshold': final['fallback_threshold'],
        'final_intent_report': final['intents'], 'final_entity_by_type': final['entity_by_type'],
        'final_sparse_confusion': [
            {'expected': labels[i], 'predicted': labels[j], 'count': count}
            for i, row in enumerate(final['confusion_matrix']) for j, count in enumerate(row) if count
        ],
        'final_failures': final['failures'],
        'acceptance': {
            'intent_macro_f1_target': 0.90, 'intent_target_met': metrics(final)['macro_f1_intent'] >= 0.90,
            'entity_exact_span_f1_target': 0.85, 'entity_target_met': final['entity_exact_span']['f1'] >= 0.85,
        },
        'core_final': load_report(args.core),
        'rest': {name: {key: load_report(path)[key] for key in ('count', 'passed')}
                 for name, path in [('explicit_intents', 'results/conversations/report.json'),
                                    ('natural_multiturn', 'results/conversations/natural-report.json')]},
    }
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(summary['acceptance']))


if __name__ == '__main__':
    main()
