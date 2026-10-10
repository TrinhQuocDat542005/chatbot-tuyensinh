# Portfolio v1.0.0

Ngày: 10/10/2026. Phạm vi theo quyết định chủ repository: GitHub portfolio và demo local; không thuê hosting hoặc nghiệm thu public deployment.

## Đã chuẩn bị

- README có ảnh/video thật, nghiên cứu AI King, quickstart, giới hạn và đường dẫn bản phát hành.
- CONTRIBUTING, SECURITY, LICENSE/NOTICE, changelog và issue/PR templates.
- Mã nguồn giữ quyền tác giả theo lựa chọn của chủ repository; PDF, dữ liệu nguồn và dependency có quyền riêng. Không cấp giấy phép MIT.
- Model chuẩn từ workflow GitHub sạch `38053556087`, commit `7be7e2f6`; manifest `working_tree_dirty: false`. Fingerprint khớp source portfolio; giữ nguyên provenance, không gán model cho commit tài liệu mới.
- Gói báo cáo không chứa service log hoặc feedback; có model/report/checksum và hướng dẫn chạy bản phát hành.
- Scanner tracked text trong CI; rà lịch sử có 25.000 blob và 70 findings trong dependency cũ. Đã review: AWS example identifiers, header constants, URL minh họa và PEM test fixtures (khớp bản package cài riêng), không phát hiện credential ứng dụng theo các mẫu đã kiểm tra.
- Các dependency cũ từng bị track trong lịch sử; không rewrite Git/LFS. Author credit/email commit và điểm giả của test được giữ có chủ đích. Scanner không chứng minh không có mọi loại secret/PII; binary nằm ngoài phạm vi.

## Kiểm tra trước phát hành

Model release CI đã có **141 test Python**, Core 10/10, 22+4 hội thoại REST và 13 nhóm browser thật pass; NLU **0,9010/0,9608** trên tập tự soạn đã review. Bộ audit có 3 kiểm tra nhận diện secret, không in giá trị và phát hiện `.env`.

Clone sạch đã build ba image và dùng bundle chuẩn: verify fingerprint/checksum, lint/schema, **141/141 Python**, Rasa validation và **Core 10/10** pass ở lần kiểm tra đầu. Sau sửa fallback, clone đồng bộ commit `7be7e2f6` và tải model release mới: ba service healthy; REST smoke 4/4, **22/22 hội thoại explicit + 4/4 natural**, **13/13 browser thật** pass, không có page error. Browser được chạy sau khi startup đã hoàn tất; một lượt chạy sớm bị gián đoạn khi thay container và đã được chạy lại đầy đủ. Bộ Python/Core cho source sửa fallback được kiểm tra lại đầy đủ trên runner GitHub sạch.

[CI source sửa fallback](https://github.com/TrinhQuocDat542005/chatbot-tuyensinh/actions/runs/38053556054) và [model regression](https://github.com/TrinhQuocDat542005/chatbot-tuyensinh/actions/runs/38053556087) đều success. Một lần fresh train trước đó phát hiện fallback trong form lặp 10 phản hồi rồi không xử lý lượt tiếp; đã đổi Core fallback sang action mặc định có revert, thêm giới hạn số phản hồi trong regression và train lại. Không sửa tập NLU hoặc hạ gate để đạt kết quả.

Tám model legacy được bỏ khỏi checkout hiện tại và quy tắc LFS mới được bỏ; file local/lịch sử vẫn giữ. Model chuẩn phân phối qua [Release v1.0.0](https://github.com/TrinhQuocDat542005/chatbot-tuyensinh/releases/tag/v1.0.0), không commit binary model mới vào source. [Báo cáo và provenance](evaluation/release-summary.json).

## Hoãn có chủ đích

Tuần 7 demo công khai, benchmark 5 phiên/100 request, HTTPS, public rate limit và rollback trên hosting là backlog. Chưa có URL public, chưa đạt tiêu chí tuần 7; không cần cho mục tiêu portfolio local. Các phần dữ liệu chưa xác minh và đánh giá mù bằng câu hỏi mới vẫn là giới hạn của v1.0.
