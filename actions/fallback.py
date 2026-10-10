"""Reapply Rasa's fallback decision while preserving its learned fallback label."""
import math


def macro_f1(gold, predicted):
    labels = set(gold) | set(predicted)
    if not labels or len(gold) != len(predicted):
        raise ValueError('Expected equally sized, nonempty predictions and labels.')
    scores = []
    for label in labels:
        tp = sum(a == b == label for a, b in zip(gold, predicted))
        fp = sum(a != label and b == label for a, b in zip(gold, predicted))
        fn = sum(a == label and b != label for a, b in zip(gold, predicted))
        scores.append(2 * tp / (2 * tp + fp + fn))
    return sum(scores) / len(scores)


def original_ranking(row, source_threshold):
    ranking = list(row['ranking'])
    added = row.get('fallback_added')
    if added is None:
        # Older reports predate explicit provenance. Rasa inserts exactly its
        # configured threshold as confidence, unlike the DIET probability.
        added = bool(ranking and ranking[0]['name'] == 'nlu_fallback'
                     and math.isclose(ranking[0]['confidence'], source_threshold, abs_tol=1e-12, rel_tol=0))
    if added:
        ranking = ranking[1:]
    if not ranking:
        raise ValueError('Missing original intent ranking; reevaluate this dataset.')
    return ranking


def prediction_at_threshold(row, threshold, source_threshold=0.7, ambiguity=0.1):
    ranking = original_ranking(row, source_threshold)
    top = ranking[0]
    second = ranking[1]['confidence'] if len(ranking) > 1 else 0
    fallback = top['confidence'] < threshold or top['confidence'] - second < ambiguity
    return 'nlu_fallback' if fallback else top['name']
