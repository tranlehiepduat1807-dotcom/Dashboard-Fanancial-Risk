/* TCBS iFlash read-only data workspace. Credentials are never entered here. */
const beforeTcbsRender = render;
let tcbsPreview = null;
render = function () {
  beforeTcbsRender();
  if (route === "integration") mountTcbs();
};
const tcbsMoney = value => Number(value).toLocaleString('vi-VN', {minimumFractionDigits: 2, maximumFractionDigits: 9});
const tcbsColumnSets = {
  assets: [
    ["Mã CK", (r) => esc(r.symbol)],
    ["Khối lượng", (r) => num(r.quantity, 0)],
    ["Giá TB (nguồn)", (r) => num(r.avgPrice)],
    ["Giá trị thị trường (tỷ)", (r) => tcbsMoney(r.value)],
  ],
  cash: [
    ["Tiểu khoản", (r) => esc(r.account)],
    ["Tiền đầu ngày (tỷ)", (r) => tcbsMoney(r.bod)],
    ["Tiền mặt (tỷ)", (r) => tcbsMoney(r.cash)],
    ["Sức mua BOND/FUND (tỷ)", (r) => tcbsMoney(r.purchasingPower)],
  ],
  risk: [
    ["Tiểu khoản", (r) => esc(r.account)],
    ["Rtt (nguồn)", (r) => num(r.rtt)],
    ["Nợ gốc (tỷ)", (r) => tcbsMoney(r.principal)],
    ["Lãi (tỷ)", (r) => tcbsMoney(r.interest)],
    ["Đến hạn (tỷ)", (r) => tcbsMoney(r.due)],
    ["Quá hạn (tỷ)", (r) => tcbsMoney(r.overdue)],
    ["Phí nợ (tỷ)", (r) => tcbsMoney(r.feeDebt)],
    ["Ký quỹ ban đầu (nguồn)", (r) => num(r.initial)],
    ["Duy trì (nguồn)", (r) => num(r.maintenance)],
    ["Cảnh báo (nguồn)", (r) => num(r.liquidation)],
    ["Trạng thái nguồn", (r) => esc(r.status), "text"],
  ],
  quotes: [
    ["Mã CK", (r) => esc(r.symbol)],
    ["Giá khớp (nguồn)", (r) => num(r.price)],
    ["Tham chiếu (nguồn)", (r) => num(r.reference)],
    ["Tổng khối lượng", (r) => num(r.volume, 0)],
  ],
  history: [
    ["Mã CK", (r) => esc(r.symbol)],
    ["Ngày giao dịch (VN)", (r) => esc(r.date)],
    ["Giá đóng cửa (nguồn)", (r) => num(r.close)],
  ],
};
async function mountTcbs() {
  tcbsPreview = null;
  const host = document.createElement("section");
  host.id = "tcbs-workspace";
  host.className = "panel";
  $("#content").prepend(host);
  host.innerHTML =
    '<div class="panel-body muted">Đang đọc cấu hình kết nối TCBS…</div>';
  try {
    const status = await api("tcbs/status");
    if (route !== "integration" || !host.isConnected) return;
    const writable = ["admin", "analyst", "integration"].includes(user.role);
    host.innerHTML = `<div class="panel-head"><div><span class="eyebrow">NGUỒN DỮ LIỆU MỚI · API v1.0.0</span><h2>Kết nối TCBS iFlash</h2></div>${badge(status.configured ? "Đã cấu hình JWT" : "Chưa cấu hình API", status.configured ? "good" : "pending")}</div><div class="panel-body"><div class="tcbs-intro"><div><h3>Dữ liệu tài khoản và thị trường</h3><p>Tập trung tài sản, số dư và rủi ro margin để đối soát trước khi sử dụng.</p><p class="muted">Bạn có thể khám phá dữ liệu minh họa hoặc nhập phản hồi JSON ngay. Kết nối thật cần quyền iFlash và JWT hợp lệ trên máy chủ.</p></div><a class="tcbs-doc-link" href="https://developers.tcbs.com.vn/docs/v1.0.0/introduction/" target="_blank" rel="noopener">Tài liệu TCBS ↗</a></div><div class="tcbs-capabilities">${Object.entries(
      status.catalog,
    )
      .map(
        ([key, item]) =>
          `<div><strong>${esc(item.label)}</strong><small>GET · Tài liệu trang ${item.page}</small></div>`,
      )
      .join("")}</div>${
      writable
        ? `<form id="tcbs-preview-form"><div class="tcbs-fields"><label>Nguồn dữ liệu<select name="source" id="tcbs-source"><option value="sample">Dữ liệu minh họa</option><option value="upload">Phản hồi JSON</option><option value="live" ${status.configured ? "" : "disabled"}>API TCBS trực tiếp${status.configured ? "" : " · chưa cấu hình"}</option></select></label><label>Nhóm dữ liệu<select name="resource" id="tcbs-resource">${Object.entries(
            status.catalog,
          )
            .map(
              ([key, item]) =>
                `<option value="${key}">${esc(item.label)}</option>`,
            )
            .join(
              "",
            )}</select></label><label id="tcbs-account-field" hidden>Số tiểu khoản<input name="account" maxlength="30" autocomplete="off" placeholder="Nhập số tiểu khoản TCBS"></label><label id="tcbs-symbol-field" hidden>Mã chứng khoán<input name="symbol" maxlength="10" placeholder="Ví dụ: TCB"></label><label id="tcbs-count-field" hidden>Số nến ngày<input name="count" type="number" min="1" max="500" value="100"></label></div><div id="tcbs-json-field" hidden><label>Chọn JSON phản hồi từ API<input id="tcbs-json-file" type="file" accept=".json,application/json"></label><label>Nội dung JSON<textarea name="payload" id="tcbs-payload" placeholder="Dán phản hồi JSON đúng nhóm dữ liệu đã chọn…" spellcheck="false"></textarea></label><p class="muted">Tối đa 2 MB. Nội dung nhập chưa được xác minh là từ TCBS. Không dán API Key, OTP hoặc JWT.</p></div><div class="tcbs-actions"><button class="primary" type="submit" id="tcbs-preview-button">Xem dữ liệu minh họa</button><span class="muted" id="tcbs-mode-note">Dữ liệu giả lập để kiểm tra giao diện.</span></div><p id="tcbs-error" role="alert"></p></form>`
        : '<div class="notice">Cần vai trò chuyên viên, quản trị viên hoặc tích hợp để xem trước dữ liệu nguồn.</div>'
    }<div id="tcbs-preview-output"></div><details class="tcbs-scope"><summary>Phương pháp đối soát và phạm vi tích hợp</summary><p class="muted">Tiền được quy đổi VND → tỷ VND; giá và Rtt giữ nguyên giá trị nguồn. Rtt và các ngưỡng ký quỹ của TCBS được hiển thị riêng, chưa quy đổi sang LTV nội bộ. Ngày nến được chuyển sang múi giờ Việt Nam. Nến nhập cần là nến ngày đã đóng, giá đã xử lý corporate actions trước khi dùng cho VaR.</p><p class="muted">Lịch sử giá gửi thành đề nghị để một người khác phê duyệt. Tài sản chưa tự nhập vào danh mục vì API chưa cung cấp các tham số mô hình như Beta và ADV theo phương pháp nội bộ.</p></details></div>`;
    if (!writable) return;
    const mode = () => {
      const source = $("#tcbs-source").value,
        resource = $("#tcbs-resource").value;
      $("#tcbs-account-field").hidden =
        source !== "live" || !["assets", "cash", "risk"].includes(resource);
      $("#tcbs-symbol-field").hidden =
        source !== "live" || !["history", "quotes"].includes(resource);
      $("#tcbs-count-field").hidden =
        source !== "live" || resource !== "history";
      $("#tcbs-json-field").hidden = source !== "upload";
      $("#tcbs-preview-button").textContent =
        source === "sample"
          ? "Xem dữ liệu minh họa"
          : source === "upload"
            ? "Kiểm tra & xem trước JSON"
            : "Đọc dữ liệu từ TCBS";
      $("#tcbs-mode-note").textContent =
        source === "sample"
          ? "Dữ liệu giả lập, không nhập vào báo cáo."
          : source === "upload"
            ? "Kiểm tra cấu trúc, đơn vị và dữ liệu trước khi duyệt."
            : "Đọc theo yêu cầu, chưa có cập nhật tự động.";
      $("#tcbs-preview-output").innerHTML = "";
      $("#tcbs-error").textContent = "";
      tcbsPreview = null;
    };
    $("#tcbs-source").onchange = $("#tcbs-resource").onchange = mode;
    $("#tcbs-json-file").onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      if (file.size > 2000000) {
        $("#tcbs-error").textContent = "Tệp JSON vượt 2 MB";
        e.target.value = "";
        return;
      }
      $("#tcbs-payload").value = await file.text();
    };
    $("#tcbs-preview-form").onsubmit = async (e) => {
      e.preventDefault();
      const b = $("#tcbs-preview-button");
      b.disabled = true;
      $("#tcbs-error").textContent = "";
      tcbsPreview = null;
      $("#tcbs-preview-output").innerHTML = "";
      try {
        const data = Object.fromEntries(new FormData(e.target));
        if (data.source === "upload") {
          try {
            data.payload = JSON.parse(data.payload);
          } catch {
            throw Error("Nội dung JSON chưa hợp lệ.");
          }
        } else delete data.payload;
        if (data.source !== "live") {
          delete data.symbol;
          delete data.account;
        }
        const result = await api("tcbs/preview", {
          method: "POST",
          body: JSON.stringify(data),
        });
        if (route !== "integration" || !host.isConnected) return;
        tcbsPreview = result;
        showTcbsPreview(result);
      } catch (err) {
        if ($("#tcbs-error")) $("#tcbs-error").textContent = err.message;
      } finally {
        b.disabled = false;
      }
    };
  } catch (err) {
    if (host.isConnected)
      host.innerHTML = `<div class="panel-body notice">${esc(err.message)}</div>`;
  }
}
function showTcbsPreview(result) {
  const output = $("#tcbs-preview-output");
  output.innerHTML = `<div class="tcbs-preview-heading"><h3>${result.source === "sample" ? "Bản minh họa" : "Bản xem trước"} · ${result.rows.length} dòng</h3>${badge(result.source === "sample" ? "Giả lập" : "Chưa phê duyệt", result.source === "sample" ? "pending" : "high")}</div><div class="notice">${esc(result.note)}</div>${table(tcbsColumnSets[result.resource], result.rows)}${result.can_submit && result.rows.length ? '<div class="tcbs-actions"><button id="tcbs-send-prices" class="primary">Gửi lịch sử giá để phê duyệt</button><span class="muted">Số liệu chỉ có hiệu lực sau khi được duyệt.</span></div>' : ""}<p class="muted" id="tcbs-submit-result" role="status"></p>`;
  // Reuse centred numeric columns and sortable headers for this provider table only.
  output.querySelectorAll("table").forEach((t) => {
    Array.from(t.tHead.rows[0].cells).forEach((h, i) => {
      const cells = Array.from(t.tBodies[0].rows).map((r) => r.cells[i]);
      if (cells.some((c) => /^[−-]?\d[\d.,]*%?$/.test(c.textContent.trim()))) {
        h.classList.add("numeric");
        cells.forEach((c) => c.classList.add("numeric"));
      }
    });
  });
  if ($("#tcbs-send-prices"))
    $("#tcbs-send-prices").onclick = async (e) => {
      e.target.disabled = true;
      try {
        const r = await api(`tcbs/snapshots/${result.id}/submit`, {
          method: "POST",
        });
        $("#tcbs-submit-result").textContent =
          `Đã tạo ${r.count} đề nghị giá; ${r.unchanged} dòng không thay đổi. Mở Phê duyệt để theo dõi.`;
      } catch (err) {
        $("#tcbs-submit-result").textContent = err.message;
        e.target.disabled = false;
      }
    };
}
