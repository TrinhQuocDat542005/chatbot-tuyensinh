# Tuần 5: demo web và README

Ngày nghiệm thu: 10/10/2026. Phạm vi theo [roadmap](ROADMAP.md): giao diện local và tài liệu trình diễn, dùng model tuần 4 đã nghiệm thu. Không train lại hoặc thay đổi NLU trong tuần này.

## Đã triển khai

- Giao diện HTML/CSS/JavaScript thuần, responsive, màu giấy sáng và xanh đậm, không tải font/script từ CDN. Sidebar chọn ngành/năm; bốn nhóm câu hỏi mẫu; input có Enter/Shift + Enter và hỗ trợ IME.
- Mỗi lần tải trang hoặc bắt đầu lại tạo UUID mới trong bộ nhớ. Các tab có sender riêng; reset không dùng lại ngữ cảnh cũ. Lịch sử không được ghi vào Web Storage.
- Thẻ trả lời có danh sách, Markdown giới hạn, liên kết nguồn HTTP(S), năm và phương thức từ nguyên văn backend. Chỉ các dòng tổng điểm tổ hợp `/30` được chuyển thành bảng THPT; điểm xét tuyển kết hợp được giữ đúng thang/phương thức.
- Trạng thái kết nối/chờ, thông báo lỗi và thử lại giữ lịch sử/câu hỏi. Không nhân đôi tin nhắn người dùng khi bấm thử lại.
- Phản hồi hữu ích/chưa hữu ích lưu ID ngẫu nhiên và boolean vào file local bị ignore; không ghi nội dung hội thoại, tên/điểm hoặc sender.
- Gateway Python standard library phục vụ đúng danh sách asset, proxy cùng origin, giới hạn payload/response, kiểm tra UUID/Origin/Host, CSP và dựng nội dung bằng DOM text.
- Service `web` trong Compose, image riêng không cần dependency Rasa, cổng `127.0.0.1:8686`, phụ thuộc Rasa healthy. Hướng dẫn chạy trực tiếp bằng Python cũng có trong README.
- README có ảnh thật, tính năng, quick start, bảng metrics, kiến trúc, giới hạn dữ liệu, hướng dẫn test, quyền riêng tư và tài liệu AI King.
- PDF AI King được sao chép nguyên byte, ghi đúng tên bài/tác giả/ngày/trang in. File gồm bìa và bài báo (12 trang), không phải toàn bộ kỷ yếu. Không dùng số liệu năm 2025 để báo chất lượng phiên bản hiện tại.

## Kiểm thử và kết quả

**131/131 test Python pass trên Docker Linux**, gồm 117 test backend và 14 test HTTP gateway. Gateway được chạy lại 14/14 sau sửa xử lý client ngắt kết nối. Test kiểm tra retry/cache, payload sai, tách sender, Origin/Host, route nội bộ, backend lỗi/empty, feedback không lưu PII, danh mục và health.

**13/13 nhóm kiểm tra trình duyệt pass với model Rasa thật**, không có JavaScript page error:

| Nhóm | Kết quả |
| --- | --- |
| Desktop 1440×1000, danh mục 67 mục | Pass; không tràn ngang |
| 5 tác vụ: danh mục, giới thiệu ngành, điểm chuẩn, tính tổ hợp, học phí | Pass qua UI → gateway → Rasa → SDK |
| Nguồn/năm/chương trình và bảng THPT | Pass; link có `noopener noreferrer` |
| Gửi phản hồi hữu ích | Pass |
| Backend 503 và thử lại | Pass; giữ lịch sử, không nhân đôi tin nhắn |
| HTML/link nguy hiểm, Markdown giới hạn | Pass; không tạo script/image từ tin nhắn |
| Bàn phím Shift + Enter | Pass |
| Reset và hai tab riêng | Pass; UUID sender khác nhau |
| Mobile 390×844 | Pass; không tràn ngang, thấy input và bảng điểm |

Trước khi engine Docker sẵn sàng, cùng bộ browser check được chạy với backend mô phỏng. Sau đó đã chạy lại **toàn bộ với model thật**; ảnh/video công khai được lấy từ lần chạy thật. Lỗi 503 trong browser test được chủ động mô phỏng tại boundary để kiểm tra phục hồi, không dùng để thay kết quả NLU.

Đã kiểm tra ảnh desktop, điểm chuẩn và mobile trực quan. UI có label cho input/select, log hội thoại `aria-live`, trạng thái kết nối, focus cho bàn phím và `prefers-reduced-motion`. Chưa thực hiện kiểm toán WCAG đầy đủ với người dùng screen reader; kiểm tra tự động/quan sát hiện tại không thay thế kiểm toán đó.

[Báo cáo UI và hash](evaluation/week5-ui.json) · [Ảnh desktop](assets/demo-desktop.png) · [Điểm chuẩn](assets/demo-cutoff.png) · [Mobile](assets/demo-mobile.png) · [Video demo](assets/demo.webm)

## Tái lập

```bash
docker compose build web
docker compose up -d --wait actions rasa web
docker compose run --rm check
```

Kiểm tra trình duyệt tùy chọn (Node.js 20+, không cần để chạy app):

```bash
npm ci
npx playwright install chromium ffmpeg
npm run test:web
node tests/web/record.cjs
```

`WEB_URL` đổi URL demo; `CHROME_EXECUTABLE` cho phép dùng Chrome có sẵn. `npm run test:web -- --mock` kiểm tra hành vi UI khi chưa có Rasa, cần gateway phục vụ asset/danh mục. Báo cáo và ảnh kiểm thử nằm trong `results/web-ui/`, bị ignore.

## Giới hạn vận hành

Gateway serialize request trong demo, cache tối đa 256 phản hồi thành công trong 10 phút. Timeout upstream có thể xảy ra sau khi Rasa đã xử lý; retry không bảo đảm exactly-once. Cache/feedback dedup chỉ có trong vòng đời tiến trình. Reset đổi sender chứ không xóa tracker cũ khỏi Rasa. Cấu hình chỉ dùng local; CI, xác thực/rate limiting và triển khai công khai tiếp tục theo tuần 6–7.
