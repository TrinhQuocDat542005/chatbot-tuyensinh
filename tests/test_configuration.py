import re
from pathlib import Path

import yaml

ROOT=Path(__file__).resolve().parents[1]


def test_nlu_rules_and_tests_reference_domain():
    domain=yaml.safe_load((ROOT/'domain.yml').read_text(encoding='utf-8'))
    nlu=yaml.safe_load((ROOT/'data/nlu.yml').read_text(encoding='utf-8'))
    declared=set(domain['intents'])
    assert {item['intent'] for item in nlu['nlu'] if 'intent' in item} <= declared
    for path in [ROOT/'data/rules.yml',ROOT/'data/stories.yml',ROOT/'tests/test_stories.yml']:
        doc=yaml.safe_load(path.read_text(encoding='utf-8'))
        for item in doc.get('rules',doc.get('stories',[])):
            for step in item['steps']:
                if 'intent' in step:assert step['intent'] in declared
                if 'action' in step:
                    assert step['action'] in set(domain['actions']) | set(domain['responses']) | set(domain.get('forms', {})) | {'action_restart'}
    labels=set(re.findall(r'\]\(([^)]+)\)',(ROOT/'data/nlu.yml').read_text(encoding='utf-8')))
    assert labels <= set(domain['entities'])


def test_regex_and_ignore_encoding():
    regex=yaml.safe_load((ROOT/'data/regex.yml').read_text(encoding='utf-8'))
    for item in regex['nlu']:
        for line in item['examples'].splitlines():re.compile(line[2:])
    assert b'\x00' not in (ROOT/'.gitignore').read_bytes()
