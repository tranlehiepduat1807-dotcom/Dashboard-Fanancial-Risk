# Dashboard Financial Risk

Dashboard quản trị rủi ro an toàn tài chính của công ty chứng khoán, sử dụng dữ liệu mô phỏng.

## Chạy ứng dụng

Mở `index.html` hoặc chạy `python -m http.server 8766` từ thư mục dự án. Không cần cài thư viện frontend hay build.

## Giao diện doanh nghiệp

- Nền trắng/xám, chữ xanh than, màu xanh dương cho hành động chính.
- Font Geist được lưu tại dự án dưới định dạng WOFF2; giấy phép trong `fonts/OFL.txt`.
- Cỡ chữ thống nhất, số liệu căn cột, màu trạng thái phân biệt an toàn/cảnh báo/vi phạm.
- Điều hướng thu gọn trên điện thoại; bảng dữ liệu cuộn trong khung; chú giải biểu đồ tự xuống dòng.
- Dữ liệu nhúng và mã tính toán hiện có được giữ nguyên. Lớp trình bày nằm trong `enterprise.css` và `enterprise.js`.

## Kiểm tra

`qa.html` kiểm tra 19 luồng thao tác trên trình duyệt. `review.html` hiển thị các phân hệ để rà soát giao diện. Xem `DESIGN_REVIEW.md` cho phạm vi kiểm tra và các cảnh báo còn mở.

Đây là bản thử nghiệm, không phải báo cáo pháp lý hay hệ thống vận hành đã được xác nhận tuân thủ.
