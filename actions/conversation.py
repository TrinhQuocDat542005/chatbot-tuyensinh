"""Explicit conversation state; never silently reuse an invalid replacement."""
import re

from actions.admissions import normalize, requested_year
from actions.repository import find_major

LOOKUPS = {
    'hoi_thong_tin_gioi_thieu_chung_cua_nganh': 'action_tra_loi_thong_tin_nganh',
    'hoi_co_hoi_viec_lam_cua_nganh': 'action_tra_loi_co_hoi_viec_lam',
    'hoi_diem_chuan_cua_nganh': 'action_tra_loi_diem_chuan_nganh',
    'hoi_khoi_tuyen_sinh_cua_nganh': 'action_tra_loi_khoi_xet_tuyen',
}


def method_from_text(text):
    text = normalize(text)
    matches = {value for keys, value in [
        (('hoc ba',), 'hoc_ba'), (('dgnl', 'danh gia nang luc'), 'dgnl'),
        (('thpt',), 'thpt'), (('ket hop',), 'ket_hop'),
    ] if any(key in text for key in keys)}
    if len(matches) > 1:
        raise ValueError('Vui lòng chọn một phương thức xét tuyển để tra cứu.')
    return next(iter(matches), None)


def major_from_message(tracker, doc):
    entities = [e['value'] for e in tracker.latest_message.get('entities', []) if e['entity'] == 'ten_nganh']
    if entities:
        found = [find_major(value, doc) for value in entities]
        ids = {m['id'] for m in found if m}
        if len(ids) != 1 or any(m is None for m in found):
            raise ValueError('Vui lòng chọn một ngành có trong danh mục đã xác minh.')
        return next(m['ten_nganh'] for m in found if m)
    text = normalize(tracker.latest_message.get('text', ''))
    # Exact aliases with word boundaries; longest match resolves parent/child overlap.
    candidates = []
    for major in doc['majors']:
        if major['verification'] != 'verified':
            continue
        for alias in [major['ten_nganh'], *major['aliases']]:
            key = normalize(alias)
            if re.search(r'(?<!\w)' + re.escape(key) + r'(?!\w)', text):
                candidates.append((len(key), major['ten_nganh']))
    if candidates:
        longest = max(length for length, _ in candidates)
        names = {name for length, name in candidates if length == longest}
        if len(names) != 1:
            raise ValueError('Vui lòng chọn một ngành để tra cứu.')
        return names.pop()
    if re.search(r'\b(?:doi sang|chuyen sang|nganh moi|thay nganh)\b', text):
        raise ValueError('Ngành thay thế chưa có trong danh mục; vui lòng nhập tên đầy đủ.')
    return None


def lookup_updates(tracker, doc):
    intent = tracker.latest_message.get('intent', {}).get('name')
    pending = intent if intent in LOOKUPS else tracker.get_slot('lookup_intent')
    major = major_from_message(tracker, doc)
    previous = tracker.get_slot('ten_nganh')
    changed = major is not None and normalize(major) != normalize(previous or '')
    year = requested_year(tracker.latest_message.get('text', ''))
    method = method_from_text(tracker.latest_message.get('text', ''))
    return {
        'lookup_intent': pending if pending in LOOKUPS else 'hoi_thong_tin_gioi_thieu_chung_cua_nganh',
        'ten_nganh': major or previous,
        'nam': str(year) if year is not None else (None if changed else tracker.get_slot('nam')),
        'phuong_thuc': method or (None if changed else tracker.get_slot('phuong_thuc')),
    }
