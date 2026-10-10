"""Entity validation independent of the Rasa runtime."""
import re
from actions.conversation import LOOKUPS
from actions.repository import find_major
from actions.admissions import SUBJECTS, normalize


def filter_entities(text, intent, entities, catalog):
    accepted = []
    for source in entities:
        entity = dict(source)
        kind = entity['entity']
        value = text[entity['start']:entity['end']]
        if kind == 'ten_nganh':
            if intent not in {*LOOKUPS, 'bo_sung_tra_cuu', 'tu_van_nganh_theo_diem'} or not find_major(value, catalog):
                continue
        elif kind in {'d', 'mon_hoc'}:
            if intent != 'cung_cap_diem':
                continue
            if kind == 'mon_hoc' and normalize(value) not in SUBJECTS:
                continue
            if kind == 'd' and not re.fullmatch(r'-?\d+(?:[.,]\d+)?', value):
                continue
        elif kind == 'diem':
            if intent != 'tu_van_nganh_theo_diem' or not re.fullmatch(r'-?\d+(?:[.,]\d+)?', value):
                continue
        elif kind == 'nam':
            # Keep only the year span, not a learned phrase such as "năm 2026 nhé".
            match = re.search(r'\b(?:19|20)\d{2}\b', value)
            if not match:
                continue
            entity['start'] += match.start()
            entity['end'] = entity['start'] + len(match[0])
            entity['value'] = match[0]
        elif kind == 'ten_nguoi_dung':
            if intent != 'nhap_ten':
                continue
            trimmed = re.sub(r'\s+(?:nha|nhé|ạ|a|nhe)\s*$', '', value, flags=re.I)
            entity['end'] = entity['start'] + len(trimmed)
            entity['value'] = trimmed
        accepted.append(entity)
    # Collapse duplicate extractors and keep the longest catalogue span.
    unique = {}
    for entity in accepted:
        if entity['entity'] == 'ten_nganh' and any(
            other['entity'] == 'ten_nganh' and other['start'] < entity['end'] and entity['start'] < other['end']
            and other['end'] - other['start'] > entity['end'] - entity['start'] for other in accepted):
            continue
        unique[(entity['entity'], entity['start'], entity['end'])] = entity
    return list(unique.values())
