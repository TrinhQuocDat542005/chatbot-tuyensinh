from datetime import date

import pytest

from actions.admissions import combination_scores, parse_subject_scores, parse_total_score, requested_year


@pytest.mark.parametrize('text', [
    'Em có 8 điểm Toán, 8 điểm Hóa và 9 điểm Anh',
    'Toán 8, Hóa 8, Anh 9',
    '8 diem Toan, 8 diem Hoa va 9 diem Tieng Anh',
])
def test_d07_regression(text):
    assert combination_scores(parse_subject_scores(text)) == {'D07': 25}


def test_more_than_three_subjects():
    scores = combination_scores(parse_subject_scores('Toán 8, Lý 7, Hóa 9, Anh 8'))
    assert scores == {'A00': 24, 'A01': 23, 'D07': 25}


def test_missing_subject_is_not_zero():
    assert combination_scores(parse_subject_scores('Toán 8, Anh 9')) == {}


def test_decimal_comma_and_full_names():
    assert combination_scores(parse_subject_scores('8,5 điểm Toán, 8 điểm Hóa học và 9 điểm Anh Văn')) == {'D07': 25.5}


@pytest.mark.parametrize('text', ['11 điểm Toán', '-1 điểm Hóa', 'Toán 10,5', 'Toán 8 và Toán 9'])
def test_invalid_or_conflicting_subjects(text):
    with pytest.raises(ValueError):
        parse_subject_scores(text)


def test_repeated_subject_cannot_fill_a_combination():
    assert combination_scores(parse_subject_scores('Toán 8, Toán 8, Anh 9')) == {}


@pytest.mark.parametrize('text,value', [
    ('năm 2024 em được 24.5 điểm',24.5),('tôi được 24,5 điểm',24.5),
    ('điểm 22 thì học gì',22),('0 điểm',0),('30',30),
])
def test_total(text,value):
    assert parse_total_score(text) == value


@pytest.mark.parametrize('text', ['31 điểm','-1 điểm','em được 99 điểm','điểm 20 và điểm 25','800 điểm đánh giá năng lực','25 điểm học bạ'])
def test_invalid_totals(text):
    with pytest.raises(ValueError):
        parse_total_score(text)


def test_year_and_combination_digits_are_not_scores():
    assert parse_total_score('tư vấn năm 2024 tổ hợp A01') is None


def test_subject_scores_are_not_a_total():
    with pytest.raises(ValueError):
        parse_total_score('8 điểm Toán, 8 điểm Hóa và 9 điểm Anh')


@pytest.mark.parametrize('value', ['nan','inf',float('nan'),-1,31])
def test_invalid_slot(value):
    with pytest.raises(ValueError):
        parse_total_score('tư vấn giúp', value)


@pytest.mark.parametrize('text,expected', [('năm nay',2026),('năm ngoái',2025),('2 năm trước',2024),('năm 2023',2023),('',None)])
def test_relative_year(text,expected):
    assert requested_year(text,today=date(2026,10,10)) == expected


def test_multiple_years_need_clarification():
    with pytest.raises(ValueError):
        requested_year('2023 và 2024')
