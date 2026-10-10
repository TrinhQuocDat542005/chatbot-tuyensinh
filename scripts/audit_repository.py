"""Scan tracked text and optionally reachable Git history without printing secrets."""
import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    'private-key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
    'github-token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b'),
    'aws-access-key': re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'google-api-key': re.compile(r'\bAIza[A-Za-z0-9_-]{35}\b'),
    'slack-token': re.compile(r'\bxox[baprs]-[A-Za-z0-9-]{20,}\b'),
    'credential-url': re.compile(r'https?://[^\s/:]+:[^\s/@]+@'),
}


def findings(raw, path):
    if b'\0' in raw[:8192]:
        return []
    text = raw.decode('utf-8', errors='replace')
    result = []
    for number, line in enumerate(text.splitlines(), 1):
        for kind, pattern in PATTERNS.items():
            if pattern.search(line):
                result.append({'path': path, 'line': number, 'kind': kind})
    if Path(path).name == '.env':
        result.append({'path': path, 'kind': 'tracked-environment-file'})
    return result


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def audit(history=False):
    paths = git('ls-files', '-z').decode().split('\0')
    result = []
    files = 0
    for path in filter(None, paths):
        candidate = ROOT / path
        if candidate.is_file():
            files += 1
            result.extend(findings(candidate.read_bytes(), path))
    blobs = 0
    if history:
        objects = {}
        for entry in git('rev-list', '--objects', '--all').decode().splitlines():
            oid, _, path = entry.partition(' ')
            if path:
                objects.setdefault(oid, path)
        process = subprocess.Popen(['git', 'cat-file', '--batch'], cwd=ROOT,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        try:
            for oid, path in objects.items():
                process.stdin.write((oid + '\n').encode())
                process.stdin.flush()
                header = process.stdout.readline().split()
                if len(header) != 3:
                    raise ValueError('Cannot inspect Git object ' + oid)
                size = int(header[2])
                raw = process.stdout.read(size)
                process.stdout.read(1)
                if header[1] != b'blob':
                    continue
                blobs += 1
                for item in findings(raw, path):
                    result.append(dict(item, blob=oid))
        finally:
            process.stdin.close()
            process.stdout.close()
            process.wait()
    return {'tracked_files': files, 'history_blobs': blobs, 'findings': result,
            'scope': 'Known token formats, private key headers, credential URLs and tracked .env; binary files are not inspected.',
            'limitations': 'Not an exhaustive secret or personal-data audit. Public author credits and synthetic score examples are intentional.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--history', action='store_true')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    report = audit(args.history)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(bool(report['findings']))
