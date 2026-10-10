import pytest
from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.executor import ActionExecutor

from actions import actions


def run(action,text='',slots=None,intent=None):
    tracker=Tracker('test-user',slots or {},{'text':text,'intent':{'name':intent}},[],False,None,{},'action_listen')
    dispatcher=CollectingDispatcher()
    events=action.run(dispatcher,tracker,{})
    return '\n'.join(m.get('text','') or '' for m in dispatcher.messages),events


def test_subject_action_reports_d07():
    text,_=run(actions.ActionTinhKhoiVaGoiYNganh(),'8 điểm Toán, 8 điểm Hóa và 9 điểm Anh')
    assert 'D07: 25/30' in text
    assert 'A00' not in text
    assert 'đủ điểm' not in text


def test_total_action_does_not_compare_to_combined_score():
    text,events=run(actions.ActionTuVanNganhTheoDiem(),'24,5 điểm năm 2026')
    assert '24.5/30' in text
    assert 'Không thể so' in text
    assert events[0]['value']==24.5


def test_cutoff_includes_program_year_method_source():
    text,_=run(actions.ActionTraLoiDiemChuanNganh(),'điểm chuẩn năm 2026',{'ten_nganh':'CNTT'})
    assert 'UTHUIT05A' in text and '2026' in text and '720' in text
    assert 'không phải tổng 3 môn' in text and 'Nguồn:' in text


def test_requested_missing_year_is_not_replaced_with_latest():
    text,_=run(actions.ActionTraLoiDiemChuanNganh(),'điểm chuẩn năm 2024',{'ten_nganh':'CNTT','nam':'2026'})
    assert 'Chưa có' in text and '2024' in text
    assert '720' not in text


def test_cutoff_for_specialization_does_not_inherit_other_program():
    text,_=run(actions.ActionTraLoiDiemChuanNganh(),'điểm chuẩn năm 2026',{'ten_nganh':'Smart logistics'})
    assert 'UTHUIT02A' in text
    assert 'UTHUIT05A' not in text


def test_method_is_respected():
    text,_=run(actions.ActionTraLoiDiemChuanNganh(),'điểm chuẩn THPT năm 2026',{'ten_nganh':'CNTT'})
    assert 'Chưa có' in text and '720' not in text


def test_missing_major_asks_question():
    text,_=run(actions.ActionTraLoiThongTinNganh())
    assert 'ngành nào' in text


def test_unverified_careers_are_not_returned():
    text,_=run(actions.ActionTraLoiCoHoiViecLam(),slots={'ten_nganh':'Công nghệ kỹ thuật cơ khí'})
    assert 'chưa được xác minh' in text
    assert 'marketing' not in text


def test_interest_suggestions_only_use_catalog():
    text,_=run(actions.ActionTuVanNganhTheoSoThich(),'tôi thích lập trình')
    assert 'Công nghệ thông tin' in text
    assert 'Kỹ thuật phần mềm' not in text


def test_fees_are_scoped_not_universal():
    text,_=run(actions.ActionTraLoiThongTinTruong(),intent='hoi_hoc_phi')
    assert '79 triệu' in text and 'KHÔNG áp dụng chung' in text
    assert '2026' in text and 'Nguồn:' in text


def test_school_facts_respect_requested_year():
    text,_=run(actions.ActionTraLoiThongTinTruong(),'học phí năm 2024',intent='hoi_hoc_phi')
    assert 'Chưa có' in text and '79 triệu' not in text


def test_error_does_not_expose_path(monkeypatch):
    def fail():raise actions.DataError('E:/private/path.json')
    monkeypatch.setattr(actions,'load_catalog',fail)
    text,_=run(actions.ActionTraLoiNganhTuyenSinh())
    assert 'tạm thời' in text and 'private' not in text


def test_sdk_discovers_only_concrete_actions():
    executor=ActionExecutor()
    executor.register_package('actions')
    assert 'action_tra_loi_diem_chuan_nganh' in executor.actions
    assert len(executor.actions)==16
    assert 'validate_tra_cuu_nganh_form' in executor.actions
    assert 'validate_tu_van_diem_form' in executor.actions
