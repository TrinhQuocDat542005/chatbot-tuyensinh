"""Authored evaluation phrases, kept separate from all training files."""
from pathlib import Path
import yaml

PHRASES = {
 'chao_hoi': 'Chào trợ lý, mình mới tới đây|Xin chào hệ thống tư vấn|Buổi tối vui vẻ nha bot|Hello, có ai tư vấn không|Chào UTH, em cần hỗ trợ|chao ad tuyen sinh|xin chaoo bot',
 'nhap_ten': 'Bạn cứ gọi em là [Hà](ten_nguoi_dung)|Tên đầy đủ của mình là [Mai Linh](ten_nguoi_dung)|Em xin giới thiệu em tên [Hoàng](ten_nguoi_dung)|Mình có tên là [Thảo](ten_nguoi_dung)|Tên em: [Ngọc](ten_nguoi_dung)|toi ten [Nam](ten_nguoi_dung) nhe|minh ten la [An](ten_nguoi_dung) a',
 'hoi_nganh_tuyen_sinh': 'Có thể liệt kê ngành đào tạo giúp em được chứ|Danh mục các ngành của UTH gồm những gì|Cho mình một danh sách ngành để lựa chọn|UTH dạy những ngành đại học nào vậy|Có bao nhiêu ngành trong danh mục trường|ke ten cac nganh o UTH giup minh|danh sach nghanh cua truong dau',
 'hoi_thong_tin_gioi_thieu_chung_cua_nganh': 'Cho mình tổng quan về [Kinh tế xây dựng](ten_nganh) nhé|[Công nghệ thông tin](ten_nganh) học kiến thức gì vậy|Nội dung ngành [Ngôn ngữ Anh](ten_nganh) gồm gì|Bạn giải thích ngành [Kỹ thuật xây dựng](ten_nganh) cho mình|Em cần một mô tả về [Kỹ thuật điện](ten_nganh)|nganh [CNTT](ten_nganh) hoc kien thuc nao|gioi thieu [Logistics và quản lý chuỗi cung ứng](ten_nganh) voi a',
 'hoi_co_hoi_viec_lam_cua_nganh': 'Tốt nghiệp [Kinh tế xây dựng](ten_nganh) có thể làm nghề nào|Vị trí công việc cho ngành [Kỹ thuật điện](ten_nganh) là gì|Học [Công nghệ thông tin](ten_nganh) xong làm ở lĩnh vực nào|Ra trường ngành đó có các lựa chọn việc làm gì|Nghề nghiệp sau khi học [Ngôn ngữ Anh](ten_nganh) ra sao|co hoi nghe nghiep cua [CNTT](ten_nganh) the nao|viec lam nganh [Logistics và quản lý chuỗi cung ứng](ten_nganh) sau tot nghiep',
 'hoi_diem_chuan_cua_nganh': 'Mức điểm trúng tuyển [Công nghệ thông tin](ten_nganh) năm [2026](nam) là gì|Mình muốn biết điểm chuẩn [Kỹ thuật điện](ten_nganh) đợt chính năm [2026](nam)|[Ngôn ngữ Anh](ten_nganh) cần điểm chuẩn bao nhiêu năm [2025](nam)|Xem điểm chuẩn của ngành đó cho năm [2023](nam) giúp em|Tra mức trúng tuyển [Kinh tế xây dựng](ten_nganh) theo THPT năm [2026](nam)|diem trung tuyen [CNTT](ten_nganh) nam [2024](nam) la may|diem chuan nganh [Kỹ thuật xây dựng](ten_nganh) nam [2026](nam) ket hop bao nhieu',
 'hoi_khoi_tuyen_sinh_cua_nganh': 'Những tổ hợp thi nào dùng xét ngành [Công nghệ thông tin](ten_nganh)|Ngành [Ngôn ngữ Anh](ten_nganh) chấp nhận khối nào năm [2026](nam)|[Kỹ thuật điện](ten_nganh) tuyển bằng tổ hợp môn gì|Em muốn xem khối xét tuyển của ngành đó|Tổ hợp vào [Kinh tế xây dựng](ten_nganh) năm [2024](nam) là gì|nganh [CNTT](ten_nganh) xet mon nao nam [2026](nam)|khoi tuyen sinh [Logistics và quản lý chuỗi cung ứng](ten_nganh) gom gi',
 'hoi_chuong_trinh_dao_tao_cua_truong': 'UTH tổ chức các chương trình đào tạo thế nào|Trường có các bậc đào tạo nào cho sinh viên|Giới thiệu về hệ đào tạo ở UTH giúp em|Có thể tìm thông tin chương trình đào tạo toàn trường ở đâu|Hệ đại học của UTH có những chương trình gì|cac he dao tao tai UTH la gi|cho minh xem chuong trinh daotao cua truong',
 'hoi_hoc_phi': 'Một năm học cần đóng học phí bao nhiêu vậy|Cho em thông tin tiền học của UTH|Mức thu học phí của trường năm [2026](nam) là gì|Học phí năm [2024](nam) có thông tin không|Chi phí học Logistics quốc tế tại Việt Nam là bao nhiêu|hoc phi o UTH moi nam may tien|hocphí nam [2026](nam) nhu nao a',
 'hoi_dia_diem_hoc': 'Sinh viên sẽ đến địa chỉ nào để học|UTH có cơ sở học tập tại những nơi nào|Bạn chỉ giúp mình địa điểm các cơ sở học|Học ở UTH thì học ở quận nào vậy|Các cơ sở giảng dạy nằm tại đâu|co so hoc o dau vay bot|dia chi truong UTH nam cho nao',
 'hoi_phuong_thuc_xet_tuyen': 'Muốn xét tuyển vào UTH thì có những cách nào|Thông báo tuyển sinh dùng phương thức gì năm [2026](nam)|UTH có nhận xét hồ sơ học bạ không|Em muốn tìm các hình thức tuyển sinh của trường|Có thể xem quy chế xét tuyển kết hợp ở đâu|UTH xet tuyen theo nhung cach gi|phuong thuc tuyensinh nam [2026](nam) co gi',
 'hoi_co_so_vat_chat': 'Điều kiện phòng học ở trường như thế nào|Khu thực hành của UTH có thông tin gì|Có thông tin về thư viện và phòng máy không|Em muốn xem điều kiện ký túc xá trường|Cơ sở vật chất phục vụ học tập ra sao|truong co cho o ky tuc xa khong|phong thi nghiem UTH nhu nao',
 'cam_on': 'Cảm ơn vì đã giải đáp cho mình nha|Mình cảm ơn sự hỗ trợ này|Dạ em cảm ơn rất nhiều|Cảm ơn, mình đã hiểu thông tin rồi|Thanks vì đã hướng dẫn mình|cam on bot da tu van|cam onnn ad',
 'tam_biet': 'Mình chào bạn nhé, hẹn lần sau|Em xin phép kết thúc, tạm biệt|Bye bot, mình đi học đây|Hẹn gặp bạn trong buổi tư vấn tới|Tạm biệt, chúc bạn buổi tối tốt lành|tam biet nha bot|hen gap lai lan khac nhe',
 'tu_van_nganh_theo_so_thich': 'Em mê chế tạo robot thì nên tìm hiểu ngành nào|Mình hứng thú với lập trình thì học ngành gì phù hợp|Em thích tìm hiểu động cơ ô tô, gợi ý ngành nhé|Mình yêu ngoại ngữ thì chọn ngành nào|Em đam mê xây dựng công trình nên học gì|minh thich may tinh tu van nganh voi|em me logistics nen chon nganh gi',
 'tu_van_nganh_theo_diem': 'Với tổng [22,75](diem) điểm THPT thì tham khảo ngành nào|Em đạt [28.25](diem) điểm, gợi ý lựa chọn học giúp em|Tổng điểm thi của mình là [16](diem), tư vấn ngành nhé|Mình sửa tổng điểm thành [25,25](diem) điểm|Em muốn được tư vấn theo tổng điểm thi|em co [21,75](diem) diem nen hoc nghanh nao|diem moi la [27.5](diem) diem tu van lai nhe',
 'cung_cap_diem': '[Toán](mon_hoc) [8.75](d), [Hóa](mon_hoc) [7.25](d), [Anh](mon_hoc) [9.5](d) thì tính tổ hợp giúp em|Em thi được [6.25](d) điểm [Toán](mon_hoc), [7.75](d) điểm [Lý](mon_hoc) và [8.5](d) điểm [Anh](mon_hoc)|Mình có [8.5](d) điểm [Văn](mon_hoc), [7.5](d) điểm [Sử](mon_hoc) và [6.5](d) điểm [Địa](mon_hoc)|Sửa [Toán](mon_hoc) thành [7.25](d), [Hóa](mon_hoc) thành [8.75](d), [Anh](mon_hoc) thành [9.25](d)|Tính tổ hợp với [Toán](mon_hoc) [9.25](d), [Lý](mon_hoc) [8.25](d), [Hóa](mon_hoc) [7.25](d), [Anh](mon_hoc) [6.25](d)|[Toan](mon_hoc) [6,75](d), [Hoa](mon_hoc) [7,25](d), [Anh](mon_hoc) [8,75](d) tinh diem voi|minh co [9.25](d) diem [Toán](mon_hoc), [8.75](d) diem [Hóa](mon_hoc), [7.25](d) diem [Anh](mon_hoc)',
 'bo_sung_tra_cuu': 'Nếu đổi năm thành [2022](nam) thì sao|Chuyển sang [Kinh tế xây dựng](ten_nganh) giúp mình|Vẫn ngành đó nhưng xem năm [2021](nam)|Đổi lựa chọn ngành thành [Kỹ thuật điện](ten_nganh)|Xem tiếp theo phương thức học bạ|con nam [2020](nam) nua thi sao|doi sang [Ngôn ngữ Anh](ten_nganh) nhe bot',
 'bat_dau_lai': 'Mình muốn xóa ngữ cảnh và hỏi từ đầu|Khởi tạo cuộc trò chuyện mới cho em|Xóa tên cùng điểm mình đã gửi nhé|Đặt lại toàn bộ thông tin tư vấn cho mình|Hãy quên ngành và năm mình vừa chọn|reset tat ca thong tin da nhap|bat dau lai tu dau cho em nhe',
 'huy_tra_cuu': 'Mình muốn hủy yêu cầu đang nhập|Bỏ phần tra cứu hiện tại giúp em|Em không muốn tiếp tục nhập điểm nữa|Dừng luồng hỏi bổ sung này lại|Thoát yêu cầu tư vấn đang mở nhé|huy yeu cau tra cuu dang mo|thoi minh khong muon tra cuu nua',
}
OOD = ['Ngày mai thời tiết ở Hà Nội ra sao', 'Tạo giúp em một bài thơ về mùa xuân', 'Bạn dự đoán giá vàng tuần tới đi', 'Mua vé máy bay tới Đà Nẵng giúp mình', 'Cho mình lời khuyên mua cổ phiếu', 'Hướng dẫn chữa đau răng tại nhà', 'Ai sẽ thắng trận bóng đá tối nay', 'Làm sao hack tài khoản người khác', 'Giải bài tích phân này giúp tôi', 'Trường khác có điểm chuẩn ngành y bao nhiêu', 'Tôi muốn tìm điểm chuẩn Đại học Bách khoa', 'Đặt bàn ăn cho bốn người tối nay', 'thoi tiet hom nay the nao', 'asdkj qwerty 987 xyz']


def main():
    rows = []
    for intent, phrases in PHRASES.items():
        for index, text in enumerate(phrases.split('|')):
            rows.append({'id': f'{intent}-{index+1}', 'intent': intent, 'text': text,
                         'difficulty': 'hard' if index >= 5 else 'normal', 'group': f'{intent}-heldout'})
    rows += [{'id': f'ood-{i+1}', 'intent': 'nlu_fallback', 'text': text, 'difficulty': 'ood', 'group': 'ood-heldout'} for i, text in enumerate(OOD)]
    Path(__file__).with_name('nlu.yml').write_text(yaml.safe_dump({'version': '1.0', 'examples': rows}, allow_unicode=True, sort_keys=False), encoding='utf-8')
    print('Frozen evaluation examples:', len(rows))


if __name__ == '__main__':
    main()
