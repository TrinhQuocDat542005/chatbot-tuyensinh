"""CI syntax checks, including duplicate keys that ordinary YAML silently accepts."""
import argparse
import copy
import json
from pathlib import Path

import yaml


class UniqueLoader(yaml.SafeLoader):
    # GitHub's `on` is a string, not YAML 1.1's boolean True.
    yaml_implicit_resolvers = copy.deepcopy(yaml.SafeLoader.yaml_implicit_resolvers)


for first, resolvers in UniqueLoader.yaml_implicit_resolvers.items():
    UniqueLoader.yaml_implicit_resolvers[first] = [
        (tag, expression) for tag, expression in resolvers
        if tag != 'tag:yaml.org,2002:bool'
    ]


def unique_mapping(loader, node):
    pairs = loader.construct_pairs(node)
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate YAML key: {key}')
        result[key] = value
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def json_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate JSON key: {key}')
        result[key] = value
    return result


def check(root):
    paths = list(root.glob('*.yml')) + list(root.glob('*.yaml')) + list(root.glob('*.json'))
    for directory in ['actions/data', 'actions/schemas', 'data', 'tests', '.github', 'docs/evaluation']:
        paths += [p for p in (root / directory).rglob('*') if p.suffix in {'.json', '.yml', '.yaml'}]
    for path in sorted(set(paths)):
        raw = path.read_text(encoding='utf-8-sig')
        if path.suffix == '.json':
            json.loads(raw, object_pairs_hook=json_pairs)
        else:
            yaml.load(raw, Loader=UniqueLoader)
    print(f'Valid syntax and unique keys: {len(set(paths))} YAML/JSON files')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    check(args.root)
