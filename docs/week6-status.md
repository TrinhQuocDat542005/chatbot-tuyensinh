# Tuần 6: Docker, CI và khả năng tái lập

Ngày kiểm tra: 10/10/2026. Phạm vi theo [roadmap](ROADMAP.md): tách runtime, kiểm tra tự động và model truy vết. Không triển khai public hoặc phát hành v1.0.

## Đã triển khai

- Action server có Dockerfile/image SDK riêng; không chứa Rasa/TensorFlow. Compose dùng hostname `actions:5055`, healthcheck và thứ tự khởi động rõ ràng.
- Lock Linux đầy đủ cho runtime Rasa và SDK; cài sạch vào container, `pip check`. Dependency test Windows không bị ép cài lock Linux.
- Script quản lý chạy trên Windows/WSL/Linux: build → force train → manifest/checksum → verify → up/check/down.
- Manifest ghi commit và trạng thái working tree, fingerprint dataset/config/custom component/action code, package thực cài, size/SHA-256 model. Khởi động từ chối model bị sửa hoặc không khớp checkout.
- CI mỗi PR có correctness lint Python, actionlint, syntax JavaScript, YAML/JSON chống duplicate key, schema/reference validation, unit/HTTP tests và UI mock.
- Model regression tự động khi input/runtime/test liên quan thay đổi, mỗi tuần hoặc manual: build sạch, train, Core/NLU, gate chỉ số, REST/natural conversation và browser với model thật.
- Artifact model gồm đúng một model hiện hành, manifest và checksum theo commit; report có JUnit, metrics, hội thoại, ảnh và service log. Không upload tám model legacy.
- Hướng dẫn tái lập, artifact, biến môi trường, health/log và giới hạn: [reproducibility.md](reproducibility.md).

## Bằng chứng đã chạy

- Build sạch Rasa từ `requirements-lock.linux.txt` thành công; dependency check pass.
- Build image SDK riêng và môi trường checks thành công; image SDK khoảng 270 MB trước lớp lock cuối (kích thước image, không phải RAM).
- Ruff, parse YAML/JSON, schema/reference và actionlint pass.
- **138/138 test Python pass**: 117 backend, 14 HTTP gateway và 7 kiểm tra tái lập/CI.
- Test lỗi có chủ đích chứng minh từ chối catalog trùng ID, duplicate key YAML/JSON, model đổi bytes, model đúng checksum nhưng sai input và NLU dưới ngưỡng.

Train/model, hội thoại và kiểm tra workflow trên GitHub đang được nghiệm thu; kết quả cuối sẽ được ghi sau khi hoàn tất.

## Giới hạn

Lock chưa có hash wheel, base Python vẫn dùng tag OS; không hứa tái lập bit-for-bit. Fresh train có thể cho chỉ số khác tuần 4. Tập NLU đã được review nên là hồi quy, chưa xác nhận trên câu người dùng mới. Chưa bật branch protection hoặc public deployment. Artifact CI có hạn lưu; release lâu dài và license thuộc tuần 8.
