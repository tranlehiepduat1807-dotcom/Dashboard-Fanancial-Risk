# Kết nối FSS FLEX / CoreFlex

Nguồn đích được người dùng xác nhận: FSS FLEX. FSS công bố FLEX hỗ trợ RESTful Open API: https://fss.com.vn/san-pham-va-dich-vu/ . Trang sản phẩm không cung cấp hợp đồng API cụ thể cho hệ thống của công ty. Chưa có kết nối mạng tới FLEX và chưa có endpoint nào được giả định.

## Những thông tin cần lấy từ đội Core/FSS

- Phiên bản FLEX và API gateway triển khai; base URL sandbox và production; OpenAPI/Postman hoặc tài liệu schema.
- Cơ chế xác thực hệ thống–hệ thống, vòng đời token, IP allowlist và quyền đọc được cấp.
- API vị thế tự doanh, dư nợ margin, tài sản bảo đảm, haircut/LTV, tiền khả dụng, nghĩa vụ thanh toán, danh mục chứng khoán và giá.
- Đơn vị tiền, giá, timestamp/múi giờ, lịch ngày giao dịch, source account/symbol identifiers, phân trang và watermark/cursor.
- Dữ liệu snapshot hay delta; cách xử lý giao dịch đảo, điều chỉnh, số dư âm, corporate actions, duplicate/retry.
- Tần suất cập nhật, giới hạn request, mã lỗi, SLA và người đối soát tại nghiệp vụ.

## Adapter đã có

`flex_mapper.py` ánh xạ JSON export sang schema nội bộ, đổi đơn vị bằng Decimal và báo lỗi nếu thiếu trường. File mapping đính kèm chỉ dùng tên example, tuyệt đối không mô tả tên trường thật của FSS.

```powershell
.venv/Scripts/python.exe connectors/flex_mapper.py --input flex-export.json --mapping connectors/flex-margin.mapping.example.json --output normalized-margin.json
```

Lô chuẩn hóa được gửi qua POST /api/import/margin bằng tài khoản integration, chờ checker duyệt. Chưa có adapter gọi REST, scheduler, retry/backoff, watermark, bulk checker hoặc đối soát tổng số dư. Chỉ bổ sung sau khi xác minh spec. Với dữ liệu lớn, không dùng hàng đợi duyệt từng giá làm thiết kế vận hành cuối cùng; cần thỏa thuận cơ chế batch certification và quy tắc auto-accept đã được kiểm soát.

## Nghiệm thu connector

Đối soát tổng dư nợ và tài sản bảo đảm với báo cáo FLEX cùng thời điểm; kiểm tra VND→tỷ VND, lịch giá, tài khoản đóng/mở, duplicate/retry, điều chỉnh và mất kết nối. Chưa đạt nghiệm thu trước khi thực hiện các kiểm tra này trên sandbox thật.
