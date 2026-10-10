"""Fail CI when authored regression metrics or Core predictions fail."""
import argparse
import json
from pathlib import Path


def check(report, min_intent=0.90, min_entity=0.85):
    intent = report['intents']['macro avg']['f1-score']
    entity = report['entity_exact_span']['f1']
    if report['count'] < 150 or report['hard_or_ood_count'] < 30:
        raise ValueError('Evaluation coverage is below the agreed minimum.')
    if intent < min_intent or entity < min_entity:
        raise ValueError(f'Regression gate failed: intent={intent:.4f}, entity={entity:.4f}')
    print(f'Authored regression gate passed: intent={intent:.4f}, entity={entity:.4f}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, default=Path('results/nlu/ci.json'))
    args = parser.parse_args()
    check(json.loads(args.report.read_text(encoding='utf-8')))
