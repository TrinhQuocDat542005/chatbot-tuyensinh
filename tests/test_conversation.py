import asyncio
from pathlib import Path
import re

import pytest
import yaml
from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.interfaces import ActionExecutionRejection

from actions.actions import (ActionCancelConsultation, ActionPrepareLookup, ActionPrepareScore,
                             ActionSubmitLookup, ValidateTraCuuNganhForm, ValidateTuVanDiemForm)
from actions.conversation import lookup_updates, major_from_message, method_from_text
from actions.repository import load_catalog


def tracker(text='', slots=None, intent='bo_sung_tra_cuu', entities=None):
    return Tracker('context-test', slots or {}, {'text': text, 'intent': {'name': intent},
                   'entities': entities or []}, [], False, None, {}, 'action_listen')


def test_switch_major_discards_old_year_and_method():
    values = lookup_updates(tracker('đổi sang Ngôn ngữ Anh', {'ten_nganh': 'Công nghệ thông tin',
        'nam': '2024', 'phuong_thuc': 'thpt', 'lookup_intent': 'hoi_diem_chuan_cua_nganh'}), load_catalog())
    assert values['ten_nganh'] == 'Ngôn ngữ Anh'
    assert values['nam'] is None and values['phuong_thuc'] is None


def test_switch_major_with_explicit_year_keeps_new_year():
    values = lookup_updates(tracker('đổi sang Ngôn ngữ Anh năm 2026 xét tuyển kết hợp', {'nam': '2024'}), load_catalog())
    assert values['nam'] == '2026' and values['phuong_thuc'] == 'ket_hop'


def test_year_followup_keeps_major_but_replaces_year():
    values = lookup_updates(tracker('còn năm 2023', {'ten_nganh': 'Công nghệ thông tin',
        'nam': '2026', 'lookup_intent': 'hoi_diem_chuan_cua_nganh'}), load_catalog())
    assert values['ten_nganh'] == 'Công nghệ thông tin' and values['nam'] == '2023'
    assert values['lookup_intent'] == 'hoi_diem_chuan_cua_nganh'


@pytest.mark.parametrize('text', ['ngành đó', 'ngành này thì sao'])
def test_pronoun_does_not_create_a_major(text):
    assert major_from_message(tracker(text), load_catalog()) is None


@pytest.mark.parametrize('text', ['đổi sang ngành ABC', 'điểm chuẩn năm 2025 và 2026', 'điểm chuẩn năm 9999'])
def test_invalid_replacement_cannot_reuse_old_context(text):
    dispatcher = CollectingDispatcher()
    events = ActionPrepareLookup().run(dispatcher, tracker(text, {'ten_nganh': 'CNTT', 'nam': '2026'},
        'hoi_diem_chuan_cua_nganh'), {})
    values = {e['name']: e['value'] for e in events}
    assert values['ten_nganh'] is None and values['nam'] is None
    assert dispatcher.messages


def test_longest_alias_matches_specialization():
    assert major_from_message(tracker('giới thiệu Kỹ thuật xây dựng cầu đường'), load_catalog()) == 'Xây dựng cầu đường'


def test_multiple_major_entities_are_rejected():
    with pytest.raises(ValueError):
        major_from_message(tracker(entities=[{'entity': 'ten_nganh', 'value': 'CNTT'},
            {'entity': 'ten_nganh', 'value': 'Ngôn ngữ Anh'}]), load_catalog())


def test_multiple_methods_are_rejected():
    with pytest.raises(ValueError):
        method_from_text('học bạ và THPT')


@pytest.mark.parametrize('intent,required', [
    ('hoi_diem_chuan_cua_nganh', ['ten_nganh', 'nam']),
    ('hoi_khoi_tuyen_sinh_cua_nganh', ['ten_nganh', 'nam']),
    ('hoi_thong_tin_gioi_thieu_chung_cua_nganh', ['ten_nganh']),
    ('hoi_co_hoi_viec_lam_cua_nganh', ['ten_nganh']),
])
def test_form_requires_only_relevant_fields(intent, required):
    assert asyncio.run(ValidateTraCuuNganhForm().required_slots([], CollectingDispatcher(),
        tracker(slots={'lookup_intent': intent}), {})) == required


def test_form_rejects_unknown_major():
    result = asyncio.run(ValidateTraCuuNganhForm().extract_ten_nganh(CollectingDispatcher(),
        tracker('ABC', {'requested_slot': 'ten_nganh'}), {}))
    assert result['ten_nganh'] is None


def test_form_major_change_clears_year():
    result = asyncio.run(ValidateTraCuuNganhForm().extract_ten_nganh(CollectingDispatcher(),
        tracker('Ngôn ngữ Anh', {'ten_nganh': 'CNTT', 'nam': '2024'}), {}))
    assert result['nam'] is None


@pytest.mark.parametrize('text,expected', [('24,5', 24.5), ('0', 0), ('sửa điểm thành 26 điểm', 26)])
def test_score_form_replaces_score(text, expected):
    result = asyncio.run(ValidateTuVanDiemForm().extract_diem(CollectingDispatcher(), tracker(text), {}))
    assert result['diem'] == expected


@pytest.mark.parametrize('text', ['31 điểm', '-1 điểm', 'Toán 8, Anh 9'])
def test_score_form_does_not_accept_bad_total(text):
    result = asyncio.run(ValidateTuVanDiemForm().extract_diem(CollectingDispatcher(), tracker(text), {}))
    assert result['diem'] is None


def test_new_score_request_does_not_reuse_old_score():
    result = ActionPrepareScore().run(CollectingDispatcher(), tracker('tư vấn ngành theo điểm', {'diem': 25}), {})
    assert result[0]['value'] is None


def test_cancel_clears_active_form_and_all_slots():
    events = ActionCancelConsultation().run(CollectingDispatcher(), tracker(slots={'nam': '2026', 'diem': 25}), {})
    assert events[0]['event'] == 'active_loop' and events[0]['name'] is None
    assert events[1]['event'] == 'reset_slots'


def test_submit_uses_corrected_year():
    dispatcher = CollectingDispatcher()
    ActionSubmitLookup().run(dispatcher, tracker('còn năm 2023', {'ten_nganh': 'CNTT', 'nam': '2023',
        'lookup_intent': 'hoi_diem_chuan_cua_nganh'}), {})
    answer = '\n'.join(m.get('text', '') for m in dispatcher.messages)
    assert '2023' in answer and '720' not in answer


def test_evaluation_is_independent_of_training():
    root = Path(__file__).resolve().parents[1]
    rows = yaml.safe_load((root/'tests/evaluation/nlu.yml').read_text(encoding='utf-8'))['examples']
    clean = lambda s: re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', s).strip().casefold()
    trained = set()
    for path in (root/'data').glob('*.yml'):
        for block in yaml.safe_load(path.read_text(encoding='utf-8')).get('nlu', []):
            if 'intent' in block:
                trained.update(clean(line[2:]) for line in block['examples'].splitlines() if line.startswith('- '))
    assert len(rows) >= 150
    assert sum(r['difficulty'] in ['hard', 'ood'] for r in rows) >= 30
    assert len({clean(r['text']) for r in rows}) == len(rows)
    assert not {clean(r['text']) for r in rows} & trained
    dev = yaml.safe_load((root/'tests/evaluation/dev.yml').read_text(encoding='utf-8'))['examples']
    dev_texts = {clean(r['text']) for r in dev}
    assert not dev_texts & trained
    assert not dev_texts & {clean(r['text']) for r in rows}


@pytest.mark.parametrize('form', [ValidateTraCuuNganhForm, ValidateTuVanDiemForm])
@pytest.mark.parametrize('intent', ['bat_dau_lai', 'huy_tra_cuu', 'nlu_fallback'])
def test_form_rejects_interrupting_intents(form, intent):
    with pytest.raises(ActionExecutionRejection):
        asyncio.run(form().run(CollectingDispatcher(), tracker(intent=intent), {}))
