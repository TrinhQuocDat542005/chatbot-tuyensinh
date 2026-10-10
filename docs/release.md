# Phát hành portfolio v1.0.0

Mục tiêu đã chốt: repository để review, demo local và bản model tải lâu dài. Không yêu cầu VPS, Render, tên miền hoặc URL công khai. Tuần 7 triển khai Internet được hoãn; không tuyên bố đã đo tải hoặc hoàn thành nghiệm thu public.

## Người xem chạy bản phát hành

```bash
git clone --branch v1.0.0 https://github.com/TrinhQuocDat542005/chatbot-tuyensinh.git
cd chatbot-tuyensinh
```

Tải **model-bundle.zip** từ [Release v1.0.0](https://github.com/TrinhQuocDat542005/chatbot-tuyensinh/releases/tag/v1.0.0). Giải nén ba file bên trong vào `models/`, giữ nguyên tên `admissions-week4.tar.gz`, `.manifest.json` và `.sha256`. Tên file được giữ để tương thích Compose, không phải phiên bản phát hành. ZIP và từng asset có SHA-256 trong **SHA256SUMS.txt** trên cùng release.

```bash
python scripts/model_artifact.py verify
docker compose build train actions web
python scripts/manage.py up
```

Mở `http://localhost:8686`; xem năm tác vụ trong README. Docker cần Linux engine, script cần Python 3.10+. Node chỉ cần cho kiểm thử UI. Dừng bằng `python scripts/manage.py down`.

Windows kiểm tra ZIP: `Get-FileHash model-bundle.zip -Algorithm SHA256`. Linux: `sha256sum model-bundle.zip`. So sánh với dòng tương ứng trong SHA256SUMS trước khi giải nén. Lệnh verify kiểm tra checksum model và fingerprint input so với checkout; không chỉ tin vào tên file.

Nếu muốn train mới, dùng `python scripts/manage.py train` rồi `up`; trọng số và chỉ số có thể khác model phát hành. Không đổi manifest để giả vờ model đã train ở tag mới.

## Nguồn model

Model chuẩn lấy từ [workflow 38053556087](https://github.com/TrinhQuocDat542005/chatbot-tuyensinh/actions/runs/38053556087), checkout sạch `7be7e2f6d9b7e366cb41e408e46c7b087fc98597`. Source release bổ sung tài liệu và kiểm tra portfolio; model input được verify vẫn khớp. Model local từng train với dirty tree không dùng làm asset phát hành.

Kèm **evaluation.zip** từ cùng workflow, và **release-report.json** mô tả checksum, commit nguồn, các kiểm tra và giới hạn. Số liệu NLU trong README thuộc model/tập test được ghi rõ; không coi là số đo trên câu hỏi người dùng mới.

## Checklist người duy trì

1. Rà quyền sử dụng trong LICENSE/NOTICE, tác giả nghiên cứu và phạm vi dữ liệu.
2. Chạy audit tracked và lịch sử; xem xét findings, không in giá trị secret. Nếu có secret thật, thu hồi trước; không rewrite lịch sử khi chưa có kế hoạch.
3. Xác nhận CI/source model run thành công, tải artifact, so SHA-256 ZIP và verify manifest trên clone sạch.
4. Build/start/check/smoke trên clone sạch bằng bundle chuẩn. Không dùng model legacy.
5. Commit/push, đợi CI mới; tạo tag đúng commit và release kèm model/report/checksums. Kiểm tra link tải asset sau publish.

Thay đổi input model ở phiên bản sau phải train và đánh giá lại. Muốn quay về bản portfolio trước: checkout tag tương ứng, tải bundle của tag đó rồi verify/build/up. Không ghép model từ một tag với dữ liệu/actions không khớp.

## Backlog sau v1.0

- Demo HTTPS, giới hạn public API, privacy log/retention và benchmark tải/restart/rollback public.
- Xác minh thêm mô tả ngành, nghề nghiệp, điểm THPT cùng phương thức/thang điểm.
- Đánh giá mù bằng câu hỏi mới; kiểm toán accessibility và dependency/runtime lifecycle.
- Chọn giấy phép mở khi có quyền của tất cả bên liên quan. LLM/RAG chỉ là hướng thử nghiệm v1.1.
