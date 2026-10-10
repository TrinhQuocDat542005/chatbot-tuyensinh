"""Evaluate frozen authored examples; reports include every error and exact entity spans."""
import argparse
import asyncio
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yaml
from rasa.core.agent import Agent
from sklearn.metrics import classification_report, confusion_matrix


def example(markup):
    entities, parts, cursor, offset = [], [], 0, 0
    for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', markup):
        prefix = markup[cursor:match.start()]
        parts += [prefix, match[1]]
        offset += len(prefix)
        entities.append((match[2], offset, offset + len(match[1])))
        offset += len(match[1])
        cursor = match.end()
    parts.append(markup[cursor:])
    return ''.join(parts), set(entities)


async def evaluate(args):
    dataset = Path(args.data)
    rows = yaml.safe_load(dataset.read_text(encoding='utf-8'))['examples']
    agent = Agent.load(args.model)
    fallback_threshold = next(node.config.get('threshold', 0.3) for node in
                              agent.processor.model_metadata.predict_schema.nodes.values()
                              if node.uses.__name__ == 'FallbackClassifier')
    gold, predicted, details = [], [], []
    tp = fp = fn = 0
    for row in rows:
        text, expected = example(row['text'])
        parse = await agent.parse_message(text)
        actual = {(e['entity'], e['start'], e['end']) for e in parse.get('entities', [])}
        tp += len(expected & actual)
        fp += len(actual - expected)
        fn += len(expected - actual)
        intent = parse['intent']['name']
        gold.append(row['intent'])
        predicted.append(intent)
        details.append({**row, 'plain_text': text, 'prediction': intent,
                        'confidence': parse['intent']['confidence'],
                        'ranking': parse.get('intent_ranking', [])[:3],
                        'fallback_added': bool(parse['intent']['name'] == 'nlu_fallback'
                                               and parse['intent']['confidence'] == fallback_threshold),
                        'entities_expected': sorted(expected), 'entities_actual': sorted(actual),
                        'intent_correct': intent == row['intent'], 'entities_correct': expected == actual})
    labels = sorted(set(gold) | set(predicted))
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    report = {
        'model': args.model, 'dataset': args.data, 'dataset_sha256': hashlib.sha256(dataset.read_bytes()).hexdigest(),
        'fallback_threshold': fallback_threshold,
        'count': len(rows), 'hard_or_ood_count': sum(r['difficulty'] in ['hard', 'ood'] for r in rows),
        'intents': classification_report(gold, predicted, labels=labels, output_dict=True, zero_division=0),
        'entity_exact_span': {'tp': tp, 'fp': fp, 'fn': fn, 'precision': precision, 'recall': recall,
                              'f1': 2 * precision * recall / (precision + recall) if precision + recall else 0},
        'entity_by_type': {},
        'confusion_labels': labels, 'confusion_matrix': confusion_matrix(gold, predicted, labels=labels).tolist(),
        'failures': [d for d in details if not d['intent_correct'] or not d['entities_correct']], 'predictions': details,
    }
    for entity in sorted({e[0] for d in details for e in d['entities_expected'] + d['entities_actual']}):
        a = b = c = 0
        for d in details:
            expected = {tuple(e) for e in d['entities_expected'] if e[0] == entity}
            actual = {tuple(e) for e in d['entities_actual'] if e[0] == entity}
            a += len(expected & actual); b += len(actual - expected); c += len(expected - actual)
        report['entity_by_type'][entity] = {'tp': a, 'fp': b, 'fn': c, 'f1': 2*a/(2*a+b+c) if 2*a+b+c else 0}
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: report[k] for k in ['count', 'hard_or_ood_count', 'entity_exact_span']}, ensure_ascii=False))
    print('Intent macro-F1:', report['intents']['macro avg']['f1-score'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True)
    parser.add_argument('--data', default='tests/evaluation/nlu.yml')
    parser.add_argument('--out', required=True)
    asyncio.run(evaluate(parser.parse_args()))
