# Portfolio v1.0.0

Ngày: 10/10/2026. Phạm vi theo quyết định chủ repository: GitHub portfolio và demo local; không thuê hosting hoặc nghiệm thu public deployment.

## Đã chuẩn bị

- README có ảnh/video thật, nghiên cứu AI King, quickstart, giới hạn và đường dẫn bản phát hành.
- CONTRIBUTING, SECURITY, LICENSE/NOTICE, changelog và issue/PR templates.
- Mã nguồn tạm giữ quyền tác giả; PDF, dữ liệu nguồn và dependency có quyền riêng. Chưa cấp MIT khi quyền của các đồng tác giả chưa được xác nhận.
- Model chuẩn từ workflow GitHub sạch `38050433408`, commit `3847c5ac`; manifest `working_tree_dirty: false`. Fingerprint khớp source portfolio; giữ nguyên provenance, không gán model cho commit mới.
- Gói báo cáo không chứa service log hoặc feedback; có model/report/checksum và hướng dẫn chạy bản phát hành.
- Scanner tracked text trong CI; rà lịch sử có 25.000 blob và 70 findings trong dependency cũ. Đã review: AWS example identifiers, header constants, URL minh họa và PEM test fixtures (khớp bản package cài riêng), không phát hiện credential ứng dụng theo các mẫu đã kiểm tra.
- Các dependency cũ từng bị track trong lịch sử; không rewrite Git/LFS. Author credit/email commit và điểm giả của test được giữ có chủ đích. Scanner không chứng minh không có mọi loại secret/PII; binary nằm ngoài phạm vi.

## Kiểm tra trước phát hành

Model CI đã có 138 test Python, Core 10/10, 22+4 hội thoại REST và 13 nhóm browser thật pass; NLU 0,9117/0,9596 trên tập tự soạn đã review. Bộ audit thêm 3 kiểm tra nhận diện secret, không in giá trị và phát hiện `.env`.

Clone sạch, build/start/check bằng bundle chuẩn và CI source portfolio phải được xác nhận trước publish; kết quả sẽ được cập nhật tại đây khi hoàn tất.

## Hoãn có chủ đích

Tuần 7 demo công khai, benchmark 5 phiên/100 request, HTTPS, public rate limit và rollback trên hosting là backlog. Chưa có URL public, chưa đạt tiêu chí tuần 7; không cần cho mục tiêu portfolio local. Các phần dữ liệu chưa xác minh và đánh giá mù bằng câu hỏi mới vẫn là giới hạn của v1.0.
