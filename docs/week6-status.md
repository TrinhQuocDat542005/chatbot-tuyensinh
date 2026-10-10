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

- Fresh train local thành công; model có manifest, checksum và fingerprint khớp checkout. Lần train này bắt đầu trước commit triển khai, nên manifest giữ đúng base commit tuần 5 và `working_tree_dirty: true`.
- **Core 10/10**, 26 dự đoán action đúng, không có prediction warning; 4 smoke SDK và 4 smoke REST pass.
- **22/22 hội thoại REST có intent tường minh và 4/4 hội thoại bằng câu tự nhiên pass**.
- **13/13 nhóm browser với model thật pass**, không có JavaScript page error; desktop và mobile đều được kiểm tra.
- NLU fresh model trên 154 câu tự soạn cố định: **macro-F1 intent 0,9394; entity exact-span F1 0,9505** (96 TP, 3 FP, 7 FN). Gate ≥0,90/≥0,85 pass. Không sửa train/test hoặc threshold trong tuần này.
- Clone sạch commit `3847c5ac` vào thư mục kiểm thử riêng: artifact có fingerprint khớp, Compose parse thành công, không có thay đổi tracked. Lần này kiểm tra đường dùng artifact đã train; GitHub model workflow kiểm tra build/train/start từ checkout sạch.
- [CI trên GitHub](https://github.com/TrinhQuocDat542005/chatbot-tuyensinh/actions/runs/38050433383) **success**: 138 test, 13 browser mock và report artifact đã xuất.
- [Model regression trên GitHub](https://github.com/TrinhQuocDat542005/chatbot-tuyensinh/actions/runs/38050433408) **success** trên checkout sạch commit `3847c5ac`: build mới, validation, force train, verify, 138 test/Core, gate NLU, start ba service, smoke SDK/REST, 22+4 hội thoại và 13 browser thật đều pass. Đây là kiểm chứng đường build/train/start/check tương đương quick start từ source Git, không dùng model local hay venv/cache môi trường cũ.
- NLU model CI: **macro-F1 intent 0,9117; entity exact-span F1 0,9596**. Khác lần train local vì fresh training không bảo đảm trọng số đồng nhất; cả hai vượt gate. Không thay tập test hoặc hạ ngưỡng để làm CI xanh.
- Artifact [model + manifest/checksum](https://github.com/TrinhQuocDat542005/chatbot-tuyensinh/actions/runs/38050433408/artifacts/11669652254) và [báo cáo](https://github.com/TrinhQuocDat542005/chatbot-tuyensinh/actions/runs/38050433408/artifacts/11669067882) đã xuất theo đúng commit. Model bundle khoảng 34 MB, lưu 30 ngày.

**Kết luận:** các tiêu chí tuần 6 đã đạt trên local và runner GitHub sạch. Không thay kết quả tuần 4 bằng số đo từ model train lại.

[Báo cáo thực đo và provenance](evaluation/week6-summary.json).

## Giới hạn

Lock chưa có hash wheel, base Python vẫn dùng tag OS; không hứa tái lập bit-for-bit. Fresh train có thể cho chỉ số khác tuần 4. Tập NLU đã được review nên là hồi quy, chưa xác nhận trên câu người dùng mới. Chưa bật branch protection hoặc public deployment. Artifact CI có hạn lưu; release lâu dài và license thuộc tuần 8.
