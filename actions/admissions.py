"""Validated score parsing, independent of Rasa and training models."""

import math
import re
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo


def normalize(text):
    text = unicodedata.normalize("NFD", str(text).lower()).replace("đ", "d")
    return " ".join("".join(c for c in text if not unicodedata.combining(c)).split())


SUBJECTS = {
    "toan": "toán", "vat ly": "lý", "ly": "lý", "hoa hoc": "hóa",
    "hoa": "hóa", "tieng anh": "anh", "anh van": "anh", "anh": "anh",
    "ngu van": "văn", "van": "văn", "sinh hoc": "sinh", "sinh": "sinh",
    "lich su": "sử", "su": "sử", "dia ly": "địa", "dia": "địa",
}
COMBINATIONS = {
    "A00": ("toán", "lý", "hóa"), "A01": ("toán", "lý", "anh"),
    "B00": ("toán", "hóa", "sinh"), "C00": ("văn", "sử", "địa"),
    "C01": ("toán", "văn", "lý"), "D01": ("toán", "văn", "anh"),
    "D07": ("toán", "hóa", "anh"),
}
NUMBER = r"-?\d+(?:[.,]\d+)?"
SUBJECT_PATTERN = "|".join(sorted(SUBJECTS, key=len, reverse=True))


def validated_score(value, maximum):
    try:
        score = float(str(value).replace(",", "."))
    except (ValueError, TypeError):
        raise ValueError("Điểm phải là số.") from None
    if not math.isfinite(score) or not 0 <= score <= maximum:
        raise ValueError(f"Điểm phải nằm trong khoảng 0–{maximum}.")
    return score


def parse_subject_scores(text):
    text = normalize(text)
    patterns = (
        rf"(?<![\w.,-])(?P<score>{NUMBER})\s*(?:diem\s+)(?P<subject>{SUBJECT_PATTERN})\b",
        rf"\b(?P<subject>{SUBJECT_PATTERN})\s*(?::|=|duoc|dat|thanh)?\s*(?P<score>{NUMBER})(?:\s*diem)?\b",
    )
    scores = {}
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            subject = SUBJECTS[match["subject"]]
            score = validated_score(match["score"], 10)
            if subject in scores and scores[subject] != score:
                raise ValueError(f"Bạn cung cấp hai điểm khác nhau cho môn {subject}.")
            scores[subject] = score
    return scores


def combination_scores(scores):
    for subject, value in scores.items():
        if subject not in SUBJECTS.values():
            raise ValueError("Môn học chưa được hỗ trợ.")
        validated_score(value, 10)
    return {code: round(sum(scores[s] for s in subjects), 2)
            for code, subjects in COMBINATIONS.items() if all(s in scores for s in subjects)}


def parse_total_score(text, slot=None):
    if parse_subject_scores(text):
        raise ValueError("Bạn đã nhập điểm từng môn; hãy dùng chức năng tính tổ hợp.")
    text = normalize(text)
    if any(term in text for term in ("hoc ba", "dgnl", "danh gia nang luc", "ket hop")):
        raise ValueError("Tổng điểm này chỉ hỗ trợ phép tính 3 môn THPT thang 30; phương thức khác cần thông tin riêng.")
    patterns = (rf"(?<![\w.,-])({NUMBER})\s*diem\b",
                rf"\b(?:tong diem|diem)\s*(?:la|:|=)?\s*({NUMBER})(?![\d.,])")
    values = []
    for pattern in patterns:
        values.extend(m.group(1) for m in re.finditer(pattern, text))
    if re.fullmatch(NUMBER, text):
        values.append(text)
    if values:
        scores = {validated_score(value, 30) for value in values}
        if len(scores) != 1:
            raise ValueError("Bạn đã nhập nhiều tổng điểm; vui lòng xác nhận một tổng điểm.")
        return scores.pop()
    if slot is not None:
        return validated_score(slot, 30)
    return None


def requested_year(text, today=None):
    text = normalize(text or "")
    year = (today or datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date()).year
    explicit = re.findall(r"\b(?:19|20)\d{2}\b", text)
    if len(set(explicit)) > 1:
        raise ValueError("Vui lòng chọn một năm để tra cứu.")
    if explicit:
        return int(explicit[0])
    if re.search(r'\bnam\s+\d+\b', text) or re.fullmatch(r'\d{4}', text):
        raise ValueError('Năm tra cứu phải nằm trong khoảng 1900–2099.')
    if "nam nay" in text:
        return year
    match = re.search(r"\b(\d+) nam truoc\b", text)
    if match:
        return year - int(match[1])
    if "nam ngoai" in text or "nam truoc" in text:
        return year - 1
    return None
