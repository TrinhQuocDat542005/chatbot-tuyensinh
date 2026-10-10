# Nguồn dữ liệu và quy trình kiểm chứng

Kiểm tra ngày 10/10/2026. Dữ liệu dùng cho UTH — Trường Đại học Giao thông vận tải TP.HCM, không phải UTC, UTC2 hoặc UTT. Những website này có tên trường tương tự nhưng không thể dùng thay thế nguồn UTH.

## Dữ liệu được dùng ở runtime

`actions/data/nganh.json` có schema version 1.0, dataset version 2026.10.10:

- 26 mục ngành, 41 mục chuyên ngành; mỗi mục có ID nội bộ, loại mục, ID ngành cha, alias, trạng thái và nguồn.
- 48 bản ghi điểm theo mã chương trình, phương thức, năm và đợt. Đây là tập con từ bảng chính và bổ sung năm 2026.
- 3 phần giới thiệu được diễn giải lại từ bài UTH; 2 phần có nội dung nghề nghiệp đã đối chiếu. Không xác minh toàn bộ nội dung trong JSON cũ.
- Mã ngành chưa có bằng chứng rõ được để `null` và `code_verification: pending`. Mã nội bộ `uth-xx` không được trình bày như mã ngành/mã xét tuyển.
- Mã chương trình năm 2026 như `UTHUIT05A` được lưu riêng trong bản ghi điểm chuẩn, không dùng làm mã ngành.

`actions/data/school.json` tách học phí, địa điểm, phương thức, chương trình và cơ sở vật chất khỏi các câu trả lời viết cứng trong domain. Học phí có số tiền, đơn vị, năm và chương trình áp dụng. Cơ sở vật chất chưa kiểm chứng đủ nên đang pending.

## Nguồn và bằng chứng

| Nguồn | Phạm vi đã đối chiếu | Giới hạn |
| --- | --- | --- |
| [Danh sách ngành/chuyên ngành Phòng Đào tạo UTH](https://daotao.ut.edu.vn/danh-sach-nganh-chuyen-nganh-dao-tao/) | Tên và quan hệ ngành/chuyên ngành theo khóa | Không phải bảng điểm hoặc cam kết tuyển sinh hiện hành; một số chuyên ngành chỉ thấy trong khóa cũ |
| [Điểm chuẩn chính quy 2026](https://tuyensinh.ut.edu.vn/thong-bao-diem-chuan-trung-tuyen-dai-hoc-chinh-quy-tai-uth-nam-2026/) | Mã chương trình và điểm xét tuyển kết hợp đợt chính | Bảng không xác minh công thức/quy đổi thang điểm; chỉ nhập tập con có liên hệ với danh mục của dự án |
| [Điểm chuẩn 2026 đợt bổ sung](https://tuyensinh.ut.edu.vn/thong-bao-diem-chuan-trung-tuyen-dai-hoc-chinh-quy-tai-uth-nam-2026-dot-bo-sung/) | 3 bản ghi bổ sung, giữ riêng đợt và chương trình | Không ghi đè điểm đợt chính |
| [Thông báo tuyển sinh chính quy 2026](https://tuyensinh.ut.edu.vn/thong-bao-tuyen-sinh-dai-hoc-chinh-quy-nam-2026/) | Sự tồn tại và URL thông báo | Chưa đọc được toàn bộ tài liệu đính kèm; chưa dùng để xác nhận công thức hoặc tổ hợp |
| [Thông báo Logistics liên kết quốc tế đợt 2/2026](https://tuyensinh.ut.edu.vn/thong-bao-tuyen-sinh-dai-hoc-2026-dot-2-chuong-trinh-cu-nhan-logistics-quoc-te-tich-hop-fiata/) | Học phí tại Việt Nam riêng chương trình liên kết | Không dùng làm học phí toàn trường, không tự trả học phí nước ngoài hoặc học phí năm khác |
| [Trang tuyển sinh UTH](https://tuyensinh.ut.edu.vn/) | Địa điểm giảng đường/cơ sở và thông tin liên hệ | Địa điểm học thực tế tùy chương trình; không tự kết luận năm nhất học tại cơ sở nào |
| [Giới thiệu CNKT điều khiển và tự động hóa](https://tuyensinh.ut.edu.vn/gioi-thieu-nganh-cong-nghe-ky-thuat-dieu-khien-va-tu-dong-hoa/) | Giới thiệu và nhóm nghề đã diễn giải | Không sao chép hoặc bảo đảm tuyển dụng |
| [Giới thiệu Kinh tế xây dựng](https://tuyensinh.ut.edu.vn/gioi-thieu-nganh-kinh-te-xay-dung/) | Giới thiệu và nhóm nghề đã diễn giải | Không xác minh bản ghi sai mã trong dữ liệu cũ |
| [Giới thiệu Mạng máy tính và truyền thông dữ liệu](https://tuyensinh.ut.edu.vn/mang-may-tinh-va-truyen-thong-du-lieu/) | Giới thiệu chương trình | Chưa dùng để xác nhận toàn bộ danh sách nghề cũ |
| [Thông báo CNTT của Phòng Đào tạo](https://daotao.ut.edu.vn/co-che-dac-thu-dao-tao-cac-nganh-thuoc-linh-vuc-cntt-trinh-do-dai-hoc-giai-doan-2017-2020/) | Mã ngành Mạng máy tính và truyền thông dữ liệu | Không phải số liệu tuyển sinh hiện hành |

Bằng chứng hiện tại là nội dung trang chính thức được công cụ tìm kiếm lập chỉ mục và trả về, ghi `evidence_type: indexed_official_page`. Một số lượt mở/tải trực tiếp bị Cloudflare 403; tài liệu PDF năm 2024 tại khoa Kinh tế gặp lỗi tải/DNS. Không lưu một bản HTML/PDF đầy đủ đã tải thành công cho các nguồn đó và không khẳng định đã đọc phần đính kèm chưa truy cập được. Cần bổ sung bằng chứng tài liệu gốc khi truy cập được.

## Audit 26 bản ghi cũ

- Bản gốc: `actions/data/legacy/nganh.original.json`.
- Báo cáo từng dòng: `actions/data/legacy/audit.json` (26 dòng, giữ tên/mã cũ, ánh xạ ID mới và ghi chú).
- Runtime chỉ đọc `nganh.json` và `school.json`; không đọc thư mục legacy.
- 114 giá trị điểm không null trong giai đoạn 2020–2024 còn pending vì thiếu nguồn/phương thức/thang điểm. Các giá trị null vẫn là thiếu dữ liệu, không chuyển thành 0.
- Nội dung giới thiệu/nghề nghiệp cũ được giữ nguyên trong archive để đối chiếu, không tự gắn nhãn verified.

Các sửa quan trọng:

| Dữ liệu cũ | Xử lý |
| --- | --- |
| Kinh tế xây dựng mang mã 7580202 | Cách ly nội dung cũ. Mục tương ứng trong danh mục là Kỹ thuật xây dựng công trình thủy; mã chính thức chưa tự công bố khi chưa có bằng chứng đủ rõ |
| Kỹ thuật điện, điện tử và điều khiển mang mã 7520207 | Tên này được mô hình hóa thành chuyên ngành Khoa học hàng hải. Mục ngành điện tử sửa tên thành Kỹ thuật điện tử - viễn thông |
| Logistics mang mã 7510605A | Giữ mã cũ trong audit; không coi hậu tố A là phần mã ngành chính thức |
| Smart logistics, Công nghệ ô tô số, Khoa học dữ liệu và AI | Mô hình hóa chuyên ngành của Công nghệ thông tin; không fuzzy match sang ngành ngoài trường |
| Ngành Hệ Thống Thông Tin Quản Lý | Chuẩn hóa tên và giữ alias hợp lệ |
| Nghề nghiệp CNKT cơ khí thiên về cảng/logistics | Cách ly, chờ đối chiếu nguồn đúng ngành |

## Quy tắc xác minh

1. Xác định đúng trường, chương trình và khóa/năm. Không dùng thông báo đào tạo thường xuyên để xác nhận chính quy hoặc dùng liên kết quốc tế để xác nhận toàn trường.
2. Phân biệt ngành, chuyên ngành và mã xét tuyển của chương trình. Alias chỉ ánh xạ khi nguồn xác nhận quan hệ; tên mơ hồ phải hỏi lại.
3. Điểm phải có phương thức, năm, mã chương trình, đợt và nguồn. Thang điểm không rõ để null và không dùng cho phép so sánh. Ngưỡng đầu vào không được gọi là điểm chuẩn.
4. Trích xuất đúng nội dung có bằng chứng; ghi URL, ngày công bố khi biết, ngày kiểm tra và phạm vi. Nếu chỉ đọc được tiêu đề/link, không xác nhận nội dung bên trong.
5. Chỉ chuyển `pending` thành `verified` sau đối chiếu. Dữ liệu pending không được gửi như thông tin xác nhận.
6. Chạy schema, kiểm tra tham chiếu, regression và smoke test. Có thay đổi model input thì train/test lại.

## Kiểm tra

```bash
python scripts/validate_data.py
python -m pytest -q
```

Loader từ chối JSON hỏng, sai schema, ID/alias mơ hồ, tham chiếu nguồn/ngành không tồn tại, chuyên ngành thuộc sai ngành, điểm ngoài thang điểm đã khai báo và phương thức không rõ bị đánh dấu verified. Nguồn verified phải thuộc domain UTH. Thông tin trường được kiểm tra nguồn ngay khi load, không chỉ ở script validation.

Không xem “schema hợp lệ” là “thông tin đúng”: schema chỉ kiểm tra cấu trúc và tính nhất quán. Những nội dung legacy và phần chưa đọc được vẫn là công việc xác minh còn lại.
