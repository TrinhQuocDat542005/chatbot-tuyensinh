# Đóng góp

Dự án portfolio tập trung vào chatbot tuyển sinh UTH chạy local. Đọc [README](README.md), [phạm vi dữ liệu](docs/data-sources.md) và [quyền sử dụng](NOTICE.md) trước khi gửi thay đổi.

## Báo lỗi và đề xuất

Tìm issue hiện có trước khi mở issue mới. Ghi câu hỏi mẫu, kết quả mong đợi/thực tế, commit, hệ điều hành và cách chạy. Dùng tên/điểm giả; không gửi hội thoại thật, token, file `.env` hoặc log chưa rà dữ liệu cá nhân. Lỗ hổng bảo mật được báo theo [SECURITY](SECURITY.md).

## Quy trình pull request

1. Tạo branch từ `main`; giữ mỗi PR tập trung vào một vấn đề.
2. Khi sửa nghiệp vụ, thêm test tái hiện lỗi; khi sửa NLU, giữ tập đánh giá trong `tests/evaluation/`, ngoài dữ liệu train.
3. Dữ liệu mới phải có nguồn chính thức, ngày kiểm tra, năm, phương thức, thang điểm và trạng thái xác minh. Không suy diễn điểm thiếu, không coi điểm lịch sử là bảo đảm trúng tuyển.
4. Chạy các kiểm tra phù hợp bên dưới và mô tả kết quả thực đo trong PR. Không hạ ngưỡng hoặc sửa tập test để che regression.
5. Cập nhật tài liệu và changelog nếu hành vi hoặc phạm vi thay đổi. Không commit model mới, môi trường, log hoặc dữ liệu cá nhân.

## Kiểm tra

Với Python 3.10 và dependency checks đã cài:

```bash
python -m pip install -r requirements-check.txt
python scripts/check_project.py
python scripts/validate_data.py
python scripts/audit_repository.py
python -m ruff check actions components scripts tests
python -m pytest -q
```

Khi có Docker Linux:

```bash
python scripts/manage.py train
python scripts/manage.py check
python scripts/manage.py up
docker compose exec actions python scripts/smoke_actions.py
docker compose exec rasa python scripts/check_conversations.py
```

UI cần Node.js 20+ chỉ khi chạy test: `npm ci`, `npx playwright install chromium`, `npm run test:web`. CI chạy kiểm tra nhẹ trên PR; workflow model kiểm tra train/Core/NLU/UI thật khi input liên quan thay đổi. Xem [tái lập](docs/reproducibility.md).

Chỉ gửi nội dung mà bạn có quyền đóng góp. Quyền của PDF, nguồn dữ liệu và dependency không thay đổi khi chúng được tham chiếu trong PR.
