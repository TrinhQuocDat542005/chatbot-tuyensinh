# Changelog

## 1.0.0 — 2026-10-10

Phiên bản portfolio chạy local; không có dịch vụ hosting trả phí hoặc URL demo công khai.

- Sửa parser môn/điểm, xử lý thiếu môn, điểm sai và dấu phẩy thập phân; chỉ tính tổ hợp hợp lệ.
- Chuẩn hóa 26 ngành, 41 chuyên ngành và 48 bản ghi điểm xét tuyển kết hợp 2026; có schema, nguồn và phạm vi.
- Bổ sung hội thoại nhiều lượt, forms, sửa ngữ cảnh, reset và fallback.
- Web responsive với nguồn, bảng điểm, retry, ID phiên riêng, feedback và xử lý nội dung an toàn.
- README, ảnh/video và tài liệu nghiên cứu AI King 2025.
- Ba runtime Docker, khóa dependency Linux, manifest model/checksum và CI kiểm tra nhẹ/model regression.
- Bộ tài liệu đóng góp, bảo mật, quyền sử dụng, audit và quy trình phát hành.
- Core fallback dùng action mặc định có revert để tránh lặp utterance khi policy thiếu tự tin; regression kiểm tra giới hạn số phản hồi và lượt tiếp sau fallback.

Model phát hành lấy từ workflow sạch tại commit `7be7e2f6d9b7e366cb41e408e46c7b087fc98597`: macro-F1 intent 0,9010; entity exact-span F1 0,9608 trên tập 154 câu tự soạn đã review. 141 test Python, Core 10/10, REST 22+4 và 13 nhóm browser thật đã pass. Không coi đây là đánh giá mù trên người dùng mới.

Giới hạn: chưa có dữ liệu THPT cùng thang để gợi ý ngành theo điểm; nhiều mô tả ngành còn chờ xác minh; chưa nghiệm thu vận hành Internet, tải đồng thời hoặc nâng cấp vòng đời runtime.
