import copy
import json

import pytest

from actions.repository import DataError, find_major, load_catalog, load_document, verified_admissions


def test_all_production_documents_validate():
    doc=load_catalog()
    assert len(doc['majors']) >= 26
    assert load_document('school')['facts']['hoi_hoc_phi']['year'] == 2026


def test_alias_resolves_to_canonical_major():
    assert find_major('cntt',load_catalog())['ten_nganh'] == 'Công nghệ thông tin'


def test_specialization_does_not_become_an_independent_major():
    doc=load_catalog()
    spec=find_major('Smart logistics',doc)
    assert spec['kind']=='specialization'
    assert spec['parent_id']==find_major('Công nghệ thông tin',doc)['id']


def test_wrong_legacy_name_is_not_an_alias():
    doc=load_catalog()
    assert find_major('Kinh tế xây dựng',doc)['id'] != find_major('Kỹ thuật xây dựng công trình thủy',doc)['id']
    assert find_major('Kỹ thuật điện, điện tử và điều khiển',doc)['parent_id'] == find_major('Khoa học hàng hải',doc)['id']


def test_combined_scores_never_leak_into_thpt_recommendations():
    doc=load_catalog()
    assert verified_admissions(doc,year=2026,method='ket_hop')
    assert verified_admissions(doc,method='thpt')==[]
    assert verified_admissions(doc,year=2024)==[]


def test_latest_verified_year_not_latest_unverified():
    doc=copy.deepcopy(load_catalog())
    row=copy.deepcopy(doc['admissions'][0])
    row['year']=2027
    row['verification']='pending'
    doc['admissions'].append(row)
    assert {a['year'] for a in verified_admissions(doc)}=={2026}


@pytest.mark.parametrize('mutation', [
    lambda d:d['majors'].append(copy.deepcopy(d['majors'][0])),
    lambda d:d['admissions'][0].update(major_id='missing'),
    lambda d:d['admissions'][0].update(source_id='missing'),
    lambda d:d['admissions'][0].update(cutoff=31,score_max=30),
    lambda d:d['admissions'][0].update(method='unknown'),
    lambda d:d['majors'][1]['aliases'].append(d['majors'][0]['ten_nganh']),
    lambda d:d['majors'][0].update(parent_id='missing'),
    lambda d:d['admissions'][0]['specialization_ids'].append('missing'),
    lambda d:d['sources'][0].update(url='https://unofficial.example.com/'),
    lambda d:d['sources'][1].update(verification='pending'),
])
def test_semantic_corruption_is_rejected(tmp_path,mutation):
    doc=copy.deepcopy(load_catalog())
    mutation(doc)
    (tmp_path/'nganh.json').write_text(json.dumps(doc),encoding='utf-8')
    with pytest.raises(DataError):load_catalog(tmp_path)


def test_broken_json_is_rejected(tmp_path):
    (tmp_path/'nganh.json').write_text('{invalid',encoding='utf-8')
    with pytest.raises(DataError):load_catalog(tmp_path)


def test_verified_profile_cannot_have_no_evidence(tmp_path):
    doc=copy.deepcopy(load_catalog())
    doc['majors'][0]['profile'].update(verification='verified')
    (tmp_path/'nganh.json').write_text(json.dumps(doc),encoding='utf-8')
    with pytest.raises(DataError):load_catalog(tmp_path)


def test_school_runtime_validates_references(tmp_path):
    doc=copy.deepcopy(load_document('school'))
    doc['facts']['hoi_hoc_phi']['source_ids']=['missing']
    (tmp_path/'school.json').write_text(json.dumps(doc),encoding='utf-8')
    with pytest.raises(DataError):load_document('school',tmp_path)
