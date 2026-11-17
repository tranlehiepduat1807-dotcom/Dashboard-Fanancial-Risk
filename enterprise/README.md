# Risk Management Enterprise

Ứng dụng quản trị rủi ro công ty chứng khoán: FastAPI + SQLAlchemy, giao diện tiếng Việt, cơ sở dữ liệu trên máy chủ. Đây là phiên bản chức năng để UAT; chưa được nghiệm thu vận hành hoặc kết nối core/trading thật.

## Chạy trên Windows

Python 3.12 trở lên. Tại thư mục `enterprise`:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.lock
.venv/Scripts/python.exe manage.py create-user
# Tạo ít nhất một analyst và một approver khác nhau để thử quy trình.
# Chỉ chạy dòng sau trong DB rỗng nếu muốn dữ liệu giả lập:
.venv/Scripts/python.exe manage.py seed-sample
./start.ps1
```

Mở http://127.0.0.1:8000. Không có tài khoản/mật khẩu mặc định. Đổi mật khẩu trong Tài khoản & mô hình. SQLite mặc định dành cho chạy tại máy; tệp `risk.db` phải được bảo vệ và sao lưu. Tệp LOCAL_ACCESS.txt nếu có chỉ do phiên thiết lập máy hiện tại tạo, không nằm trong repo.

## Triển khai cho nhóm >20 người

Có cấu hình Docker Compose với PostgreSQL 16 và hai web workers. Phiên đăng nhập lưu trong DB, dùng được qua nhiều worker. PostgreSQL/Docker chưa được chạy thử trong môi trường làm việc này; cần kiểm tra tải và triển khai staging trước khi dùng thật.

1. Tạo `.env` với `POSTGRES_PASSWORD` mạnh, URL-safe; không commit.
2. `docker compose up -d --build`
3. `docker compose exec web python manage.py create-user` để tạo admin, analyst, approver.
4. Đặt sau reverse proxy TLS của công ty; bật `COOKIE_SECURE=1` khi truy cập qua HTTPS. Chỉ cổng loopback được ánh xạ theo mặc định.
5. Thực hiện sao lưu `pg_dump` và thử phục hồi, log tập trung, rate limit ở gateway, quét bảo mật, UAT và kiểm thử tải theo kích thước dữ liệu thực. Schema ban đầu được tạo tự động; chưa có hệ thống versioned migrations.

Không đưa tài khoản thật hoặc dữ liệu khách hàng lên GitHub Pages/Sites tĩnh. Hai nền tảng tĩnh cũ không chạy máy chủ Python này. Cần địa chỉ backend riêng trong hạ tầng công ty trước khi chuyển người dùng sang bản doanh nghiệp.

## Chức năng đã triển khai

| Phân hệ | Hành vi thực hiện được |
|---|---|
| Đăng nhập | Cookie HttpOnly, SameSite Strict, CSRF, PBKDF2; phiên 8 giờ lưu DB; đổi mật khẩu hủy mọi phiên |
| Phân quyền | Admin, analyst, approver, viewer, integration; kiểm tra phía API; admin cấp/khóa/mở tài khoản |
| Danh mục | Xem, tìm kiếm, đề nghị thêm/sửa vị thế, tỷ trọng, số ngày thoái vốn theo 10% ADV |
| Thị trường | Historical VaR/ES từ giá được duyệt, 95/97.5/99%; tối đa 500 lợi suất, tối thiểu 60; thiếu giá trả null |
| Stress | Cú sốc cổ phiếu qua beta, cú sốc lãi suất qua duration; tham số thay đổi được |
| Margin | Dư nợ, TSBĐ, haircut, LTV, lượng tài sản cần bổ sung |
| Đối tác | Dư nợ, xếp hạng nhập, hạn mức, tỷ lệ sử dụng, cảnh báo vượt |
| Thanh khoản | Lịch tiền vào/ra và số dư cộng dồn từ tiền mặt danh mục |
| Vốn | Vốn khả dụng và ba cấu phần rủi ro nhập; tỷ lệ tổng hợp, không tự gán trọng số pháp lý |
| Hạn mức | Chính sách có tên, chỉ tiêu, ngưỡng, mức độ và người phụ trách; cảnh báo tính từ dữ liệu |
| Sự cố | Tạo/sửa sự cố qua phê duyệt, trạng thái, tổn thất, người phụ trách, hạn xử lý |
| Phê duyệt | Người lập không được tự duyệt, ghi lý do, kiểm tra phiên bản, từ chối cập nhật cũ, khóa nghiệp vụ duy nhất |
| Dữ liệu | CSV UTF-8/JSON, kiểm tra cả lô, tối đa 1.000 dòng/2 MB, idempotency; mỗi dòng là một đề nghị |
| Báo cáo | CSV đã chống spreadsheet formula injection, báo cáo JSON có tham số, in màn hình |
| Audit | Login, thay đổi, quyết định, xuất dữ liệu, quản trị user; chỉ đọc qua API, chưa có WORM/chữ ký |

Không có gửi lệnh, force sell tự động, KYC/AML/surveillance, sổ cái kế toán, settlement reconciliation, corporate actions, derivative Greeks, SSO/MFA, email/SMS hoặc báo cáo pháp lý tự động. Những nghiệp vụ này cần xác định phạm vi với công ty, thiết kế connector và kiểm định riêng. Cảnh báo hiện hiển thị trong ứng dụng, chưa có notification engine.

## Hợp đồng kết nối

Đặc tả đầy đủ tại `GET /openapi.json`; schema trường tại `GET /api/schema` sau đăng nhập.

```python
import uuid, httpx
with httpx.Client(base_url='https://risk.internal.example') as c:
    login=c.post('/api/login',json={'username':'integration-user','password':'READ_FROM_SECRET_MANAGER'})
    login.raise_for_status()
    token=login.json()['csrf']
    result=c.post('/api/import/prices',headers={
        'X-CSRF-Token':token,
        'Idempotency-Key':str(uuid.uuid4()),
    },json=[{'symbol':'ASSET-A','date':'2026-11-16','close':100.0}])
    result.raise_for_status()
    print(result.json())  # pending; chưa cập nhật giá trước khi được duyệt
```

Batch chỉ thêm mới; sửa bản ghi bằng POST `/api/records/{kind}` cùng id/version. Nhập giá trùng symbol/date bị từ chối khi duyệt, cần đề nghị sửa bản cũ. Không có job scheduler/adapter của nhà cung cấp nào được cấu hình. Cần tài liệu API, cơ chế xác thực, bảng ánh xạ mã và sandbox của công ty để kết nối thật. API key/mật khẩu phải lưu tại secret manager, không điền trong mã hoặc chat.

## Phương pháp và giới hạn dữ liệu

Đơn vị tiền là tỷ VND. Vị thế long-only, không có cơ chế netting short/derivative. Giá phải cùng lịch ngày; cần xử lý chia tách/cổ tức trước khi nhập. VaR giữ nguyên giá trị vị thế hiện tại trên lợi suất ngày; ES lấy khối xác suất đuôi với trọng số phân số. Mức tối thiểu 60 quan sát dành cho kiểm tra chức năng, chưa đủ để tuyên bố mô hình đã được thẩm định. Stress là xấp xỉ tuyến tính. Kết quả margin là lượng TSBĐ sau haircut cần bổ sung, chưa áp quy trình gọi margin/force sell riêng của công ty. Dòng tiền không tự lọc ngày làm việc và không thay thế hệ thống treasury. Cấu phần an toàn vốn và ngưỡng cần được bộ phận tuân thủ phê duyệt theo quy định áp dụng.

## Kiểm thử

```powershell
.venv/Scripts/python.exe -m pytest -q
node --check app/static/app.js
```

19 kiểm thử API: xác thực, CSRF, viewer, maker/checker, conflict phiên bản, nhập nguyên tử, idempotency, khóa nghiệp vụ, VaR/ES trên mẫu biết trước, margin/thanh khoản/vốn, thiếu giá, xuất/audit, tạo user, cookie và logout. Kiểm tra trình duyệt cục bộ xác nhận login, 15 màn hình, lập đề nghị, hàng đợi, menu mobile, không tràn trang ở 390px và không lỗi JS. Chưa kiểm thử PostgreSQL, tải >20 người, pentest, phục hồi thảm họa hoặc tính phù hợp pháp lý. Một cảnh báo deprecation từ testclient/httpx của dependency vẫn còn.

Giao diện đã kiểm tra trực quan ở 1440px và 390px. Không áp dụng hero quảng cáo/fullscreen vào các màn hình tác nghiệp. Chưa chạy lại toàn bộ marketing design gate cho ứng dụng mới.


Thông tin tích hợp FSS FLEX được bổ sung tại [connectors/FSS_FLEX.md](connectors/FSS_FLEX.md). Adapter ánh xạ export đã có kiểm thử; chưa kết nối REST do chưa có spec/sandbox.
