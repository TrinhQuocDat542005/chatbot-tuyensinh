# Tuần 4: hội thoại nhiều lượt và đánh giá NLU

Ngày triển khai: 10/10/2026. Phạm vi theo tuần 4 của [roadmap](ROADMAP.md); một phần nghiệp vụ tuần 3 đã được tách trong tuần 1–2. Dữ liệu chưa có nguồn vẫn giữ các giới hạn trong [báo cáo tuần 1–2](week1-2-status.md).

**Đã triển khai luồng hội thoại và hoàn tất đo v0.5.** Logic, macro-F1 intent và F1 entity đạt mục tiêu trên bộ câu tự soạn hiện tại. Tập test đã được review lỗi; cần câu người dùng mới để xác nhận khả năng khái quát trước khi phát hành rộng rãi.

## Luồng hội thoại

- Form tra cứu thu thập ngành; với điểm chuẩn/tổ hợp yêu cầu thêm năm. Phương thức được đọc khi người dùng chỉ định; nếu không chỉ định, câu trả lời liệt kê rõ phương thức từng bản ghi có nguồn.
- Form tư vấn điểm yêu cầu tổng điểm THPT 0–30, chấp nhận dấu phẩy và số 0; điểm sai được hỏi lại.
- `lookup_intent` giữ mục đích tra cứu, `ten_nganh` giữ ngành hiện tại, `nam` giữ năm người dùng đã chọn và `phuong_thuc` giữ phương thức.
- “ngành đó” dùng ngành trong phiên; “còn năm 2023?” thay năm, không tự quay về năm có dữ liệu. Đổi ngành xóa năm/phương thức cũ nếu không chỉ định giá trị mới.
- Ngành/năm/phương thức thay thế không hợp lệ không được âm thầm dùng lại giá trị cũ.
- Tên người dùng tùy chọn. `bat_dau_lai` dùng `action_restart` xóa phiên; `huy_tra_cuu` thoát form và xóa slot. Các phiên mới không kế thừa slot.
- Fallback trong form giải thích và hỏi lại; có thể hủy/bắt đầu lại khi form đang hoạt động.

Form tùy biến dùng `FormValidationAction` và danh sách slot động theo [tài liệu Rasa](https://legacy-docs-oss.rasa.com/docs/rasa/3.x/forms/). Các intent ngắt form cần trả rejection cho form để Core xử lý nhánh tương ứng.

## Bộ kiểm tra

- 117 test Python: parser, dữ liệu, action, form, chuyển ngữ cảnh, bộ lọc entity, calibration và kiểm tra không trùng câu train/dev/test; toàn bộ pass trên Docker Linux.
- 22 kịch bản REST/Core/SDK thực trong `tests/conversations/scenarios.json`: thiếu ngành/năm, đổi ngành/năm/phương thức, thông tin sai, reset/hủy khi form hoạt động, điểm 0/ngoài thang/sửa điểm, fallback, không bắt buộc tên và tách phiên.
- Kịch bản REST nhiều lượt dùng intent/entity tường minh để kiểm tra logic hội thoại. Chúng không chứng minh NLU nhận đúng câu tự nhiên. `smoke_rest.py` dùng câu tự nhiên; đánh giá NLU dưới đây đo riêng.
- 4 luồng nhiều lượt bằng câu tự nhiên trong `tests/conversations/natural.json` pass: đổi năm/ngành, nhập và sửa điểm, hủy form, đổi phương thức. Thêm 4 smoke SDK và 4 câu hỏi REST đơn lẻ đều pass.
- Bộ lọc entity chạy trong pipeline thực: gộp extractor trùng, chỉ chấp nhận tên ngành exact/alias từ danh mục, loại span ngành cha giao nhau, ràng buộc điểm/môn theo intent và sửa span năm. Chỉ nhận tên môn thuộc danh sách hỗ trợ và span điểm thuần số; điểm ngoài thang vẫn được chuyển đến action để báo lỗi.

## Thiết kế đánh giá

`tests/evaluation/nlu.yml` có **154 câu**, gồm **54 câu khó hoặc ngoài phạm vi**. Có 20 intent nghiệp vụ/hội thoại và 14 câu ngoài phạm vi mong đợi fallback. Tập development `dev.yml` gồm 44 câu riêng dùng để hiệu chỉnh threshold. Cả hai nằm ngoài thư mục `data/`, nên lệnh train thông thường không nạp chúng.

Các câu do người phát triển soạn, chưa phải dữ liệu người dùng độc lập. Có kiểm tra không trùng câu train/dev/test sau khi bỏ annotation và chuyển chữ thường. Cách diễn đạt/nhóm chủ đề mới được soạn riêng; điều này không chứng minh hoàn toàn loại bỏ tương đồng ngữ nghĩa giữa các tập.

Lần cải thiện tiếp theo bổ sung 266 câu train trong `data/intent_coverage.yml`, ưu tiên nhóm thiếu dữ liệu: chương trình đào tạo, địa điểm, danh sách ngành, phương thức, chào hỏi và câu không dấu. Không chuyển câu dev/test sang train, không thay ground truth. Vì lỗi của tập test đã được review, lần đo tiếp theo là kiểm tra hồi quy trên tập cố định, **không phải đánh giá mù**. Cần bộ câu người dùng mới để xác nhận khả năng khái quát.

Intent được chấm theo từng nhãn, có confusion matrix. Entity được chấm exact span + loại entity, gộp duplicate extractor; có thống kê theo từng loại, false positive và false negative. Không chấm giá trị sau synonym như một span mới. Báo cáo JSON giữ mọi câu sai và ranking để review.

Baseline dùng model tuần 1–2 trên cùng 154 câu. Model này chưa có ba intent mới `bat_dau_lai`, `bo_sung_tra_cuu`, `huy_tra_cuu`; mức tăng phản ánh cả mở rộng phạm vi và thay đổi model, không chỉ cải thiện classifier. Ground truth đã bổ sung 3 annotation tên môn bị thiếu trước khi khóa kết quả baseline cuối cùng; không thay đổi câu hoặc nhãn intent. Ngưỡng fallback chỉ chọn từ dev, không điều chỉnh tập test để đạt mục tiêu.

## Kết quả

| Model | Tập | Macro-F1 intent | F1 entity exact span |
| --- | --- | --- | --- |
| Tuần 1–2 | Test 154 câu | 0,4333 | 0,6465 |
| Tuần 4 lần đầu, threshold 0,5 | Test 154 câu | 0,7251 | 0,9700 |
| Tuần 4 lần đầu, threshold 0,5 | Dev 44 câu | 0,8363 | 0,9474 |
| Tuần 4 sau bổ sung 266 câu, threshold 0,5 | Test 154 câu | **0,9247** | **0,9490** |
| Tuần 4 sau bổ sung 266 câu, threshold 0,5 | Dev 44 câu | 0,9788 | 1,0000 |

Entity test cuối: TP 93, FP 0, FN 10; precision 1,0000 và recall 0,9029. Từng loại: `diem`, `nam` F1 1,0000; `d`, `mon_hoc` 0,9268; `ten_nganh` 0,9630; `ten_nguoi_dung` 0,8333. F1 entity giảm từ 0,9700 xuống 0,9490, vẫn vượt mục tiêu 0,85. Một câu điểm từng môn bị nhận sai intent khiến bộ lọc loại entity; một số tên người dùng/ngành chưa được trích xuất. Không thể coi việc tăng intent là cải thiện mọi chỉ số. Kết quả chỉ áp dụng tập câu đã soạn, không phải chất lượng trên tất cả câu người dùng.

Mục tiêu F1 entity >=0,85 và macro-F1 intent >=0,90 đều đạt trên tập hiện tại. Nhãn yếu nhất còn là `nlu_fallback` (F1 0,6452); một số câu hỏi trường khác hoặc nội dung ngoài phạm vi vẫn bị nhận thành intent tuyển sinh. Tra cứu điểm chuẩn và bổ sung ngữ cảnh đạt F1 0,8000. Cần thu thập câu người dùng thực, tăng khả năng phân biệt ngoài phạm vi và đo thêm trên tập mới chưa xem lỗi. Không sửa tập test hiện tại hoặc chuyển các câu sai đó sang train để báo chỉ số cao hơn trên cùng tập.

Core cuối: **10/10 hội thoại, 26/26 dự đoán action đúng**, không có cảnh báo hội thoại. REST nhiều lượt: **22/22 kịch bản** và **4/4 luồng câu tự nhiên** pass.

Trong lần đo đầu, thử nghiệm cấu hình đầy đủ và rút gọn giữ nguyên DIET/NLU đã train, bỏ ResponseSelector, UnexpecTEDIntentPolicy và AugmentedMemoizationPolicy. Tại threshold 0,7, cả hai có **cùng từng dự đoán dev**, macro-F1 0,7198, entity F1 0,9474 và Core 10/10. Vì bỏ các thành phần này không làm hồi quy trên bộ kiểm tra, cấu hình rút gọn được chọn mặc định. Đây là kiểm tra trên bộ dữ liệu hiện tại, không chứng minh tương đương ở mọi tình huống. Cấu hình đối chiếu lưu trong `configs/`. Model bổ sung 266 câu được train mới với cấu hình rút gọn.

Calibration lần đầu thử các threshold 0,4–0,9 trên 44 câu dev; 0,4 và 0,5 cùng macro-F1 0,8363, chọn 0,5 vì gần ngưỡng cũ hơn. Runtime lúc đó xác nhận macro-F1 0,8363 khớp calibration. Giữ threshold 0,5 và ambiguity threshold 0,1 khi mở rộng train; không chỉnh ngưỡng sau khi đo test mới. Dev của model mới đạt macro-F1 0,9788. Logic calibration chỉ bỏ phần tử fallback do ngưỡng thêm vào; nhãn `nlu_fallback` học từ DIET được giữ. Kết quả test không được dùng để chọn threshold.

Tóm tắt có hash dataset/model, confusion matrix thưa, chỉ số từng intent/entity và các câu thất bại lưu tại [evaluation/week4-summary.json](evaluation/week4-summary.json). Dependency Rasa vẫn có cảnh báo deprecation và overlap extractor; bộ lọc entity xử lý trùng trong runtime. Train lại từ đầu có thể cho chỉ số/hash khác; các model đối chiếu dùng lại cùng trọng số DIET trong cache để cô lập thay đổi policy/threshold.

## Tái lập

```bash
docker compose build train
docker compose run --rm train
docker compose run --rm check
docker compose run --rm check python scripts/evaluate_nlu.py --model models/admissions-week4.tar.gz --data tests/evaluation/dev.yml --out results/nlu/dev-final.json
docker compose run --rm check python scripts/calibrate_fallback.py results/nlu/dev-final.json
docker compose run --rm check python scripts/evaluate_nlu.py --model models/admissions-week4.tar.gz --out results/nlu/final.json
docker compose up -d --wait actions rasa
docker compose exec rasa python scripts/check_conversations.py
docker compose exec rasa python scripts/check_conversations.py --cases tests/conversations/natural.json --out results/conversations/natural-report.json
docker compose exec rasa python scripts/smoke_rest.py
```

Model và báo cáo chi tiết trong `models/`, `results/` bị ignore. Tóm tắt kết quả, hash dataset/model và ví dụ sai được lưu cùng tài liệu nghiệm thu. Có thể tạo lại tóm tắt bằng `python scripts/summarize_evaluation.py --date YYYY-MM-DD` sau khi tạo đủ báo cáo; script từ chối nếu dataset đã thay đổi so với lúc đánh giá. Baseline trong tóm tắt mới là `null` nếu không có report baseline local; số liệu lịch sử vẫn được giữ tại [evaluation/week4-initial-summary.json](evaluation/week4-initial-summary.json). Mã nguồn được chuẩn hóa xuống dòng LF trước lần đo cuối để hash dataset khớp file trong Git; không thay đổi câu hoặc annotation.
