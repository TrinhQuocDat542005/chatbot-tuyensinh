"""Cross-platform Docker commands with explicit model provenance."""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args, **kwargs):
    subprocess.run(args, cwd=ROOT, check=True, **kwargs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['train', 'up', 'check', 'down'])
    parser.add_argument('--skip-build', action='store_true', help='CI only: images were built from this checkout.')
    args = parser.parse_args()
    if args.mode == 'train':
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip())
        if not args.skip_build:
            run('docker', 'compose', 'build', 'train', 'actions', 'web')
        run('docker', 'compose', 'run', '--rm', '-e', f'SOURCE_COMMIT={commit}',
            '-e', f'SOURCE_DIRTY={str(dirty).lower()}', 'train')
    elif args.mode == 'up':
        run(sys.executable, 'scripts/model_artifact.py', 'verify')
        run('docker', 'compose', 'up', '-d', '--wait', '--wait-timeout', '180', '--no-build', 'actions', 'rasa', 'web')
    elif args.mode == 'check':
        run('docker', 'compose', 'run', '--rm', 'check')
    else:
        run('docker', 'compose', 'down')
