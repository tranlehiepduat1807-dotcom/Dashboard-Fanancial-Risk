const $ = (s) => document.querySelector(s),
  esc = (v) =>
    String(v ?? "").replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
const num = (v, d = 2) =>
  v == null
    ? "—"
    : Number(v).toLocaleString("vi-VN", {
        maximumFractionDigits: d,
        minimumFractionDigits: d,
      });
let user,
  csrf,
  schema = {},
  state = {},
  route = "overview",
  filter = "",
  editing = null,
  confidence = 0.99,
  shock = -0.15,
  rate = 0.02;
const labels = {
  symbol: "Mã tài sản",
  book: "Danh mục / bộ phận",
  sector: "Ngành",
  type: "Loại tài sản",
  value: "Giá trị (tỷ)",
  beta: "Beta",
  duration: "Duration (năm)",
  adv: "GTGD bình quân/ngày (tỷ)",
  account: "Tài khoản",
  name: "Tên",
  debt: "Dư nợ (tỷ)",
  collateral: "TSBĐ trước chiết khấu (tỷ)",
  haircut: "Tỷ lệ chiết khấu (0–1)",
  maintenance: "LTV tối đa (0–1)",
  due: "Ngày đến hạn",
  rating: "Xếp hạng",
  exposure: "Dư nợ đối tác (tỷ)",
  limit: "Hạn mức (tỷ)",
  date: "Ngày dữ liệu",
  category: "Nhóm",
  inflow: "Dòng tiền vào (tỷ)",
  outflow: "Dòng tiền ra (tỷ)",
  metric: "Chỉ tiêu",
  threshold: "Ngưỡng cảnh báo",
  severity: "Mức độ",
  owner: "Người phụ trách",
  title: "Tên sự cố",
  status: "Trạng thái",
  loss: "Tổn thất (tỷ)",
  notes: "Ghi chú xử lý",
  close: "Giá đóng cửa",
  available: "Vốn khả dụng (tỷ)",
  market: "Rủi ro thị trường (tỷ)",
  settlement: "Rủi ro thanh toán (tỷ)",
  operational: "Rủi ro hoạt động (tỷ)",
  username: "Tên đăng nhập",
  password: "Mật khẩu",
  role: "Vai trò",
};
const words = {
  equity: "Cổ phiếu",
  bond: "Trái phiếu",
  cash: "Tiền mặt",
  high: "Cao",
  medium: "Trung bình",
  low: "Thấp",
  open: "Mở",
  investigating: "Đang xử lý",
  resolved: "Đã khắc phục",
  operational: "Vận hành",
  compliance: "Tuân thủ",
  data: "Dữ liệu",
  cyber: "An ninh mạng",
  var_pct: "VaR / NAV (%)",
  concentration_pct: "Tỷ trọng lớn nhất (%)",
  margin_ltv_pct: "LTV margin cao nhất (%)",
  counterparty_pct: "Sử dụng HM đối tác (%)",
  liquidity_gap: "Thiếu hụt tiền (tỷ)",
  pending: "Chờ duyệt",
  approved: "Đã duyệt",
  rejected: "Từ chối",
  admin: "Quản trị viên",
  analyst: "Chuyên viên",
  approver: "Người phê duyệt",
  viewer: "Chỉ xem",
  integration: "Tích hợp dữ liệu",
};
const pages = {
  overview: [
    "Tổng quan",
    "Theo dõi rủi ro trọng yếu và những việc cần xử lý trong ngày.",
    "ĐIỀU HÀNH",
  ],
  positions: [
    "Danh mục đầu tư",
    "Quản lý vị thế, phân bổ tài sản và khả năng thoái vốn.",
    "DANH MỤC & THỊ TRƯỜNG",
  ],
  market: [
    "Rủi ro thị trường",
    "VaR và Expected Shortfall từ lịch sử giá được phê duyệt.",
    "DANH MỤC & THỊ TRƯỜNG",
  ],
  stress: [
    "Kiểm tra sức chịu đựng",
    "Đánh giá tác động của cú sốc cổ phiếu và lãi suất lên danh mục.",
    "DANH MỤC & THỊ TRƯỜNG",
  ],
  margin: [
    "Tín dụng & margin",
    "Giám sát dư nợ, tài sản bảo đảm và yêu cầu bổ sung.",
    "NGHIỆP VỤ & GIỚI HẠN",
  ],
  counterparties: [
    "Đối tác & thanh toán",
    "Theo dõi dư nợ, xếp hạng và mức sử dụng hạn mức đối tác.",
    "NGHIỆP VỤ & GIỚI HẠN",
  ],
  cashflows: [
    "Thanh khoản",
    "Lập lịch dòng tiền và phát hiện thiếu hụt theo ngày.",
    "NGHIỆP VỤ & GIỚI HẠN",
  ],
  capital: [
    "An toàn vốn",
    "Theo dõi vốn khả dụng và các cấu phần giá trị rủi ro.",
    "NGHIỆP VỤ & GIỚI HẠN",
  ],
  limits: [
    "Hạn mức & cảnh báo",
    "Thiết lập khẩu vị rủi ro và phân công xử lý vi phạm.",
    "NGHIỆP VỤ & GIỚI HẠN",
  ],
  incidents: [
    "Sự cố & tuân thủ",
    "Ghi nhận tổn thất, phân công trách nhiệm và theo dõi khắc phục.",
    "KIỂM SOÁT",
  ],
  approvals: [
    "Phê duyệt",
    "Kiểm soát thay đổi theo nguyên tắc người lập và người duyệt độc lập.",
    "KIỂM SOÁT",
  ],
  reports: [
    "Báo cáo",
    "Xuất dữ liệu đã phê duyệt phục vụ đối soát và lưu hồ sơ.",
    "KIỂM SOÁT",
  ],
  integration: [
    "Dữ liệu & kết nối",
    "Nhập CSV hoặc tích hợp API theo lô có kiểm soát phê duyệt.",
    "HỆ THỐNG",
  ],
  users: [
    "Người dùng",
    "Cấp tài khoản và phân quyền theo trách nhiệm.",
    "HỆ THỐNG",
  ],
  audit: [
    "Nhật ký kiểm toán",
    "Truy vết người thực hiện và nội dung thay đổi trên máy chủ.",
    "HỆ THỐNG",
  ],
  settings: [
    "Tài khoản & mô hình",
    "Thông tin phương pháp và bảo mật tài khoản.",
    "HỆ THỐNG",
  ],
};
const canWrite = () => ["admin", "analyst"].includes(user.role);
async function api(url, opts = {}) {
  const r = await fetch("/api/" + url, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrf || "",
      ...opts.headers,
    },
  });
  let data;
  try {
    data = await r.json();
  } catch {
    throw Error("Phản hồi máy chủ không hợp lệ");
  }
  if (!r.ok) {
    if (r.status === 401 && url !== "login") showLogin();
    throw Error(
      typeof data.detail === "string"
        ? data.detail
        : "Dữ liệu yêu cầu chưa hợp lệ",
    );
  }
  return data;
}
function toast(msg) {
  $("#toast").textContent = msg;
  $("#toast").hidden = false;
  setTimeout(() => ($("#toast").hidden = true), 5000);
}
function showLogin() {
  $("#workspace").hidden = true;
  $("#login").hidden = false;
}
function badge(value, cls = "") {
  return `<span class="tag ${esc(cls)}">${esc(words[value] || value)}</span>`;
}
function panel(title, body, sub = "") {
  return `<section class="panel"><div class="panel-head"><h2>${esc(title)}</h2><small>${esc(sub)}</small></div>${body}</section>`;
}
function empty(msg = "Chưa có dữ liệu được phê duyệt.") {
  return `<div class="empty">${esc(msg)}</div>`;
}
function table(cols, rows) {
  return rows.length
    ? `<div class="table-wrap"><table><thead><tr>${cols.map((c) => `<th scope="col">${esc(c[0])}</th>`).join("")}</tr></thead><tbody>${rows.map((r) => `<tr>${cols.map((c) => `<td class="${c[2] || ""}">${c[1](r)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`
    : empty();
}
function kpis(items) {
  return `<div class="kpis">${items.map(([label, value, note, cls]) => `<div class="kpi"><label>${esc(label)}</label><strong class="${cls || ""}">${esc(value)}</strong><small>${esc(note)}</small></div>`).join("")}</div>`;
}
function chart(values) {
  const max = Math.max(...values.map(Math.abs), 0.01);
  return `<div class="bars" role="img" aria-label="Biên độ tổn thất lịch sử">${values.map((v) => `<div title="${esc(num(v) + " tỷ")}" style="height:${Math.max(1, (Math.abs(v) / max) * 160)}px;background:${v > 0 ? "#b76b70" : "#6588c1"}"></div>`).join("")}</div>`;
}
// All dynamic text is escaped before HTML insertion; event listeners never use inline JS.
async function start() {
  const me = await api("me");
  user = me.user;
  csrf = me.csrf;
  schema = await api("schema");
  $("#identity").textContent = user.name + " · " + words[user.role];
  $("#login").hidden = true;
  $("#workspace").hidden = false;
  let group = "";
  $("#nav").innerHTML = Object.entries(pages)
    .filter(
      ([k]) =>
        !(k === "users" && user.role !== "admin") &&
        !(k === "audit" && !["admin", "approver"].includes(user.role)),
    )
    .map(([key, [title, , g]], i) => {
      let head = g !== group ? `<div class="group">${g}</div>` : "";
      group = g;
      return `${head}<a href="#${key}" data-route="${key}"><span>${String(i + 1).padStart(2, "0")}</span>${title}</a>`;
    })
    .join("");
  await navigate();
}
async function navigate() {
  route = location.hash.slice(1) || "overview";
  if (!pages[route]) route = "overview";
  filter = "";
  document.body.classList.remove("nav-open");
  $("#menu").setAttribute("aria-expanded", "false");
  document
    .querySelectorAll("#nav a")
    .forEach((a) =>
      a.setAttribute(
        "aria-current",
        a.dataset.route === route ? "page" : "false",
      ),
    );
  let [title, subtitle, group] = pages[route];
  $("#title").textContent = title;
  $("#breadcrumb").textContent = title;
  $("#subtitle").textContent = subtitle;
  $("#section-label").textContent = group;
  $("#page-actions").innerHTML = '<button id="refresh">↻ Làm mới</button>';
  $("#refresh").onclick = () => navigate();
  $("#content").innerHTML = '<div class="loading">Đang tải dữ liệu…</div>';
  try {
    state.analytics = await api(
      `analytics?confidence=${confidence}&shock=${shock}&rate=${rate}`,
    );
    if (schema[route]) state.rows = await api("records/" + route);
    if (route === "approvals") state.rows = await api("approvals");
    if (route === "users") state.rows = await api("users");
    if (route === "audit") state.rows = await api("audit");
    render();
  } catch (e) {
    $("#content").innerHTML = panel(
      "Không thể tải dữ liệu",
      `<div class="empty">${esc(e.message)}</div>`,
    );
  }
  $("#clock").textContent = new Date().toLocaleDateString("vi-VN");
}
function render() {
  const a = state.analytics;
  $("#source-status").textContent = a.sample_data
    ? "DỮ LIỆU GIẢ LẬP · Chưa kết nối core/trading"
    : "Dữ liệu nội bộ · Chưa xác minh nguồn bên ngoài";
  let html = "";
  if (schema[route]) {
    if (canWrite()) {
      $("#page-actions").insertAdjacentHTML(
        "beforeend",
        '<button id="add" class="primary">+ Lập đề nghị mới</button>',
      );
      $("#add").onclick = () => openEditor(route);
    }
    html = recordPage(route);
  } else if (route === "overview") {
    html =
      kpis([
        ["Tổng giá trị danh mục", num(a.nav), "Giá trị vị thế đã phê duyệt"],
        ["VaR 99% · 1 ngày", num(a.var), a.observations + " quan sát giá"],
        [
          "Vi phạm hạn mức",
          a.breaches.length,
          "Cần rà soát và phân công",
          a.breaches.length ? "negative" : "",
        ],
        [
          "Tài khoản cần bổ sung",
          a.margin.filter((x) => x.breach).length,
          "Sau chiết khấu tài sản bảo đảm",
          "negative",
        ],
      ]) +
      (!a.var ? `<div class="notice">${esc(a.data_status)}</div>` : "") +
      `<div class="grid">${panel(
        "Phân bổ danh mục",
        `<div class="panel-body allocation">${
          a.positions
            .slice(0, 10)
            .map(
              (x) =>
                `<div><div class="allocation-line"><strong>${esc(x.symbol)}</strong><span>${num(x.weight)}% · ${num(x.value)} tỷ</span></div><div class="track"><div style="width:${Math.min(100, x.weight)}%"></div></div></div>`,
            )
            .join("") || empty("Thêm vị thế để bắt đầu theo dõi danh mục.")
        }</div>`,
      )}${panel("Ưu tiên trong ngày", `<div class="panel-body"><div class="risk-summary"><span>Stress danh mục hiện tại</span><strong class="negative">${num(a.stress_total)} tỷ</strong></div><div class="risk-summary"><span>Đối tác vượt hạn mức</span><strong>${a.counterparties.filter((x) => x.breach).length}</strong></div><div class="risk-summary"><span>Ngày dự kiến thiếu tiền</span><strong>${a.cashflows.filter((x) => x.balance < 0).length}</strong></div><div class="risk-summary"><span>Tỷ lệ vốn khả dụng</span><strong>${num(a.capital?.far)}%</strong></div><p class="muted">Các số liệu chỉ tổng hợp dữ liệu đã được duyệt. Giá trị rủi ro cần đối soát với nguồn nghiệp vụ.</p><a href="#approvals">Mở hàng đợi phê duyệt →</a></div>`)}</div>` +
      breaches(a);
  } else if (route === "market") {
    html =
      `<div class="toolbar"><label>Mức tin cậy<select id="confidence">${[0.95, 0.975, 0.99].map((c) => `<option value="${c}" ${c === confidence ? "selected" : ""}>${c * 100}%</option>`).join("")}</select></label></div>` +
      kpis([
        ["Historical VaR", num(a.var), "Tỷ VND · kỳ hạn 1 ngày"],
        ["Expected Shortfall", num(a.es), "Trung bình đuôi tổn thất"],
        ["VaR / NAV", num(a.metrics.var_pct) + "%", "Giá trị vị thế hiện tại"],
        ["Quan sát hợp lệ", a.observations, "Tối đa 500 ngày giao nhau"],
      ]) +
      `<div class="notice">${esc(a.data_status)}. Ngày giá chung mới nhất: ${esc(a.price_asof || "chưa có")}. Phân tích dùng giá đóng cửa chưa điều chỉnh nếu nguồn nhập chưa điều chỉnh corporate actions.</div>` +
      panel(
        "Biên độ lãi lỗ lịch sử",
        `<div class="panel-body">${a.losses.length ? chart(a.losses) : empty("Nhập lịch sử giá tại Dữ liệu & kết nối.")}<p class="muted">Cột đỏ: tổn thất · Cột xanh: lãi. Giữ nguyên vị thế hiện tại trên lịch sử lợi suất.</p></div>`,
      ) +
      panel(
        "Phương pháp tính",
        `<div class="panel-body muted">${esc(a.method)}</div>`,
      );
  } else if (route === "stress") {
    html =
      `<form id="stress-form" class="toolbar"><label>Cú sốc cổ phiếu (%)<input name="shock" type="number" value="${shock * 100}" min="-90" max="100" step=".1" required></label><label>Thay đổi lãi suất (điểm %)<input name="rate" type="number" value="${rate * 100}" min="-20" max="20" step=".01" required></label><button class="primary">Chạy kịch bản</button></form>` +
      kpis([
        ["Tác động danh mục", num(a.stress_total), "Tỷ VND", "negative"],
        ["NAV sau cú sốc", num(a.nav + a.stress_total), "Giả định tuyến tính"],
        ["Cổ phiếu", num(shock * 100) + "%", "Nhân beta từng vị thế"],
        [
          "Lãi suất",
          num(rate * 100) + " điểm %",
          "Xấp xỉ duration cho trái phiếu",
        ],
      ]) +
      panel(
        "Kết quả theo tài sản",
        table(
          [
            ["Tài sản", (x) => esc(x.symbol)],
            ["Giá trị", (x) => num(x.value)],
            [
              "Tác động",
              (x) =>
                `<strong class="${x.pnl < 0 ? "negative" : "positive"}">${num(x.pnl)}</strong>`,
            ],
          ],
          a.stress,
        ),
      ) +
      `<div class="notice">Kịch bản chưa bao gồm convexity, biến động spread, phí giao dịch và tác động giá khi bán lớn.</div>`;
  } else if (route === "approvals") {
    html = panel(
      "Hàng đợi thay đổi",
      table(
        [
          ["Ngày lập", (x) => esc(x.created.slice(0, 16))],
          ["Phân hệ", (x) => esc(pages[x.kind]?.[0] || labels[x.kind])],
          ["Người lập", (x) => esc(x.maker)],
          [
            "Trạng thái",
            (x) =>
              badge(
                x.status,
                x.status === "approved"
                  ? "good"
                  : x.status === "rejected"
                    ? "bad"
                    : "pending",
              ),
          ],
          [
            "Nội dung",
            (x) =>
              `<details><summary>Xem thay đổi</summary><pre>${esc(JSON.stringify(JSON.parse(x.data), null, 2))}</pre>${esc(x.reason || "")}</details>`,
            "text",
          ],
          [
            "Thao tác",
            (x) =>
              x.status === "pending" &&
              ["admin", "approver"].includes(user.role) &&
              x.maker !== user.username
                ? `<button data-decide="${esc(x.id)}" data-value="approve">Duyệt</button> <button class="danger" data-decide="${esc(x.id)}" data-value="reject">Từ chối</button>`
                : esc(x.checker || "—"),
          ],
        ],
        state.rows,
      ),
    );
  } else if (route === "reports") {
    html =
      panel(
        "Bộ dữ liệu đã phê duyệt",
        `<div class="panel-body">${Object.keys(schema)
          .map(
            (k) =>
              `<div class="report-row"><div><strong>${esc(pages[k]?.[0] || "Lịch sử giá")}</strong><small>CSV UTF-8 · Dữ liệu hiện tại · Có nhật ký xuất</small></div><button data-export="${k}">Xuất CSV ↓</button></div>`,
          )
          .join("")}</div>`,
      ) +
      panel(
        "Báo cáo tổng hợp",
        `<div class="panel-body"><p class="muted">Tải JSON chứa số liệu, tham số và phương pháp tại thời điểm xuất để lưu hồ sơ phân tích.</p><button id="snapshot">Tải báo cáo rủi ro JSON</button> <button id="print">In báo cáo hiện tại</button></div>`,
      );
  } else if (route === "integration") {
    html =
      panel(
        "Tiếp nhận dữ liệu",
        `<div class="panel-body"><div class="toolbar"><label>Loại dữ liệu<select id="import-kind">${Object.keys(
          schema,
        )
          .map(
            (k) =>
              `<option value="${k}">${esc(pages[k]?.[0] || "Lịch sử giá")}</option>`,
          )
          .join(
            "",
          )}</select></label><button id="template">Tải mẫu CSV ↓</button>${["admin", "analyst", "integration"].includes(user.role) ? '<label class="file"><span>Chọn CSV để gửi phê duyệt ↑</span><input id="import-file" type="file" accept=".csv" aria-label="Chọn CSV nhập dữ liệu"></label>' : ""}</div><p class="muted">Mỗi lô tối đa 1.000 dòng / 2 MB, UTF-8, dấu phẩy. Kiểm tra toàn bộ lô trước khi ghi. Mỗi dòng tạo một đề nghị chờ duyệt; không cập nhật trực tiếp số liệu đang sử dụng.</p><div id="import-result" role="status"></div></div>`,
      ) +
      panel(
        "API tích hợp nghiệp vụ",
        `<div class="panel-body"><div class="notice">Nguồn đích: FSS FLEX / CoreFlex. Đang chờ tài liệu API và sandbox của công ty để cấu hình kết nối.</div><p>Hợp đồng API đã có cho nguồn nội bộ: đăng nhập tài khoản integration, lấy CSRF token và gửi lô có Idempotency-Key.</p><pre>POST /api/login\nGET /api/schema\nPOST /api/import/{kind}\nContent-Type: application/json\nX-CSRF-Token: &lt;token&gt;\nIdempotency-Key: &lt;batch-id&gt;\n\n[ { ... các trường theo schema ... } ]</pre><p class="muted">Xem đặc tả tương tác tại <a href="/openapi.json" target="_blank" rel="noopener">OpenAPI JSON</a>. Chưa có dữ liệu thị trường trực tuyến hoặc chức năng gửi lệnh.</p></div>`,
      );
  } else if (route === "users") {
    html =
      panel(
        "Tài khoản trong tổ chức",
        table(
          [
            ["Tài khoản", (x) => esc(x.username)],
            ["Họ tên", (x) => esc(x.name)],
            ["Vai trò", (x) => badge(words[x.role])],
            [
              "Trạng thái",
              (x) =>
                badge(
                  x.active ? "Hoạt động" : "Đã khóa",
                  x.active ? "good" : "bad",
                ),
            ],
            [
              "Thao tác",
              (x) =>
                x.id === user.id
                  ? "Tài khoản hiện tại"
                  : `<button data-active="${esc(x.id)}" data-state="${x.active ? 0 : 1}">${x.active ? "Khóa tài khoản" : "Mở khóa"}</button>`,
            ],
          ],
          state.rows,
        ),
      ) +
      panel(
        "Cấp tài khoản",
        `<form id="user-form" class="panel-body form-grid"><label>Tên đăng nhập<input name="username" required></label><label>Họ tên<input name="name" required></label><label>Mật khẩu ban đầu<input name="password" type="password" minlength="12" autocomplete="new-password" required></label><label>Vai trò<select name="role">${["analyst", "approver", "viewer", "integration", "admin"].map((x) => `<option value="${x}">${words[x]}</option>`).join("")}</select></label><button class="primary">Tạo tài khoản</button><p id="user-result" role="alert"></p></form>`,
      );
  } else if (route === "audit") {
    html = panel(
      "Sự kiện gần nhất",
      table(
        [
          ["Thời điểm UTC", (x) => esc(x.created.slice(0, 19))],
          ["Người thực hiện", (x) => esc(x.actor)],
          ["Hành động", (x) => esc(x.action)],
          ["Đối tượng", (x) => esc(x.target)],
          [
            "Chi tiết",
            (x) =>
              `<details><summary>Xem nội dung</summary><pre>${esc(JSON.stringify(JSON.parse(x.detail), null, 2))}</pre></details>`,
            "text",
          ],
        ],
        state.rows,
      ),
      "Tối đa 1.000 sự kiện gần nhất",
    );
  } else if (route === "settings") {
    html =
      panel(
        "Tài khoản hiện tại",
        `<div class="panel-body"><p>${esc(user.name)} · ${esc(user.username)} · ${esc(words[user.role])}</p><form id="password-form" class="form-grid"><label>Mật khẩu hiện tại<input name="old" type="password" autocomplete="current-password" required></label><label>Mật khẩu mới<input name="new" type="password" minlength="12" autocomplete="new-password" required></label><button class="primary">Đổi mật khẩu</button></form></div>`,
      ) +
      panel(
        "Phương pháp và phạm vi",
        `<div class="panel-body"><p class="muted">${esc(a.method)}</p><p class="muted">LTV margin = dư nợ / TSBĐ sau haircut. Bổ sung TSBĐ = max(0, dư nợ / LTV tối đa − TSBĐ đã chiết khấu). Thanh khoản giả định bán tối đa 10% ADV/ngày. Tỷ lệ vốn khả dụng = vốn khả dụng / tổng giá trị rủi ro; các cấu phần nhập từ nguồn đã kiểm soát. Ứng dụng không tự tính trọng số pháp lý.</p><p class="muted">Dữ liệu khởi tạo minh họa được ghi rõ trong nguồn. Vận hành chính thức cần đối soát dữ liệu, kiểm định mô hình và cấu hình hạn mức nội bộ.</p></div>`,
      );
  }
  $("#content").innerHTML = html;
  bind();
}
function breaches(a) {
  return panel(
    "Vi phạm cần theo dõi",
    table(
      [
        ["Hạn mức", (x) => esc(x.name)],
        ["Chỉ tiêu", (x) => esc(words[x.metric])],
        ["Quan sát", (x) => num(x.actual)],
        ["Ngưỡng", (x) => num(x.threshold)],
        ["Mức độ", (x) => badge(x.severity, "bad")],
        ["Phụ trách", (x) => esc(x.owner)],
      ],
      a.breaches,
    ),
  );
}
function recordPage(kind) {
  let rows = state.rows;
  const source = {
    positions: state.analytics.positions,
    margin: state.analytics.margin,
    counterparties: state.analytics.counterparties,
  };
  if (source[kind]) rows = source[kind];
  let cols = Object.keys(schema[kind]).map((k) => [
    labels[k] || k,
    (x) => (typeof x[k] === "number" ? num(x[k]) : esc(words[x[k]] || x[k])),
    ["notes", "title"].includes(k) ? "text" : "",
  ]);
  if (kind === "positions")
    cols.push(
      ["Tỷ trọng", (x) => num(x.weight) + "%"],
      ["Thoái vốn (ngày)", (x) => num(x.days, 1)],
    );
  if (kind === "margin")
    cols.push(
      ["LTV", (x) => num(x.ltv) + "%"],
      ["TSBĐ cần bổ sung", (x) => num(x.call)],
      [
        "Cảnh báo",
        (x) =>
          x.breach
            ? badge("Cần bổ sung", "bad")
            : badge("Trong hạn mức", "good"),
      ],
    );
  if (kind === "counterparties")
    cols.push(
      ["Sử dụng HM", (x) => num(x.utilization) + "%"],
      [
        "Trạng thái",
        (x) =>
          badge(
            x.breach ? "Vượt hạn mức" : "Trong hạn mức",
            x.breach ? "bad" : "good",
          ),
      ],
    );
  if (canWrite())
    cols.push([
      "Thao tác",
      (x) => `<button data-edit="${esc(x.id)}">Đề nghị sửa</button>`,
    ]);
  let extra = "";
  if (kind === "cashflows")
    extra = panel(
      "Dòng tiền lũy kế",
      table(
        [
          ["Ngày", (x) => esc(x.date)],
          ["Tiền vào", (x) => num(x.inflow)],
          ["Tiền ra", (x) => num(x.outflow)],
          [
            "Số dư sau dòng tiền",
            (x) =>
              `<strong class="${x.balance < 0 ? "negative" : "positive"}">${num(x.balance)}</strong>`,
          ],
        ],
        state.analytics.cashflows,
      ),
    );
  if (kind === "limits") extra = breaches(state.analytics);
  if (kind === "capital" && state.analytics.capital)
    extra = kpis([
      ["Vốn khả dụng", num(state.analytics.capital.available), "Tỷ VND"],
      ["Tổng rủi ro", num(state.analytics.capital.total), "Tỷ VND"],
      [
        "Tỷ lệ vốn khả dụng",
        num(state.analytics.capital.far) + "%",
        "Cấu phần nhập đã duyệt",
      ],
      [
        "Ngày dữ liệu",
        state.analytics.capital.date,
        "Cần đối soát với báo cáo nguồn",
      ],
    ]);
  return (
    extra +
    `<div class="toolbar"><input id="search" type="search" placeholder="Tìm trong dữ liệu…" aria-label="Tìm trong dữ liệu"><button data-export="${kind}">Xuất CSV ↓</button></div><div id="data-table">${panel("Dữ liệu đã phê duyệt", table(cols, rows), rows.length + " bản ghi")}</div>`
  );
}
function openEditor(kind, row) {
  editing = { kind, row };
  $("#dialog-title").textContent =
    (row ? "Đề nghị sửa · " : "Thêm mới · ") + (pages[kind]?.[0] || kind);
  $("#form-error").textContent = "";
  $("#fields").innerHTML = Object.entries(schema[kind])
    .map(
      ([key, type]) =>
        `<label>${esc(labels[key] || key)}${Array.isArray(type) ? `<select name="${key}">${type.map((v) => `<option value="${v}" ${row?.[key] === v ? "selected" : ""}>${esc(words[v] || v)}</option>`).join("")}</select>` : key === "notes" ? `<textarea name="${key}" required>${esc(row?.[key] || "")}</textarea>` : `<input name="${key}" required ${["number", "positive", "strictpositive", "ratio"].includes(type) ? `type="number" step="any" ${type !== "number" ? 'min="0"' : ""} ${type === "ratio" ? 'max="1"' : ""}` : type === "date" ? 'type="date"' : 'maxlength="2000"'} value="${esc(row?.[key] ?? "")}">`}</label>`,
    )
    .join("");
  $("#editor").showModal();
}
async function download(url) {
  const r = await fetch("/api/" + url);
  if (!r.ok) {
    toast("Không thể tải tệp");
    return;
  }
  const blob = await r.blob();
  save(blob, url.split("/").pop() + ".csv");
}
function save(blob, name) {
  const u = URL.createObjectURL(blob),
    a = document.createElement("a");
  a.href = u;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(u), 1000);
}
function bind() {
  document.querySelectorAll("[data-active]").forEach(
    (b) =>
      (b.onclick = async () => {
        try {
          await api("users/" + b.dataset.active + "/active", {
            method: "POST",
            body: JSON.stringify({ active: b.dataset.state === "1" }),
          });
          toast("Đã cập nhật quyền truy cập");
          await navigate();
        } catch (e) {
          toast(e.message);
        }
      }),
  );
  document.querySelectorAll("[data-edit]").forEach(
    (b) =>
      (b.onclick = () =>
        openEditor(
          route,
          state.rows.find((r) => r.id === b.dataset.edit),
        )),
  );
  document
    .querySelectorAll("[data-export]")
    .forEach((b) => (b.onclick = () => download("export/" + b.dataset.export)));
  document.querySelectorAll("[data-decide]").forEach(
    (b) =>
      (b.onclick = async () => {
        const reason = prompt(
          "Nhập lý do " +
            (b.dataset.value === "approve" ? "phê duyệt" : "từ chối") +
            ":",
        );
        if (!reason?.trim()) return;
        b.disabled = true;
        try {
          await api(`approvals/${b.dataset.decide}/${b.dataset.value}`, {
            method: "POST",
            body: JSON.stringify({ reason }),
          });
          toast("Đã ghi nhận quyết định");
          await navigate();
        } catch (e) {
          toast(e.message);
          b.disabled = false;
        }
      }),
  );
  if ($("#search"))
    $("#search").oninput = (e) => {
      const q = e.target.value.toLocaleLowerCase();
      document
        .querySelectorAll("#data-table tbody tr")
        .forEach(
          (tr) => (tr.hidden = !tr.textContent.toLocaleLowerCase().includes(q)),
        );
    };
  if ($("#confidence"))
    $("#confidence").onchange = (e) => {
      confidence = Number(e.target.value);
      navigate();
    };
  if ($("#stress-form"))
    $("#stress-form").onsubmit = (e) => {
      e.preventDefault();
      const f = new FormData(e.target);
      shock = Number(f.get("shock")) / 100;
      rate = Number(f.get("rate")) / 100;
      navigate();
    };
  if ($("#template"))
    $("#template").onclick = () =>
      download("template/" + $("#import-kind").value);
  if ($("#import-file"))
    $("#import-file").onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      try {
        if (file.size > 2000000) throw Error("Tệp vượt quá 2 MB");
        const r = await api("import/" + $("#import-kind").value, {
          method: "POST",
          headers: {
            "Content-Type": "text/csv",
            "Idempotency-Key": crypto.randomUUID(),
          },
          body: await file.text(),
        });
        $("#import-result").textContent =
          `Đã kiểm tra và gửi ${r.count} dòng chờ phê duyệt.`;
      } catch (err) {
        $("#import-result").textContent = err.message;
      }
      e.target.value = "";
    };
  if ($("#snapshot"))
    $("#snapshot").onclick = async () => {
      try {
        const report = await api("report");
        save(
          new Blob([JSON.stringify(report, null, 2)], {
            type: "application/json",
          }),
          "risk-report-" + new Date().toISOString().slice(0, 10) + ".json",
        );
      } catch (e) {
        toast(e.message);
      }
    };
  if ($("#print")) $("#print").onclick = () => window.print();
  if ($("#user-form"))
    $("#user-form").onsubmit = async (e) => {
      e.preventDefault();
      try {
        await api("users", {
          method: "POST",
          body: JSON.stringify(Object.fromEntries(new FormData(e.target))),
        });
        toast("Đã tạo tài khoản");
        await navigate();
      } catch (err) {
        $("#user-result").textContent = err.message;
      }
    };
  if ($("#password-form"))
    $("#password-form").onsubmit = async (e) => {
      e.preventDefault();
      try {
        await api("password", {
          method: "POST",
          body: JSON.stringify(Object.fromEntries(new FormData(e.target))),
        });
        showLogin();
        toast("Đã đổi mật khẩu. Vui lòng đăng nhập lại.");
      } catch (err) {
        toast(err.message);
      }
    };
}
$("#record-form").onsubmit = async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target));
  Object.entries(schema[editing.kind]).forEach(([k, t]) => {
    if (["number", "positive", "strictpositive", "ratio"].includes(t))
      data[k] = Number(data[k]);
  });
  const button = e.target.querySelector("[type=submit]");
  button.disabled = true;
  try {
    await api("records/" + editing.kind, {
      method: "POST",
      body: JSON.stringify({
        data,
        id: editing.row?.id,
        version: editing.row?.version || 0,
      }),
    });
    $("#editor").close();
    toast("Đã gửi đề nghị. Mở Phê duyệt để theo dõi.");
  } catch (err) {
    $("#form-error").textContent = err.message;
  } finally {
    button.disabled = false;
  }
};
$("#close-dialog").onclick = $("#cancel-dialog").onclick = () =>
  $("#editor").close();
$("#menu").onclick = () => {
  const open = document.body.classList.toggle("nav-open");
  $("#menu").setAttribute("aria-expanded", String(open));
};
$("#logout").onclick = async () => {
  await api("logout", { method: "POST" });
  showLogin();
};
$("#login-form").onsubmit = async (e) => {
  e.preventDefault();
  const button = e.target.querySelector("button");
  button.disabled = true;
  $("#login-error").textContent = "";
  try {
    const data = await api("login", {
      method: "POST",
      body: JSON.stringify(Object.fromEntries(new FormData(e.target))),
    });
    csrf = data.csrf;
    e.target.reset();
    await start();
  } catch (err) {
    $("#login-error").textContent = err.message;
  } finally {
    button.disabled = false;
  }
};
window.addEventListener("hashchange", () => {
  if (user) navigate();
});
start().catch(() => showLogin());
