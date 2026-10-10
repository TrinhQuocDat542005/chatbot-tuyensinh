"""Validate JSON schemas and cross-document references without starting Rasa."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from actions.repository import DataError, load_catalog, load_document


def main():
    try:
        catalog = load_catalog()
        school = load_document('school')
        sources = {s['id']: s for s in school['sources']}
        for fact in school['facts'].values():
            if not set(fact['source_ids']) <= sources.keys():
                raise DataError('Unknown school fact source')
            if fact['verification'] == 'verified' and (not fact['text'] or any(sources[s]['verification'] != 'verified' for s in fact['source_ids'])):
                raise DataError('Verified fact requires verified sources and text')
        print(f"Valid: {len(catalog['majors'])} catalog entries, {len(catalog['admissions'])} cutoff records, {len(school['facts'])} school facts")
    except DataError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
