"""Model provenance and checksum validation; no Rasa import is required."""
import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest() if hasattr(hashlib, 'file_digest') else _digest(stream)


def _digest(stream):
    digest = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
        digest.update(chunk)
    return digest.hexdigest()


def inputs(root=ROOT):
    paths = [root / p for p in ['config.yml', 'domain.yml', 'requirements-lock.linux.txt', 'Dockerfile']]
    for directory in ['data', 'components', 'actions']:
        paths += [p for p in (root / directory).rglob('*')
                  if p.is_file() and p.suffix in {'.py', '.json', '.yml', '.yaml'} and '__pycache__' not in p.parts]
    return {p.relative_to(root).as_posix(): sha256(p) for p in sorted(set(paths))}


def write(model, commit, dirty, started_inputs):
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('SOURCE_COMMIT must be a full Git commit SHA. Use python scripts/manage.py train.')
    if inputs() != started_inputs:
        raise ValueError('Training inputs changed during training; refuse provenance.')
    freeze = subprocess.check_output(['python', '-m', 'pip', 'freeze', '--all'], text=True)
    manifest = {'format_version': 1, 'trained_at_utc': datetime.now(timezone.utc).isoformat(),
                'commit': commit, 'working_tree_dirty': dirty,
                'model': {'file': model.name, 'sha256': sha256(model), 'bytes': model.stat().st_size},
                'python': platform.python_version(), 'platform': platform.platform(),
                'training_command': ['python', '-m', 'rasa', 'train', '--force', '--data', 'data', '--fixed-model-name', model.name.removesuffix('.tar.gz')],
                'inputs': started_inputs, 'installed_packages': freeze.splitlines()}
    manifest_path = model.with_name(model.name + '.manifest.json')
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    model.with_name(model.name + '.sha256').write_text(f"{manifest['model']['sha256']}  {model.name}\n", encoding='ascii')
    return manifest


def verify(model, manifest_path=None, check_inputs=True):
    manifest = json.loads((manifest_path or model.with_name(model.name + '.manifest.json')).read_text(encoding='utf-8'))
    if manifest['model']['file'] != model.name or manifest['model']['sha256'] != sha256(model):
        raise ValueError('Model checksum or filename mismatch.')
    if manifest['model']['bytes'] != model.stat().st_size:
        raise ValueError('Model size mismatch.')
    if not re.fullmatch(r'[0-9a-f]{40}', manifest['commit']):
        raise ValueError('Invalid provenance commit.')
    if check_inputs and manifest['inputs'] != inputs():
        raise ValueError('Model training inputs differ from this checkout. Retrain or use the matching commit.')
    print(f"Verified {model.name}: SHA-256 and provenance commit {manifest['commit']}")
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['train', 'verify'])
    parser.add_argument('--model', type=Path, default=Path('models/admissions-week4.tar.gz'))
    parser.add_argument('--checksum-only', action='store_true', help='Verify bytes without matching checkout inputs.')
    args = parser.parse_args()
    if args.mode == 'train':
        commit = os.environ.get('SOURCE_COMMIT', '')
        if not re.fullmatch(r'[0-9a-f]{40}', commit):
            parser.error('Use python scripts/manage.py train to provide SOURCE_COMMIT.')
        snapshot = inputs()
        subprocess.run(['python', '-m', 'rasa', 'train', '--force', '--data', 'data', '--out', str(args.model.parent),
                        '--fixed-model-name', args.model.name.removesuffix('.tar.gz')], check=True)
        write(args.model, commit, os.environ.get('SOURCE_DIRTY', 'true') != 'false', snapshot)
    verify(args.model, check_inputs=not args.checksum_only)
