"""Real REST/Core/SDK multi-turn checks with explicit intents to isolate dialogue behavior.

NLU is evaluated separately on the frozen evaluation set and by smoke_rest.py.
"""
import argparse
import json
import uuid
from pathlib import Path
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://localhost:5005')
    parser.add_argument('--out', default='results/conversations/report.json')
    parser.add_argument('--cases', default='tests/conversations/scenarios.json')
    args = parser.parse_args()
    scenarios = json.loads((Path(__file__).resolve().parents[1] / args.cases).read_text(encoding='utf-8'))
    results = []
    for case in scenarios:
        sender = f"week4-{uuid.uuid4()}"
        turns = []
        for turn in case['turns']:
            message = '/' + turn.get('intent', 'nlu_fallback') + json.dumps(turn.get('entities', {}), ensure_ascii=False)
            # Slash intents preserve the intent/entity input; text-sensitive parsers
            # still read the values present in the JSON string.
            if 'text' in turn:
                message = turn['text']
            request = Request(args.url + '/webhooks/rest/webhook',
                              data=json.dumps({'sender': sender, 'message': message}).encode('utf-8'),
                              headers={'Content-Type': 'application/json'})
            with urlopen(request, timeout=90) as response:
                answer = '\n'.join(m.get('text', '') for m in json.load(response))
            passed = all(s in answer for s in turn.get('contains', [])) and all(s not in answer for s in turn.get('excludes', []))
            turns.append({'message': message, 'answer': answer, 'passed': passed})
        passed = all(turn['passed'] for turn in turns)
        print('PASS' if passed else 'FAIL', case['id'], flush=True)
        results.append({'id': case['id'], 'passed': passed, 'turns': turns})
    report = {'count': len(results), 'passed': sum(r['passed'] for r in results), 'results': results}
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    if report['passed'] != report['count']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
