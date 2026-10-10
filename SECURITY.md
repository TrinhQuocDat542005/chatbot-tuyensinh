# Bảo mật

## Phạm vi hỗ trợ

`v1.0.x` là phiên bản portfolio chạy local. Các model legacy năm 2025 không được hỗ trợ với action/domain hiện tại. Rasa 3.6, TensorFlow và Python 3.10 là stack được khóa để tái lập; chưa có kiểm toán bảo mật toàn bộ dependency.

Compose bind các cổng trên `127.0.0.1`. Không đưa cấu hình này thẳng lên Internet hoặc bật API quản trị/CORS toàn bộ origin. HTTPS, xác thực/rate limit, chính sách log và kiểm thử tải công khai chưa được nghiệm thu.

## Báo lỗ hổng

Dùng mục **Security → Report a vulnerability** trên GitHub; repository đã bật private vulnerability reporting. Nếu mục này không khả dụng với tài khoản của bạn, mở issue chỉ xin kênh liên hệ riêng; không đăng exploit, token, nội dung hội thoại hoặc dữ liệu cá nhân. Chưa cam kết thời gian xử lý; đây là dự án cá nhân.

Trong báo cáo riêng, cung cấp commit, cách chạy, bước tái hiện bằng dữ liệu giả, ảnh hưởng và biện pháp khắc phục nếu có. Không thực hiện thử nghiệm vào hệ thống tuyển sinh chính thức hoặc dịch vụ của bên thứ ba.

## Dữ liệu trong demo

Lịch sử UI nằm trong bộ nhớ trang; tracker Rasa nằm trong tiến trình và có thể còn sau khi đổi ID phiên. Cache gateway tối đa 10 phút. Feedback local chỉ lưu UUID câu trả lời và boolean ở `results/`; không có job tự xóa file feedback. Dừng demo và xóa file feedback local khi không cần; tránh nhập thông tin nhạy cảm và rà log trước khi chia sẻ.

Kiểm tra mẫu secret trước khi commit: `python scripts/audit_repository.py`. Rà toàn bộ lịch sử: thêm `--history`. Scanner nhận diện một số định dạng token/private key và file môi trường; không thay thế kiểm toán bảo mật hoặc chứng minh không có mọi loại bí mật.
