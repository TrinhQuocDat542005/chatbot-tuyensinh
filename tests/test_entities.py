from actions.entities import filter_entities
from actions.repository import load_catalog


def entity(text, value, kind, start=None):
    start = text.index(value) if start is None else start
    return {'entity': kind, 'start': start, 'end': start+len(value), 'value': value}


def test_subject_words_in_names_and_greetings_are_not_subject_entities():
    text = 'Chào anh, mình tên Vân Anh'
    values = [entity(text, 'anh', 'mon_hoc'), entity(text, 'Anh', 'mon_hoc'), entity(text, 'Vân Anh', 'ten_nguoi_dung')]
    assert filter_entities(text, 'nhap_ten', values, load_catalog()) == [values[2]]


def test_wrong_total_score_entity_is_removed():
    text = 'tổng 24,5 điểm'
    values = [entity(text, '24,5', 'd'), entity(text, '24,5', 'diem')]
    assert filter_entities(text, 'tu_van_nganh_theo_diem', values, load_catalog()) == [values[1]]


def test_duplicate_extractors_collapse_and_unknown_name_is_removed():
    text = 'ngành Công nghệ thông tin học gì'
    values = [entity(text, 'Công nghệ thông tin', 'ten_nganh')]*2 + [entity(text, 'Công nghệ thông tin học', 'ten_nganh')]
    result = filter_entities(text, 'hoi_diem_chuan_cua_nganh', values, load_catalog())
    assert len(result) == 1 and result[0]['value'] == 'Công nghệ thông tin'


def test_year_phrase_is_reduced_to_exact_year_span():
    text = 'điểm chuẩn năm 2026 nhé'
    result = filter_entities(text, 'hoi_diem_chuan_cua_nganh', [entity(text, 'năm 2026 nhé', 'nam')], load_catalog())
    assert result[0]['start'] == text.index('2026') and result[0]['value'] == '2026'


def test_parent_span_does_not_hide_specialization():
    text = 'Kỹ thuật xây dựng cầu đường'
    result = filter_entities(text, 'bo_sung_tra_cuu', [entity(text, 'Kỹ thuật xây dựng', 'ten_nganh'),
        entity(text, 'xây dựng cầu đường', 'ten_nganh')], load_catalog())
    assert len(result) == 1 and result[0]['end'] == len(text)


def test_out_of_range_values_are_kept_for_action_validation():
    text = '31 điểm'
    values = [entity(text, '31', 'diem')]
    assert filter_entities(text, 'tu_van_nganh_theo_diem', values, load_catalog()) == values


def test_subject_score_entities_reject_non_subject_and_non_numeric_spans():
    text = 'Vật lý đạt 12 điểm, tính giúp mình'
    valid = [entity(text, 'Vật lý', 'mon_hoc'), entity(text, '12', 'd')]
    invalid = [entity(text, 'Vật lý đạt', 'mon_hoc'), entity(text, 'tính', 'mon_hoc'),
               entity(text, '12 điểm', 'd')]
    # Out-of-range numeric scores still reach the action's validation.
    assert filter_entities(text, 'cung_cap_diem', valid + invalid, load_catalog()) == valid
