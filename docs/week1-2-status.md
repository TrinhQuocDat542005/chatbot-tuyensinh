# Nghiệm thu tuần 1–2

Ngày triển khai: 10/10/2026. Phạm vi theo tuần 1–2 của [ROADMAP](ROADMAP.md). Báo cáo này cập nhật kết quả thực thi; phần đánh giá hiện trạng trong roadmap giữ nguyên để đối chiếu trước/sau.

## Thay đổi đã triển khai

| Đầu việc | Kết quả |
| --- | --- |
| Môi trường Rasa | Python 3.10; dependency có version; Docker Linux phục vụ train/test/server local |
| Domain và NLU | Bổ sung intent thiếu, sửa annotation `ten_ngành`, khai báo fallback, chuẩn hóa regex/lookup, loại ví dụ trùng |
| Parser điểm | Hỗ trợ dấu phẩy/chấm, tên môn có/không dấu, hai thứ tự nhập; từ chối điểm ngoài thang, môn lặp mâu thuẫn và tổng điểm mơ hồ |
| Tính tổ hợp | Chỉ tính khi đủ môn; xét tất cả tổ hợp hỗ trợ; sửa trường hợp Toán 8 + Hóa 8 + Anh 9 = D07 25 |
| Custom action | 10 action, tách parser/repository, xử lý ngành không rõ và dữ liệu lỗi; bỏ ghép tên gần đúng tự động |
| Dữ liệu ngành | 26 ngành + 41 chuyên ngành, alias, quan hệ cha/con, nguồn và trạng thái kiểm chứng |
| Điểm chuẩn | 48 bản ghi xét tuyển kết hợp 2026, phân biệt chương trình, đợt, năm và phương thức |
| Thông tin trường | Học phí, địa điểm, chương trình và tuyển sinh chuyển khỏi response cố định sang JSON có nguồn/phạm vi |
| Kiểm tra dữ liệu | JSON Schema và kiểm tra tham chiếu, trùng ID/alias, nguồn, thang điểm và quan hệ chuyên ngành |
| Repository | Sửa encoding, ignore môi trường/model mới, script chạy local, README và hướng dẫn nguồn dữ liệu |

## Kết quả kiểm tra

- Python trên Windows: **69 test pass**. Chính sách Application Control của máy chặn DLL scikit-learn khi train; train chuyển sang Docker Linux, không thay đổi chính sách Windows.
- Build Docker: cài dependency từ image Python 3.10 mới; `pip check` không phát hiện dependency không tương thích.
- Python trong Docker Linux: **69 test pass**; schema hợp lệ cho 67 bản ghi danh mục, 48 điểm chuẩn và 5 nhóm thông tin trường.
- `rasa data validate --fail-on-warnings`: **pass**.
- Train Docker: **thành công**, model mới `models/admissions-week1-2.tar.gz` (29.786.776 byte).
- Core: **10/10 hội thoại pass**, **21/21 dự đoán action đúng**, không có cảnh báo hội thoại.
- Smoke SDK: **4/4 kiểm tra HTTP pass**, gồm D07 = 25/30, điểm chuẩn 2026, năm chưa có dữ liệu và học phí đúng phạm vi.
- Smoke REST: **4/4 câu hỏi pass** qua NLU → Core → SDK: danh sách ngành, điểm chuẩn CNTT 2026, tính D07 và học phí.
- Hai service Docker `actions` và `rasa` đã khởi động và đạt healthcheck, chỉ mở ở localhost 5055 và 5005.

SHA-256 của model trong lần nghiệm thu: `8bc2fe1659c4c640decce06ba69e27ef917cdc5481fea150c380abf80e82c60a`. Train lại có thể tạo hash khác. TensorFlow và dependency Rasa cũ có cảnh báo deprecation; chưa thực hiện nâng cấp stack ngoài phạm vi tuần 1–2.

Các tiêu chí nghiệm thu tuần 1–2 trong roadmap đã đạt: môi trường sạch cài được, train và REST chạy được, lỗi regression đã sửa, dữ liệu runtime qua schema và thông tin xác quyết có nguồn. Điều này không đồng nghĩa toàn bộ dữ liệu gốc đã được xác minh; các phần còn thiếu dưới đây được loại khỏi trả lời xác quyết.

Core test kiểm tra dự đoán action, không thực thi custom action. Smoke SDK kiểm tra nội dung action qua HTTP; smoke REST kiểm tra NLU → Core → SDK → dữ liệu. Các kịch bản này chưa thay thế tập đánh giá NLU độc lập, và không chứng minh accuracy/F1 trên câu mới.

## Những phần dữ liệu vẫn chưa xác minh

- 114 giá trị điểm chuẩn lịch sử trong dữ liệu gốc chưa đủ nguồn/phương thức/thang điểm. Bản gốc và audit 26 ngành được giữ trong `actions/data/legacy/`; runtime không đọc dữ liệu đó.
- Danh mục đã kiểm tra tên và quan hệ ngành/chuyên ngành. Mã ngành chính thức chỉ điền khi có bằng chứng; ID `uth-*` là ID nội bộ. Một danh mục đào tạo không chứng minh mọi chuyên ngành đang tuyển sinh năm 2026.
- Có 3 phần giới thiệu và 2 danh sách nghề nghiệp được kiểm chứng. Chi tiết còn lại và cơ sở vật chất giữ trạng thái `pending`; bot chỉ dẫn đến nguồn chính thức.
- Học phí 79 triệu đồng/năm chỉ áp dụng chương trình Logistics quốc tế được nguồn chỉ định, tại Việt Nam năm 2026. Không áp dụng chung toàn trường.
- Điểm xét tuyển kết hợp không được so trực tiếp với tổng 3 môn THPT thang 30. Gợi ý ngành theo điểm THPT chờ dữ liệu cùng phương thức và thang điểm có nguồn.
- Một số website nguồn chặn truy cập trực tiếp. Những bản ghi đối chiếu từ nội dung được công cụ tìm kiếm lập chỉ mục trên trang chính thức có `evidence_type: indexed_official_page`; chưa được coi là đã tải và kiểm tra PDF gốc. Chi tiết ở [data-sources.md](data-sources.md).

## Cách tái kiểm tra

```bash
docker compose build train
docker compose run --rm train
docker compose run --rm check
docker compose up -d --wait actions rasa
docker compose exec actions python scripts/smoke_actions.py
docker compose exec rasa python scripts/smoke_rest.py
```

Model của lần nghiệm thu tuần 1–2 nằm trong `models/admissions-week1-2.tar.gz` và bị ignore. Các lệnh trên hiện sử dụng cấu hình/model tuần 4; xem [báo cáo tuần 4](week4-status.md) để biết kết quả mới nhất. Các model LFS cũ vẫn còn trong lịch sử, chưa chỉnh sửa lịch sử Git.

Tuần 3–8 tiếp tục theo roadmap: hoàn thiện tư vấn khi có dữ liệu phù hợp, hội thoại nhiều lượt, đánh giá NLU độc lập, giao diện, CI và phát hành. Docker local được đưa lên sớm để giải quyết trở ngại môi trường tuần 1.
