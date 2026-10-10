"""Authored state-transition acceptance cases, not generated from implementation."""
import json
from pathlib import Path


def turn(intent, contains, entities=None, excludes=None):
    return {'intent': intent, 'entities': entities or {}, 'contains': contains, 'excludes': excludes or []}


def main():
    intro = lambda major='CNTT': turn('hoi_thong_tin_gioi_thieu_chung_cua_nganh', ['Công nghệ thông tin'] if major == 'CNTT' else [major], {'ten_nganh': major})
    cutoff = lambda year='2026', method=None: turn('hoi_diem_chuan_cua_nganh', ['UTHUIT05A'] if year == '2026' else ['Chưa có', year], {'ten_nganh': 'CNTT', 'nam': year, **({'phuong_thuc': method} if method else {})})
    follow = lambda entities, contains, excludes=None: turn('bo_sung_tra_cuu', contains, entities, excludes)
    missing = turn('hoi_thong_tin_gioi_thieu_chung_cua_nganh', ['ngành nào'])
    score = lambda value: turn('tu_van_nganh_theo_diem', [f'{value}/30'], {'diem': str(value)})
    cases = [
        ('missing-major', [missing, follow({'ten_nganh': 'CNTT'}, ['Công nghệ thông tin'])]),
        ('missing-year', [turn('hoi_diem_chuan_cua_nganh', ['năm nào'], {'ten_nganh': 'CNTT'}), follow({'nam': '2026'}, ['UTHUIT05A'])]),
        ('year-replacement', [cutoff(), follow({'nam': '2023'}, ['Chưa có', '2023'], ['UTHUIT05A'])]),
        ('new-major-clears-year', [cutoff(), follow({'ten_nganh': 'Ngôn ngữ Anh'}, ['năm nào'], ['UTHUIT05A']), follow({'nam': '2026'}, ['UTHNNA01A'])]),
        ('same-major-keeps-year', [cutoff(), follow({'ten_nganh': 'CNTT'}, ['UTHUIT05A'])]),
        ('method-thpt', [cutoff(), follow({'phuong_thuc': 'THPT'}, ['Chưa có'], ['UTHUIT05A'])]),
        ('method-back-to-combined', [cutoff(), follow({'phuong_thuc': 'THPT'}, ['Chưa có']), follow({'phuong_thuc': 'xét tuyển kết hợp'}, ['UTHUIT05A'])]),
        ('unknown-major-replacement', [cutoff(), follow({'ten_nganh': 'Ngành ABC'}, ['ngành nào'], ['UTHUIT05A']), follow({'ten_nganh': 'Ngôn ngữ Anh', 'nam': '2026'}, ['UTHNNA01A'])]),
        ('restart-clears-context', [cutoff(), turn('bat_dau_lai', ['phiên mới']), follow({'nam': '2026'}, ['ngành nào'], ['Công nghệ thông tin ('])]),
        ('restart-in-form', [missing, turn('bat_dau_lai', ['phiên mới']), turn('hoi_diem_chuan_cua_nganh', ['ngành nào'], {'nam': '2026'})]),
        ('cancel-in-form', [missing, turn('huy_tra_cuu', ['Đã hủy']), follow({'nam': '2026'}, ['ngành nào'])]),
        ('bad-major-in-form', [missing, follow({'ten_nganh': 'ABC'}, ['ngành nào']), follow({'ten_nganh': 'CNTT'}, ['Công nghệ thông tin'])]),
        ('score-asks-value', [turn('tu_van_nganh_theo_diem', ['tổng điểm']), turn('tu_van_nganh_theo_diem', ['24.5/30'], {'diem': '24,5'})]),
        ('score-out-of-range', [turn('tu_van_nganh_theo_diem', ['tổng điểm'], {'diem': '31'}), score(0)]),
        ('score-replacement', [score(24), score(26)]),
        ('score-fresh-request', [score(25), turn('tu_van_nganh_theo_diem', ['tổng điểm'], excludes=['25/30']), score(22)]),
        ('isolated-new-session', [follow({'nam': '2026'}, ['ngành nào'])]),
        ('fallback-in-form', [missing, turn('nlu_fallback', ['chưa hiểu']), follow({'ten_nganh': 'CNTT'}, ['Công nghệ thông tin'])]),
        ('name-optional', [turn('chao_hoi', ['không cần cung cấp tên'], excludes=['cho tôi biết tên']), intro()]),
        ('career-context', [intro(), turn('hoi_co_hoi_viec_lam_cua_nganh', ['Công nghệ thông tin'], excludes=['ngành nào'])]),
        ('explicit-new-year-new-major', [cutoff('2024'), follow({'ten_nganh': 'Ngôn ngữ Anh', 'nam': '2026'}, ['UTHNNA01A'], ['năm 2024'])]),
        ('zero-total', [score(0)]),
    ]
    Path(__file__).with_name('scenarios.json').write_text(json.dumps([{'id': name, 'turns': turns} for name, turns in cases], ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
