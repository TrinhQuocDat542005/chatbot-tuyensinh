import json
from pathlib import Path

import pytest
import yaml

from actions.repository import DataError, load_catalog
from scripts.check_evaluation import check as check_evaluation
from scripts.check_project import check as check_syntax
from scripts.model_artifact import sha256, verify

ROOT = Path(__file__).resolve().parents[1]


def test_ci_rejects_deliberately_corrupted_catalog(tmp_path):
    catalog = json.loads((ROOT / 'actions/data/nganh.json').read_text(encoding='utf-8'))
    catalog['majors'][0]['id'] = catalog['majors'][1]['id']
    (tmp_path / 'nganh.json').write_text(json.dumps(catalog), encoding='utf-8')
    with pytest.raises(DataError, match='Duplicate major ID'):
        load_catalog(tmp_path)


@pytest.mark.parametrize('name,content', [('config.yml', 'language: vi\nlanguage: en\n'),
                                         ('package.json', '{"name":"first","name":"second"}')])
def test_ci_rejects_duplicate_configuration_keys(tmp_path, name, content):
    (tmp_path / name).write_text(content, encoding='utf-8')
    with pytest.raises(ValueError, match='Duplicate'):
        check_syntax(tmp_path)


def test_checksum_rejects_modified_model(tmp_path):
    model = tmp_path / 'demo.tar.gz'
    model.write_bytes(b'original-model')
    manifest = {'commit': 'a' * 40, 'model': {'file': model.name, 'sha256': sha256(model), 'bytes': model.stat().st_size}}
    model.with_name(model.name + '.manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    verify(model, check_inputs=False)
    model.write_bytes(b'tampered-model')
    with pytest.raises(ValueError, match='checksum'):
        verify(model, check_inputs=False)


def test_metric_gate_rejects_regression():
    report = {'count':154, 'hard_or_ood_count':54, 'intents':{'macro avg':{'f1-score':0.5}}, 'entity_exact_span':{'f1':0.9}}
    with pytest.raises(ValueError, match='Regression gate failed'):
        check_evaluation(report)


def test_valid_checksum_does_not_allow_a_different_checkout(tmp_path):
    model = tmp_path / 'demo.tar.gz'
    model.write_bytes(b'valid-model-bytes')
    manifest = {'commit':'a' * 40, 'model':{'file':model.name, 'sha256':sha256(model), 'bytes':model.stat().st_size},
                'inputs':{'config.yml':'stale-config-hash'}}
    model.with_name(model.name + '.manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    with pytest.raises(ValueError, match='inputs differ'):
        verify(model)


def test_sdk_image_and_internal_action_endpoint_are_separate():
    compose = yaml.safe_load((ROOT / 'compose.yaml').read_text(encoding='utf-8'))['services']
    assert compose['actions']['image'] != compose['rasa']['image']
    assert compose['actions']['build']['target'] == 'runtime'
    assert yaml.safe_load((ROOT / 'endpoints.docker.yml').read_text(encoding='utf-8'))['action_endpoint']['url'] == 'http://actions:5055/webhook'
