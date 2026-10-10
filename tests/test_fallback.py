from actions.fallback import macro_f1, original_ranking, prediction_at_threshold
import pytest


def test_only_inserted_fallback_is_removed():
    row = {'ranking': [{'name': 'nlu_fallback', 'confidence': 0.7},
                       {'name': 'nlu_fallback', 'confidence': 0.6},
                       {'name': 'chao_hoi', 'confidence': 0.2}]}
    assert original_ranking(row, 0.7)[0]['name'] == 'nlu_fallback'
    assert prediction_at_threshold(row, 0.4) == 'nlu_fallback'


def test_confident_learned_fallback_is_preserved():
    row = {'ranking': [{'name': 'nlu_fallback', 'confidence': 0.99},
                       {'name': 'chao_hoi', 'confidence': 0.01}]}
    assert prediction_at_threshold(row, 0.4) == 'nlu_fallback'


def test_new_threshold_restores_underlying_intent():
    row = {'ranking': [{'name': 'nlu_fallback', 'confidence': 0.7},
                       {'name': 'chao_hoi', 'confidence': 0.65},
                       {'name': 'cam_on', 'confidence': 0.2}]}
    assert prediction_at_threshold(row, 0.5) == 'chao_hoi'
    assert prediction_at_threshold(row, 0.7) == 'nlu_fallback'


def test_ambiguity_still_triggers_fallback():
    row = {'ranking': [{'name': 'chao_hoi', 'confidence': 0.55},
                       {'name': 'cam_on', 'confidence': 0.5}]}
    assert prediction_at_threshold(row, 0.4) == 'nlu_fallback'


def test_explicit_provenance_takes_precedence():
    row = {'fallback_added': False, 'ranking': [{'name': 'nlu_fallback', 'confidence': 0.7},
                                               {'name': 'chao_hoi', 'confidence': 0.2}]}
    assert original_ranking(row, 0.7) == row['ranking']


def test_missing_ranking_is_rejected():
    with pytest.raises(ValueError):
        original_ranking({'ranking': []}, 0.7)


def test_macro_f1_counts_missed_labels():
    assert macro_f1(['a', 'b'], ['a', 'a']) == pytest.approx(1/3)


def test_macro_f1_rejects_incomplete_predictions():
    with pytest.raises(ValueError):
        macro_f1(['a', 'b'], ['a'])
