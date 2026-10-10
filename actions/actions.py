"""Rasa adapters: answer only with source-verified admissions facts."""

import logging
import re
from abc import ABC, abstractmethod

from rasa_sdk import Action
from rasa_sdk.events import SlotSet, AllSlotsReset, ActiveLoop
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.interfaces import ActionExecutionRejection

from actions.admissions import combination_scores, normalize, parse_subject_scores, parse_total_score, requested_year
from actions.repository import DataError, find_major, load_catalog, load_document, source_text, verified_admissions
from actions.conversation import LOOKUPS, lookup_updates, major_from_message, method_from_text

LOGGER = logging.getLogger(__name__)
OFFICIAL_URL = "https://tuyensinh.ut.edu.vn/"
DATA_ERROR = "Dữ liệu đang tạm thời không khả dụng. Xem thông tin tại " + OFFICIAL_URL
DISCLAIMER = "Điểm chuẩn đã công bố chỉ dùng để tham khảo, không bảo đảm trúng tuyển."


def query_year(tracker):
    return requested_year(tracker.latest_message.get("text", "")) or requested_year(tracker.get_slot("nam"))


def catalog(dispatcher):
    try:
        return load_catalog()
    except DataError:
        LOGGER.exception("Unable to load catalog")
        dispatcher.utter_message(text=DATA_ERROR)
        return None


class ActionXuLyTen(Action):
    def name(self):
        return "action_xu_ly_ten"

    def process_name(self, name):
        return " ".join("".join(c for c in (name or "") if c.isalpha() or c.isspace()).split()).title()

    def run(self, dispatcher, tracker, domain):
        name = self.process_name(tracker.get_slot("ten_nguoi_dung"))
        if not name:
            dispatcher.utter_message(text="Bạn có thể tra cứu ngay hoặc cho tôi biết tên của bạn.")
            return []
        return [SlotSet("ten_nguoi_dung", name)]


class ActionTraLoiNganhTuyenSinh(Action):
    def name(self):
        return "action_tra_loi_nganh_tuyen_sinh"

    def run(self, dispatcher, tracker, domain):
        doc = catalog(dispatcher)
        if doc is None:
            return []
        majors = [m for m in doc["majors"] if m["verification"] == "verified" and m["kind"] == "major"]
        dispatcher.utter_message(text="Các ngành trong danh mục đào tạo UTH đã đối chiếu nguồn:\n"
                                 + "\n".join(f"{i}. {m['ten_nganh']}" for i, m in enumerate(majors, 1))
                                 + "\nDanh mục đào tạo không thay thế thông báo tuyển sinh từng năm.\n"
                                 + source_text(doc, [s for m in majors for s in m["source_ids"]]))
        return []


class MajorAction(Action, ABC):
    @abstractmethod
    def answer(self, dispatcher, tracker, doc, major):
        """Implemented by concrete actions; never registered by the SDK."""
        raise NotImplementedError

    def name(self):
        return self.action_name

    def run(self, dispatcher, tracker, domain):
        doc = catalog(dispatcher)
        if doc is None:
            return []
        name = tracker.get_slot("ten_nganh")
        if not name:
            dispatcher.utter_message(text="Bạn muốn tra cứu ngành nào? Ví dụ: Công nghệ thông tin.")
            return []
        major = find_major(name, doc)
        if major is None:
            dispatcher.utter_message(text="Tên ngành chưa có trong danh mục đã xác minh. Bạn hãy nhập tên đầy đủ hoặc hỏi danh sách ngành.")
            return []
        try:
            self.answer(dispatcher, tracker, doc, major)
        except ValueError as exc:
            dispatcher.utter_message(text=str(exc))
        return [SlotSet("ten_nganh", major["ten_nganh"])]


def major_records(doc, major, year=None, method=None):
    records = verified_admissions(doc, major["parent_id"] or major["id"], year, method)
    if major["kind"] == "specialization":
        records = [a for a in records if major["id"] in a["specialization_ids"]]
    return records


class ActionTraLoiThongTinNganh(MajorAction):
    action_name = "action_tra_loi_thong_tin_nganh"

    def answer(self, dispatcher, tracker, doc, major):
        children = [m["ten_nganh"] for m in doc["majors"] if m["parent_id"] == major["id"] and m["verification"] == "verified"]
        text = f"UTH có {('ngành' if major['kind'] == 'major' else 'chuyên ngành')} {major['ten_nganh']} trong danh mục đã đối chiếu."
        if children:
            text += "\nChuyên ngành trong dữ liệu: " + "; ".join(children) + "."
        profile = major["profile"]
        text += "\n" + (profile["summary"] if profile["verification"] == "verified" else "Giới thiệu chi tiết đang được kiểm chứng; xem chương trình tại nguồn chính thức.")
        dispatcher.utter_message(text=text + "\n" + source_text(doc, [*major["source_ids"], *profile["source_ids"]]))


class ActionTraLoiCoHoiViecLam(MajorAction):
    action_name = "action_tra_loi_co_hoi_viec_lam"

    def answer(self, dispatcher, tracker, doc, major):
        profile = major["profile"]
        text = (f"Cơ hội nghề nghiệp của {major['ten_nganh']}:\n" + "\n".join(profile["careers"])) if profile["verification"] == "verified" and profile["careers"] else f"Thông tin nghề nghiệp chi tiết của {major['ten_nganh']} chưa được xác minh. Vui lòng xem chương trình đào tạo chính thức."
        dispatcher.utter_message(text=text + "\n" + source_text(doc, profile["source_ids"] if profile["verification"] == "verified" and profile["careers"] else major["source_ids"]))


class ActionTraLoiDiemChuanNganh(MajorAction):
    action_name = "action_tra_loi_diem_chuan_nganh"

    def answer(self, dispatcher, tracker, doc, major):
        year = query_year(tracker)
        text = normalize(tracker.latest_message.get("text", ""))
        method = method_from_text(text) or tracker.get_slot('phuong_thuc')
        records = major_records(doc, major, year, method)
        if not records:
            dispatcher.utter_message(text=f"Chưa có điểm chuẩn đã xác minh cho {major['ten_nganh']}" + (f" năm {year}" if year else "") + (f" theo phương thức {method}" if method else "") + f". Xem thông báo: {OFFICIAL_URL}")
            return
        lines = [f"Điểm chuẩn đã công bố của {major['ten_nganh']} (năm {records[0]['year']}):"]
        for a in records:
            scale = f"thang {a['score_max']}" if a["score_max"] is not None else "theo quy chế xét tuyển kết hợp; không phải tổng 3 môn thang 30"
            lines.append(f"- {a['program_code']} — {a['program_label']}, đợt {a['round']}: {a['cutoff']:g} điểm ({a['method_label']}; {scale}).")
        dispatcher.utter_message(text="\n".join([*lines, DISCLAIMER, source_text(doc, [a["source_id"] for a in records])]))


class ActionTraLoiKhoiXetTuyen(MajorAction):
    action_name = "action_tra_loi_khoi_xet_tuyen"

    def answer(self, dispatcher, tracker, doc, major):
        records = major_records(doc, major, query_year(tracker), "thpt")
        codes = sorted({c for a in records for c in a["combinations"]})
        text = (f"Tổ hợp THPT của {major['ten_nganh']}: {', '.join(codes)} (năm {records[0]['year']}).\n" + source_text(doc, [a["source_id"] for a in records])) if codes else "Chưa có tổ hợp xét tuyển THPT đã xác minh cho ngành/năm này. " + OFFICIAL_URL
        dispatcher.utter_message(text=text)


def recommend(dispatcher, doc, scores, year):
    records = verified_admissions(doc, year=year, method="thpt")
    candidates = [a for a in records if a["score_max"] == 30 and any(code in a["combinations"] and value >= a["cutoff"] for code, value in scores.items())]
    if candidates:
        dispatcher.utter_message(text="Chương trình để tham khảo:\n" + "\n".join(f"- {a['program_code']} ({a['program_label']}), năm {a['year']}: {a['cutoff']:g}." for a in sorted(candidates, key=lambda a: a["cutoff"], reverse=True)[:5]) + "\n" + DISCLAIMER + "\n" + source_text(doc, [a["source_id"] for a in candidates]))
    else:
        dispatcher.utter_message(text="Chưa có chương trình phù hợp trong điểm chuẩn THPT đã xác minh" + (f" năm {year}" if year else "") + ". Điểm xét tuyển kết hợp không thể so trực tiếp với tổng 3 môn. " + OFFICIAL_URL)


class ActionTuVanNganhTheoDiem(Action):
    def name(self):
        return "action_tu_van_nganh_theo_diem"

    def run(self, dispatcher, tracker, domain):
        try:
            score = parse_total_score(tracker.latest_message.get("text", ""), tracker.get_slot("diem"))
            year = query_year(tracker)
        except ValueError as exc:
            dispatcher.utter_message(text=str(exc))
            return []
        if score is None:
            dispatcher.utter_message(text="Bạn hãy nhập tổng điểm 3 môn THPT thang 30, ví dụ: 24,5 điểm.")
            return []
        doc = catalog(dispatcher)
        if doc is None:
            return []
        combos = re.findall(r"\b(?:A00|A01|B00|C00|C01|D01|D07)\b", tracker.latest_message.get("text", "").upper())
        if not verified_admissions(doc, year=year, method="thpt"):
            dispatcher.utter_message(text=f"Tổng điểm 3 môn của bạn là {score:g}/30. Chưa có điểm chuẩn THPT đã xác minh" + (f" năm {year}" if year else "") + ". Không thể so với điểm xét tuyển kết hợp. " + OFFICIAL_URL)
        elif len(set(combos)) != 1:
            dispatcher.utter_message(text="Bạn xét tổ hợp nào? Vui lòng chọn một tổ hợp như A00, A01 hoặc D07.")
        else:
            recommend(dispatcher, doc, {combos[0]: score}, year)
        return [SlotSet("diem", score)]


class ActionTuVanNganhTheoSoThich(Action):
    def name(self):
        return "action_tu_van_nganh_theo_so_thich"

    def run(self, dispatcher, tracker, domain):
        doc = catalog(dispatcher)
        if doc is None:
            return []
        text = normalize(tracker.latest_message.get("text", ""))
        majors = [m for m in doc["majors"] if m["kind"] == "major" and m["verification"] == "verified" and any(normalize(tag) in text for tag in m["interest_tags"])][:5]
        if not majors:
            dispatcher.utter_message(text="Bạn quan tâm lĩnh vực nào? Ví dụ lập trình, ô tô, xây dựng hoặc ngoại ngữ.")
        else:
            dispatcher.utter_message(text="Gợi ý khám phá theo từ khóa sở thích (chưa phải đánh giá năng lực nghề nghiệp):\n" + "\n".join(f"- {m['ten_nganh']}" for m in majors) + "\n" + source_text(doc, [s for m in majors for s in m["source_ids"]]))
        return []


class ActionTinhKhoiVaGoiYNganh(Action):
    def name(self):
        return "action_tinh_khoi_va_goi_y_nganh"

    def run(self, dispatcher, tracker, domain):
        try:
            scores = combination_scores(parse_subject_scores(tracker.latest_message.get("text", "")))
            year = query_year(tracker)
        except ValueError as exc:
            dispatcher.utter_message(text=str(exc))
            return []
        if not scores:
            dispatcher.utter_message(text="Bạn hãy nhập đủ điểm các môn của một tổ hợp, ví dụ: 8 điểm Toán, 8 điểm Hóa và 9 điểm Anh. Điểm mỗi môn từ 0 đến 10.")
            return []
        dispatcher.utter_message(text="Tổng các tổ hợp đủ môn (chưa cộng ưu tiên hoặc quy đổi):\n" + "\n".join(f"- {code}: {score:g}/30" for code, score in sorted(scores.items())))
        doc = catalog(dispatcher)
        if doc is not None:
            recommend(dispatcher, doc, scores, year)
        return []


class ActionTraLoiThongTinTruong(Action):
    def name(self):
        return "action_tra_loi_thong_tin_truong"

    def run(self, dispatcher, tracker, domain):
        try:
            doc = load_document("school")
        except DataError:
            LOGGER.exception("Unable to load school facts")
            dispatcher.utter_message(text=DATA_ERROR)
            return []
        fact = doc["facts"].get(tracker.latest_message.get("intent", {}).get("name"))
        if not fact or fact["verification"] != "verified":
            dispatcher.utter_message(text="Thông tin này đang được kiểm chứng. Xem thông báo chính thức: " + OFFICIAL_URL)
            return []
        try:
            year = query_year(tracker)
        except ValueError as exc:
            dispatcher.utter_message(text=str(exc))
            return []
        if year is not None and fact["year"] is not None and year != fact["year"]:
            dispatcher.utter_message(text=f"Chưa có thông tin đã xác minh năm {year} cho nội dung này. " + OFFICIAL_URL)
        else:
            dispatcher.utter_message(text=fact["text"] + "\n" + source_text(doc, fact["source_ids"]))
        return []


class ActionPrepareLookup(Action):
    def name(self):
        return 'action_prepare_lookup'

    def run(self, dispatcher, tracker, domain):
        doc = catalog(dispatcher)
        if doc is None:
            return [SlotSet('ten_nganh', None)]
        try:
            updates = lookup_updates(tracker, doc)
        except ValueError as exc:
            dispatcher.utter_message(text=str(exc))
            # Discard old context on an invalid explicit replacement.
            updates = {'ten_nganh': None, 'nam': None, 'phuong_thuc': None,
                       'lookup_intent': tracker.latest_message.get('intent', {}).get('name')
                       if tracker.latest_message.get('intent', {}).get('name') in LOOKUPS
                       else tracker.get_slot('lookup_intent')}
        return [SlotSet(key, value) for key, value in updates.items()]


class ValidateTraCuuNganhForm(FormValidationAction):
    def name(self):
        return 'validate_tra_cuu_nganh_form'

    async def run(self, dispatcher, tracker, domain):
        intent = tracker.latest_message.get('intent', {}).get('name')
        valid_input = False
        if intent == 'nlu_fallback' and tracker.get_slot('requested_slot'):
            try:
                if tracker.get_slot('requested_slot') == 'nam':
                    valid_input = requested_year(tracker.latest_message.get('text', '')) is not None
                else:
                    valid_input = major_from_message(tracker, load_catalog()) is not None
            except (ValueError, DataError):
                pass
        if intent in {'bat_dau_lai', 'huy_tra_cuu'} or (intent == 'nlu_fallback' and not valid_input and tracker.latest_action_name != 'utter_default'):
            raise ActionExecutionRejection('tra_cuu_nganh_form')
        return await super().run(dispatcher, tracker, domain)

    async def required_slots(self, domain_slots, dispatcher, tracker, domain):
        return ['ten_nganh', 'nam'] if tracker.get_slot('lookup_intent') in {
            'hoi_diem_chuan_cua_nganh', 'hoi_khoi_tuyen_sinh_cua_nganh'} else ['ten_nganh']

    async def extract_ten_nganh(self, dispatcher, tracker, domain):
        doc = catalog(dispatcher)
        if doc is None:
            return {'ten_nganh': None}
        try:
            major = major_from_message(tracker, doc)
        except ValueError as exc:
            dispatcher.utter_message(text=str(exc))
            return {'ten_nganh': None, 'nam': None, 'phuong_thuc': None}
        if major is None and tracker.get_slot('requested_slot') == 'ten_nganh':
            dispatcher.utter_message(text='Tên ngành chưa rõ. Hãy nhập tên đầy đủ, ví dụ Công nghệ thông tin.')
            return {'ten_nganh': None}
        if not major:
            return {}
        result = {'ten_nganh': major}
        if normalize(major) != normalize(tracker.get_slot('ten_nganh') or ''):
            result.update(nam=None, phuong_thuc=None)
            try:
                year = requested_year(tracker.latest_message.get('text', ''))
                result['nam'] = str(year) if year else None
                result['phuong_thuc'] = method_from_text(tracker.latest_message.get('text', ''))
            except ValueError as exc:
                dispatcher.utter_message(text=str(exc))
        return result

    async def extract_nam(self, dispatcher, tracker, domain):
        try:
            year = requested_year(tracker.latest_message.get('text', ''))
            method = method_from_text(tracker.latest_message.get('text', ''))
        except ValueError as exc:
            dispatcher.utter_message(text=str(exc))
            return {'nam': None, 'phuong_thuc': None}
        result = {'nam': str(year)} if year else {}
        if method:
            result['phuong_thuc'] = method
        if not year and tracker.get_slot('requested_slot') == 'nam':
            dispatcher.utter_message(text='Hãy nhập một năm rõ ràng, ví dụ 2026 hoặc năm ngoái.')
            result['nam'] = None
        return result

    def validate_ten_nganh(self, value, dispatcher, tracker, domain):
        doc = catalog(dispatcher)
        major = find_major(value, doc) if doc and value else None
        return {'ten_nganh': major['ten_nganh'] if major else None}

    def validate_nam(self, value, dispatcher, tracker, domain):
        try:
            year = requested_year(str(value or ''))
        except ValueError:
            year = None
        return {'nam': str(year) if year else None}


class ActionSubmitLookup(Action):
    def name(self):
        return 'action_submit_lookup'

    def run(self, dispatcher, tracker, domain):
        action_name = LOOKUPS.get(tracker.get_slot('lookup_intent'))
        action_class = next((cls for cls in [ActionTraLoiThongTinNganh, ActionTraLoiCoHoiViecLam,
                             ActionTraLoiDiemChuanNganh, ActionTraLoiKhoiXetTuyen]
                             if cls.action_name == action_name), ActionTraLoiThongTinNganh)
        return action_class().run(dispatcher, tracker, domain)


class ActionPrepareScore(Action):
    def name(self):
        return 'action_prepare_score'

    def run(self, dispatcher, tracker, domain):
        try:
            entity = next((e['value'] for e in tracker.latest_message.get('entities', []) if e['entity'] == 'diem'), None)
            value = parse_total_score(tracker.latest_message.get('text', ''), entity)
        except ValueError as exc:
            dispatcher.utter_message(text=str(exc))
            value = None
        return [SlotSet('diem', value)]


class ValidateTuVanDiemForm(FormValidationAction):
    def name(self):
        return 'validate_tu_van_diem_form'

    async def run(self, dispatcher, tracker, domain):
        intent = tracker.latest_message.get('intent', {}).get('name')
        valid_input = False
        if intent == 'nlu_fallback' and tracker.get_slot('requested_slot') == 'diem':
            try:
                valid_input = parse_total_score(tracker.latest_message.get('text', '')) is not None
            except ValueError:
                pass
        if intent in {'bat_dau_lai', 'huy_tra_cuu'} or (intent == 'nlu_fallback' and not valid_input and tracker.latest_action_name != 'utter_default'):
            raise ActionExecutionRejection('tu_van_diem_form')
        return await super().run(dispatcher, tracker, domain)

    async def extract_diem(self, dispatcher, tracker, domain):
        try:
            entity = next((e['value'] for e in tracker.latest_message.get('entities', []) if e['entity'] == 'diem'), None)
            value = parse_total_score(tracker.latest_message.get('text', ''), entity)
        except ValueError as exc:
            dispatcher.utter_message(text=str(exc))
            return {'diem': None}
        return {'diem': value} if value is not None else {}

    def validate_diem(self, value, dispatcher, tracker, domain):
        try:
            return {'diem': parse_total_score(str(value))}
        except ValueError as exc:
            dispatcher.utter_message(text=str(exc))
            return {'diem': None}


class ActionCancelConsultation(Action):
    def name(self):
        return 'action_huy_tra_cuu'

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text='Đã hủy tra cứu và xóa ngữ cảnh. Bạn có thể hỏi câu mới.')
        return [ActiveLoop(None), AllSlotsReset()]
