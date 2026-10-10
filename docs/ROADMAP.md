# Lộ trình nâng cấp chatbot tuyển sinh

Ngày đánh giá: 10/10/2026. Phạm vi: mã nguồn, cấu hình Rasa, dữ liệu JSON, dữ liệu huấn luyện, kịch bản test và cấu trúc Git đang có trong repository.

Tiến độ triển khai sau đánh giá: xem [nghiệm thu tuần 1–2](week1-2-status.md), [kết quả tuần 4](week4-status.md), [demo web tuần 5](week5-status.md) và [Docker/CI tuần 6](week6-status.md). Tuần 4 đạt mục tiêu trên tập câu tự soạn đã review, cần xác nhận thêm bằng câu người dùng mới. Tuần 5 có demo local và 5 tác vụ qua UI đã pass với model thật. Tuần 6 có runtime SDK riêng, model truy vết bằng commit/input/checksum; CI và model regression đã success trên checkout GitHub sạch. Các phát hiện hiện trạng dưới đây mô tả phiên bản trước khi sửa.

Đây là kế hoạch triển khai, không phải báo cáo hệ thống đã chạy đạt các chỉ số bên dưới. Phiên đánh giá này chưa có môi trường Rasa khả dụng để train hoặc chạy kiểm thử hội thoại; các phát hiện dựa trên đọc file, đối chiếu dữ liệu và kiểm tra tĩnh. Chưa xác minh tính đúng đắn của thông tin tuyển sinh với trường.

## 1. Mục tiêu và phạm vi phiên bản 1.0

Xây dựng một chatbot tuyển sinh tiếng Việt có thể được người khác clone, chạy, kiểm tra và sử dụng qua giao diện web. Chất lượng cần thể hiện ở độ chính xác, nguồn dữ liệu, khả năng tái lập và trải nghiệm hội thoại.

Phiên bản 1.0 giới hạn ở một trường, một danh mục ngành được xác minh và các phương thức tuyển sinh đã có dữ liệu. Tính năng chính:

- Tra cứu ngành, giới thiệu, cơ hội nghề nghiệp, tổ hợp và điểm chuẩn theo năm/phương thức.
- Tra cứu học phí, địa điểm và thông tin tuyển sinh có nguồn, thời điểm cập nhật.
- Tham khảo ngành từ điểm và sở thích, giải thích căn cứ gợi ý.
- Hỏi bổ sung khi thiếu ngành, năm, phương thức, tổ hợp hoặc điểm.
- Giữ ngữ cảnh trong phiên; cho phép sửa thông tin và bắt đầu lại.
- Thừa nhận thiếu dữ liệu và chỉ dẫn đến nguồn chính thức.

Điểm chuẩn lịch sử chỉ phục vụ tham khảo. Bot không chuyển việc vượt điểm chuẩn năm trước thành kết luận chắc chắn trúng tuyển.

## 2. Hiện trạng và những vấn đề cụ thể

### Nền tảng có thể giữ lại

- Rasa 3.6.21, rasa-sdk 3.6.2; đã tách NLU, rules, stories và domain.
- 17 intent trong NLU nhưng chỉ 16 intent khai báo trong domain.
- 9 custom action, khoảng 499 dòng trong `actions/actions.py`.
- Khoảng 351 dòng ví dụ NLU; vẫn cần loại ví dụ trùng và đánh giá chất lượng.
- JSON có 26 bản ghi ngành và các trường giới thiệu, nghề nghiệp, tổ hợp, điểm chuẩn.
- Có REST channel và action endpoint để nối giao diện.

### Danh sách ưu tiên

| Mức | Phát hiện | Ảnh hưởng | Hành động |
| --- | --- | --- | --- |
| P0 | `cung_cap_diem` có trong NLU/rules nhưng thiếu trong `domain.yml` | Cấu hình hội thoại không đồng bộ | Bổ sung và chạy validation/train |
| P0 | Có 3 annotation `ten_ngành` thay vì `ten_nganh` | Entity có thể không đi vào slot mong muốn | Sửa nhãn, rà toàn bộ annotation |
| P0 | Regex trong action tính tổ hợp bắt tên môn `hóa và` ở câu “8 điểm Toán, 8 điểm Hóa và 9 điểm Anh” | Môn Hóa không được nhận diện đúng | Chuẩn hóa môn và tách liên từ trước khi tính |
| P0 | Môn còn thiếu được cộng với giá trị 0; chỉ lấy 3 cặp đầu rồi chọn một tổ hợp cao nhất | Có thể gợi ý từ tổ hợp chưa đủ môn; bỏ lỡ tổ hợp hợp lệ khác | Chỉ tính tổ hợp đủ môn, xét tất cả tổ hợp phù hợp |
| P0 | Parser tổng điểm lấy số đầu tiên, không kiểm tra khoảng điểm, không hỗ trợ dấu phẩy thập phân | Có thể nhầm năm với điểm hoặc nhận điểm không hợp lệ | Parser có validation theo phương thức và thang điểm |
| P0 | Cả hai action tư vấn điểm cố định năm `2024` | Không tự theo dữ liệu mới; dễ hiểu nhầm dữ liệu lịch sử | Chọn năm người dùng yêu cầu; nếu không có thì công bố năm dữ liệu thực dùng |
| P0 | Gợi ý sở thích dùng danh sách tên viết trong code, gồm tên chưa có trong JSON | Gợi ý ngành rồi không tra cứu được thông tin | Gợi ý bằng ID thuộc danh mục đã xác minh |
| P0 | JSON và câu trả lời tĩnh chưa có nguồn, năm áp dụng/phương thức đủ rõ | Không chứng minh được thông tin tuyển sinh | Bổ sung metadata và kiểm chứng từng nội dung |
| P1 | `tests/test_stories.yml` vẫn là test mẫu `greet`, `mood_great`, `utter_happy` | Không kiểm tra chức năng tuyển sinh hiện có | Thay bằng kịch bản tiếng Việt thực tế |
| P1 | Có `FallbackClassifier` nhưng chưa có rule xử lý `nlu_fallback` | Chưa mô tả rõ hành vi khi NLU thiếu tự tin | Thêm rule, gợi ý câu hỏi và kiểm thử |
| P1 | Fuzzy matching chọn một kết quả với threshold 70 | Ngành gần tên có thể bị tự chọn nhầm | Exact/alias trước; trường hợp mơ hồ hỏi xác nhận |
| P1 | Đọc JSON lặp trong nhiều action; bắt `Exception` rộng; một action trả lỗi kỹ thuật trực tiếp | Khó bảo trì, chẩn đoán và kiểm soát lỗi | Repository dữ liệu dùng chung, schema, logging và thông báo lỗi ổn định |
| P1 | Ngưỡng điểm, mapping sở thích và logic gợi ý nằm trong action | Khó kiểm thử nghiệp vụ riêng | Tách service thuần Python và cấu hình dữ liệu |
| P1 | `.gitignore` chứa 8 byte NUL; có đoạn `!models/*.tar.gz.rasa/` đáng ngờ | Quy tắc ignore khó tin cậy | Viết lại UTF-8, xác minh bằng `git check-ignore` |
| P1 | `start.sh` và `star.sh` gần trùng nhau, dùng `$PORT` không có default, không khởi động action server | Hướng dẫn triển khai chưa đầy đủ | Hợp nhất script và dùng Docker Compose |
| P1 | Script mở `--enable-api` và `--cors "*"` | Cần kiểm soát bề mặt API trước demo công khai | Reverse proxy, CORS giới hạn, API quản trị được bảo vệ |
| P1 | README chỉ có hai tiêu đề trùng; chưa có CI, license, tài liệu vận hành hay frontend | Người ngoài khó chạy, đánh giá và đóng góp | Hoàn thiện bộ tài liệu, demo và kiểm thử tự động |
| P2 | Có 8 model cục bộ tổng khoảng 226,4 MiB, `.gitattributes` khai báo LFS | Tăng chi phí lưu trữ và tải model | Phân phối model qua Release/artifact; kiểm tra LFS thực tế trước thay đổi |

Các điểm cần kiểm chứng dữ liệu:

- Điểm chuẩn có năm 2020–2024; số bản ghi có điểm lần lượt là 21, 21, 22, 24, 26. Không suy diễn `null` thành 0 và không gọi dữ liệu năm 2024 là dữ liệu hiện hành năm 2026.
- NLU chứa nhiều tên chuyên ngành trong khi JSON thường lưu tên ngành rộng hơn. Cần mô hình hóa ngành/chuyên ngành và alias, thay vì chỉ tăng fuzzy threshold.
- Bản ghi Công nghệ kỹ thuật cơ khí có danh sách nghề nghiệp tập trung nhiều vào cảng/logistics. Đây là dấu hiệu cần rà soát nguồn, chưa đủ căn cứ kết luận toàn bộ nội dung sai.
- Có hai bản ghi tên gần như “Kinh tế xây dựng” với mã khác nhau; cần xác minh mã/tên chính thức trước khi gộp.
- `regex.yml` nằm ngoài thư mục `data/`, khai báo version 2.0 và regex trong chuỗi dấu nháy kép. Cần kiểm tra cú pháp YAML và cách đưa file vào quá trình train; không mặc định file đang có tác dụng.
- Logic sắp xếp tư vấn điểm dùng điểm chuẩn tăng dần trong khi comment nói ưu tiên điểm cao hơn. Cần định nghĩa tiêu chí xếp hạng trước khi sửa.

## 3. Ba phương án nâng cấp

| Phương án | Phạm vi | Ưu điểm | Chi phí/rủi ro | Thời lượng dự kiến |
| --- | --- | --- | --- | --- |
| A. Hoàn thiện Rasa hiện có | Sửa lỗi, chuẩn hóa dữ liệu, hội thoại nhiều lượt, frontend, Docker, CI, tài liệu | Tận dụng công việc cũ; dễ chứng minh cải tiến bằng test | Cần phát triển dữ liệu NLU; giới hạn ở phạm vi đã huấn luyện | 6–8 tuần |
| B. Rasa kết hợp truy xuất tài liệu và LLM | Toàn bộ A; thêm trả lời FAQ mở từ tài liệu chính thức, trích dẫn nguồn | Phủ câu hỏi linh hoạt hơn; có điểm nhấn về AI | Thêm chi phí suy luận, đánh giá truy xuất, kiểm soát câu trả lời và vận hành | Thêm 3–4 tuần sau A |
| C. Viết lại backend theo hướng LLM | Backend API mới, công cụ tra cứu dữ liệu, truy xuất tài liệu, quản lý phiên | Linh hoạt hơn cho hướng phát triển dài hạn khác | Phải làm lại điều phối, kiểm thử và demo; không giải quyết tự động vấn đề dữ liệu | 10–14 tuần, cần ước lượng lại |

**Khuyến nghị: hoàn thành A, phát hành v1.0, sau đó cân nhắc B cho v1.1.** Chưa có bằng chứng cần viết lại toàn bộ. Với GitHub/portfolio, demo chạy được và có báo cáo đánh giá sẽ thuyết phục hơn việc thêm nhiều công nghệ chưa được kiểm chứng.

Ước lượng dành cho một người làm khoảng 12–15 giờ/tuần. Công tác tìm và xác minh dữ liệu có thể kéo dài thời gian. Các phương án và mốc thời gian là đề xuất, không phải cam kết đã đo.

## 4. Kiến trúc đề xuất

```text
Web chat (React + TypeScript + Vite)
                  |
           HTTPS / reverse proxy
                  |
             Rasa REST channel
                  |
             Action server
                  |
      Services nghiệp vụ độc lập
        |         |           |
   Tra cứu ngành  Tính điểm   Gợi ý ngành
                  |
       Repository + schema validation
                  |
        Dữ liệu có phiên bản và nguồn
```

Frontend trên là một lựa chọn mặc định để xây demo, có thể dùng giao diện HTML/JS đơn giản nếu muốn giảm phạm vi. Không cần thêm một backend API thứ hai chỉ để chuyển tiếp request mà reverse proxy đã xử lý được.

- Giai đoạn đầu giữ JSON có schema để dễ review trên GitHub. SQLite chỉ thêm khi thực sự cần tìm kiếm/cập nhật phức tạp; PostgreSQL phù hợp khi có nhiều người quản trị và ghi đồng thời.
- Chỉ thêm Redis/tracker store khi cần giữ phiên qua lần khởi động hoặc triển khai nhiều instance. Với demo đơn instance, mô tả rõ giới hạn của lưu phiên trong bộ nhớ.
- Phiên bản 1.1 có thể thêm service truy xuất/LLM riêng. Các phép tính và số liệu tuyển sinh vẫn đi qua service dữ liệu đã kiểm tra.
- Giữ môi trường tái lập của Rasa 3.6 trước; đánh giá đường nâng cấp framework riêng, không thay version hàng loạt trong lúc sửa nghiệp vụ.

Rasa 3.6.21 yêu cầu Python >=3.8 và <3.11 theo [metadata của gói](https://pypi.org/project/rasa/3.6.21/). Có thể dùng Python 3.10 trong môi trường tái lập ban đầu, kiểm tra đầy đủ dependency rồi đóng gói container. Đây không phải đề xuất duy trì stack cũ vô thời hạn; cần lập issue riêng cho vòng đời runtime, dependency và hướng chuyển đổi.

### Cấu trúc thư mục đích

```text
actions/
  actions.py                 # Adapter Rasa mỏng
  services/                  # Tra cứu, điểm, gợi ý
  repositories/              # Đọc và cache dữ liệu
  schemas/                   # Validation dữ liệu
  data/                      # Danh mục, aliases, tổ hợp, tuyển sinh
data/                        # NLU, stories, rules, lookup
tests/
  unit/                      # Service, parser, matcher
  integration/               # Action, webhook, dữ liệu
  conversations/             # Test nhiều lượt
  evaluation/                # Tập đánh giá NLU tách biệt
frontend/
docs/
  ROADMAP.md
  architecture.md
  data-sources.md
  evaluation.md
  deployment.md
scripts/
.github/workflows/
compose.yaml
Dockerfile
Dockerfile.actions
.env.example
README.md
LICENSE
CONTRIBUTING.md
SECURITY.md
CHANGELOG.md
```

Tách kiểm thử không phụ thuộc Rasa để chạy nhanh; chỉ integration/training dùng dependency đầy đủ.

### Mô hình dữ liệu cần bổ sung

- Danh mục: ID nội bộ ổn định, mã chính thức, tên, alias, ID ngành cha nếu là chuyên ngành, trạng thái còn tuyển sinh.
- Thông tin tuyển sinh: ID chương trình, năm, phương thức, tổ hợp, thang điểm, điểm chuẩn và quy tắc ưu tiên nếu có.
- Nguồn: URL tài liệu chính thức, ngày công bố, ngày kiểm tra, người xác minh/trạng thái xác minh.
- Học phí: chương trình, năm áp dụng, số tiền, đơn vị như tín chỉ hoặc học kỳ, điều kiện áp dụng.
- Sở thích: tag/mapping đến ID đã có trong danh mục, có thể review và thay đổi mà không sửa Python.

Không đánh đồng THPT, học bạ và đánh giá năng lực bằng cùng một tổng điểm. Trường hợp chưa mô hình hóa được phương thức phải trả lời rõ phạm vi hỗ trợ.

## 5. Lộ trình 8 tuần với đầu ra và tiêu chí nghiệm thu

### Tuần 1 — Làm project chạy lại được và khóa lỗi nghiêm trọng

**Việc làm:**

1. Tạo môi trường phù hợp Rasa 3.6.21; kiểm tra cài dependency sạch, `pip check`, train và khởi động hai server.
2. Sửa intent thiếu, ba nhãn entity sai, rà YAML/regex và thêm rule `nlu_fallback`.
3. Thay test mẫu bằng 5–10 hội thoại tuyển sinh tối thiểu.
4. Viết test tái hiện lỗi parser môn, tổng điểm, thiếu môn và số ngoài thang điểm; sửa các lỗi này trước.
5. Sửa encoding `.gitignore`, hợp nhất script, có default port và README chạy local ngắn.

**Đầu ra:** bản v0.1 chạy local; danh sách lỗi còn lại có mức ưu tiên.

**Nghiệm thu:** cài được từ môi trường sạch; `rasa data validate` và train thành công; REST gọi được custom action; các test lỗi nghiêm trọng đã sửa đều pass. Không coi validation thay thế cho train/test hội thoại.

### Tuần 2 — Chuẩn hóa và kiểm chứng dữ liệu

**Việc làm:**

1. Rà 26 bản ghi với nguồn chính thức; lập bảng phần đã/chưa xác minh.
2. Phân biệt ngành, chương trình và chuyên ngành; giải quyết tên/mã không rõ.
3. Thêm alias, metadata năm/phương thức/nguồn và schema validation.
4. Chuyển thông tin biến động như học phí, địa chỉ, phương thức ra khỏi response viết cố định.
5. Chọn năm dữ liệu một cách tường minh; xử lý `null`, năm chưa có và ngày cập nhật.

**Đầu ra:** bộ dữ liệu có phiên bản và `docs/data-sources.md`.

**Nghiệm thu:** 100% bản ghi được dùng để trả lời đã qua schema; mỗi số liệu được trình bày như thông tin xác nhận có nguồn truy vết; bản ghi chưa xác minh bị loại khỏi trả lời xác quyết. Bot không bịa điểm cho năm không có.

### Tuần 3 — Tách nghiệp vụ và sửa cách tư vấn

**Việc làm:**

1. Tách loader/repository, parser, matcher và recommendation service khỏi action.
2. Match exact/alias trước; fuzzy trả danh sách ứng viên khi mơ hồ.
3. Chuẩn hóa dấu tiếng Việt, viết tắt tên môn, điểm `8,5` và `8.5`; phát hiện môn lặp/điểm mâu thuẫn.
4. Chỉ tính tổ hợp đủ môn; với 4–6 môn phải xét tất cả tổ hợp hợp lệ.
5. Gợi ý theo phương thức, năm tham khảo, tổ hợp và sở thích; quy tắc xếp hạng có giải thích.
6. Chỉ trả ngành thuộc danh mục; bỏ cách kết luận “đủ điểm” như lời bảo đảm trúng tuyển.

**Đầu ra:** service nghiệp vụ có unit test; action chủ yếu đọc slot và gửi kết quả.

**Nghiệm thu:** câu “8 điểm Toán, 8 điểm Hóa và 9 điểm Anh” cho D07 = 25 khi dữ liệu tổ hợp hỗ trợ; thiếu môn thì hỏi bổ sung; điểm sai bị từ chối; gợi ý không chứa ID ngoài danh mục. Hai cách nhập dấu phẩy/dấu chấm cho cùng kết quả.

### Tuần 4 — Hội thoại nhiều lượt và đánh giá NLU

**Việc làm:**

1. Thêm forms/slot validation để thu thập trường thiếu.
2. Hỗ trợ “ngành đó”, “còn năm 2023?”, thay đổi ngành, thay đổi điểm và bắt đầu lại.
3. Không bắt buộc cho tên trước khi tra cứu; quyết định rõ slot nào giữ qua phiên mới.
4. Làm sạch ví dụ trùng; bổ sung câu không dấu, sai chính tả, ngoài phạm vi và câu gần giống giữa các intent.
5. Tạo tối thiểu 150 câu đánh giá độc lập, có ít nhất 30 câu khó/ngoài phạm vi; tách theo nhóm diễn đạt để hạn chế rò rỉ từ train.
6. Đo baseline, xem confusion matrix, chọn threshold fallback theo dữ liệu; thử bỏ component/policy dư và so sánh trước khi chốt.

**Đầu ra:** hội thoại nhiều lượt và báo cáo đánh giá v0.5.

**Nghiệm thu:** tối thiểu 20 hội thoại quan trọng pass; không dùng ngành/năm cũ khi người dùng đã thay đổi; báo cáo có chỉ số theo từng intent/entity và ví dụ thất bại. Mục tiêu ban đầu: macro-F1 intent >=0,90 và F1 entity >=0,85 trên tập độc lập; phải ghi kết quả thực đo, không điều chỉnh tập test để đạt mục tiêu.

### Tuần 5 — Giao diện web có thể trình diễn

**Việc làm:**

1. Xây chat responsive trên điện thoại/máy tính, có nút câu hỏi mẫu và lựa chọn ngành.
2. Hiển thị câu trả lời theo card, bảng điểm, năm/phương thức tham khảo và liên kết nguồn.
3. Thêm trạng thái chờ, lỗi kết nối, thử lại và bắt đầu phiên mới.
4. Hiển thị nội dung dài có cấu trúc; Markdown/link được xử lý an toàn.
5. Dùng session ID riêng mỗi người; không đưa tên/điểm vào URL; cho phản hồi hữu ích/không hữu ích.
6. Kiểm tra bàn phím, độ tương phản, chữ tiếng Việt và màn hình nhỏ.

**Đầu ra:** demo local hoàn chỉnh, ảnh chụp/GIF và video ngắn.

**Nghiệm thu:** người mới thực hiện được 5 tác vụ chính qua giao diện; lỗi backend không làm mất lịch sử đang hiển thị; các phiên không trộn ngữ cảnh; nguồn/năm hiện rõ ở câu trả lời có số liệu.

### Tuần 6 — Docker, CI và khả năng tái lập

**Việc làm:**

1. Đóng gói Rasa và action server riêng, nối bằng Compose; sửa action endpoint sang hostname service trong container.
2. Chọn rõ cách train model hoặc tải model phát hành có checksum.
3. Thêm healthcheck, biến môi trường, `.env.example`, log chuẩn và hướng dẫn Windows/WSL/Docker.
4. CI mỗi PR: lint, validation YAML/JSON, unit test, kiểm tra cấu hình.
5. CI cho thay đổi dữ liệu NLU/cấu hình: train và conversation/NLU test; dùng lịch hoặc manual cho đánh giá nặng.
6. Xuất báo cáo đánh giá và model vào artifact; cache dependency phù hợp, không để cache che lỗi cài sạch.

**Đầu ra:** `compose.yaml`, Dockerfile, workflow và hướng dẫn tái lập.

**Nghiệm thu:** clone sạch rồi chạy theo README thành công; CI phát hiện một dữ liệu lỗi có chủ đích; bản model liên kết được với commit, dataset và config dùng train.

### Tuần 7 — Demo công khai và vận hành tối thiểu

**Việc làm:**

1. Chọn máy chủ/container hosting sau khi đo RAM, CPU, thời gian khởi động và chi phí thực tế.
2. Cấu hình HTTPS, reverse proxy, CORS đúng origin và giới hạn request/message size.
3. Không để action server/API quản trị truy cập tự do từ Internet.
4. Có timeout, thông báo lỗi dễ hiểu, theo dõi health và tỷ lệ fallback.
5. Dùng dữ liệu phiên tối thiểu; tránh ghi nguyên tên/điểm vào log; mô tả thời hạn lưu nếu lưu hội thoại.
6. Chạy smoke test, thử hai phiên song song, thử restart và rollback theo phiên bản.

**Đầu ra:** URL demo, runbook và số liệu hiệu năng trên cấu hình được ghi rõ.

**Nghiệm thu:** 5 hành trình chính chạy qua URL demo; không lẫn phiên; khôi phục được bản trước; không lộ chi tiết exception. Mục tiêu p95 dưới 2 giây cho câu tra cứu thông thường, đo ít nhất 100 request sau warm-up ở 5 phiên đồng thời; ghi cả tỷ lệ lỗi và cold start.

### Tuần 8 — Hoàn thiện GitHub và phát hành v1.0

**Việc làm:**

1. README: giới thiệu, ảnh/GIF, demo, tính năng, giới hạn, kiến trúc, quickstart, test và kết quả đánh giá.
2. Bổ sung license phù hợp quyền sở hữu code; ghi riêng quyền sử dụng/nguồn của dữ liệu.
3. Thêm CONTRIBUTING, SECURITY, issue/PR templates, changelog và roadmap rút gọn.
4. Rà bí mật và dữ liệu cá nhân trong file được track; lịch sử Git cần kiểm tra riêng trước khi public.
5. Chốt cách lưu model: một model phát hành chuẩn, checksum và hướng dẫn tải; không rewrite lịch sử chỉ để dọn model nếu chưa có kế hoạch phối hợp.
6. Thử lại hướng dẫn trên clone sạch; chạy bộ nghiệm thu; tạo tag/release v1.0.0 kèm model và báo cáo.

**Đầu ra:** repository có thể review, demo hoạt động và release tái lập.

**Nghiệm thu:** một người chưa biết dự án chạy được theo README; mọi tính năng quảng bá có demo/test chứng minh; chỉ số được công bố kèm tập dữ liệu, phương pháp đo và giới hạn.

## 6. Backlog nên tạo thành GitHub Issues

| Thứ tự | Issue | Ưu tiên | Phụ thuộc |
| --- | --- | --- | --- |
| 1 | Tái lập môi trường Rasa và kiểm tra dependency | P0 | Không |
| 2 | Đồng bộ intent/entity/domain và xử lý NLU fallback | P0 | 1 |
| 3 | Sửa parser điểm/môn và tính tổ hợp hợp lệ | P0 | 1 |
| 4 | Chuẩn hóa danh mục ngành/chuyên ngành và nguồn | P0 | Không |
| 5 | Schema tuyển sinh theo năm/phương thức và kiểm chứng dữ liệu | P0 | 4 |
| 6 | Tách repository/service khỏi custom actions | P1 | 3, 5 |
| 7 | Gợi ý ngành hợp lệ và giải thích căn cứ | P1 | 6 |
| 8 | Forms, sửa slot, hội thoại nhiều lượt và reset phiên | P1 | 2, 6 |
| 9 | Tập test độc lập, test hội thoại và báo cáo NLU | P1 | 2; đánh giá lại sau 8 |
| 10 | Web chat responsive và hiển thị nguồn | P1 | 5, 8 |
| 11 | Docker Compose và GitHub Actions | P1 | 1, 9 |
| 12 | Demo HTTPS, giới hạn API và kiểm tra vận hành | P1 | 10, 11 |
| 13 | README, license, hướng dẫn đóng góp và release model | P1 | 9, 12 |
| 14 | Đánh giá vòng đời dependency/runtime và hướng nâng cấp | P1 | 1; chốt trước public demo |
| 15 | Thử nghiệm truy xuất tài liệu có trích dẫn cho v1.1 | P2 | v1.0 đã ổn định |

Mỗi issue nên có ví dụ đầu vào, đầu ra mong đợi, tiêu chí nghiệm thu và liên kết test. Chỉ đóng khi đáp ứng tiêu chí, không chỉ vì đã viết code.

## 7. Phạm vi v1.1: bổ sung AI có kiểm soát

Sau v1.0, dành thêm 3–4 tuần nếu nhu cầu câu hỏi mở đủ rõ:

1. Chọn một tập tài liệu chính thức, theo dõi phiên bản/ngày, chia đoạn và lưu nguồn.
2. Làm baseline truy xuất; đánh giá câu hỏi có tài liệu trả lời và câu hỏi không có tài liệu.
3. Cho LLM diễn giải đoạn tìm được, trích dẫn đúng nguồn; không tự suy ra số liệu thiếu.
4. Đưa phép tính, tra cứu điểm/học phí qua service cấu trúc; giới hạn công cụ được phép gọi.
5. Kiểm thử prompt injection trong tài liệu/câu hỏi, timeout, mất kết nối và giới hạn chi phí.
6. So sánh với v1.0 trên cùng tập câu hỏi: độ đúng, nguồn, độ trễ và chi phí; chỉ phát hành nếu có lợi ích đo được.

Không cần thêm ngay đa trường, đăng nhập người dùng, dashboard quản trị lớn, microservices, Kubernetes, voice hay ứng dụng mobile. Chúng làm tăng phạm vi trước khi vấn đề cốt lõi được giải quyết.

## 8. Điều kiện gọi là hoàn thành

- [ ] Cài/chạy được từ clone sạch và môi trường đã công bố.
- [ ] Các lỗi P0 đã đóng với bằng chứng kiểm thử.
- [ ] Dữ liệu trả lời có nguồn, năm và phương thức thích hợp.
- [ ] Thiếu dữ liệu thì bot hỏi lại hoặc nói rõ chưa biết.
- [ ] Gợi ý chỉ dùng ngành thuộc danh mục được xác minh.
- [ ] Không bảo đảm trúng tuyển từ điểm chuẩn lịch sử.
- [ ] Có unit, integration, conversation test và tập NLU độc lập.
- [ ] Có báo cáo chỉ số thực đo, lỗi còn lại và giới hạn.
- [ ] Demo web dùng được trên điện thoại; có phân tách phiên.
- [ ] CI chạy và artifact/model truy vết được tới commit.
- [ ] API công khai được giới hạn; log không lộ dữ liệu không cần thiết.
- [ ] README, license, nguồn dữ liệu, đóng góp và release đầy đủ.

## 9. Tài liệu kỹ thuật đối chiếu

- [Rasa 3.6.21: metadata và yêu cầu Python](https://pypi.org/project/rasa/3.6.21/).
- [Rasa: testing your assistant](https://legacy-docs-oss.rasa.com/docs/rasa/testing-your-assistant/): validation không thay thế kiểm thử rule/story và hội thoại.
- [Rasa: fallback và handoff](https://legacy-docs-oss.rasa.com/docs/rasa/fallback-handoff/): cấu hình NLU fallback cần hành vi/rule tương ứng.
- [GitHub Actions: build và test Python](https://docs.github.com/en/actions/tutorials/build-and-test-code/python): cơ sở xây CI Python.
- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases): phát hành theo tag và đính kèm artifact/model.
