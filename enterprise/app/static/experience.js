/* Presentation and navigation layer. Financial calculations remain in the API. */
const navPaths = {
  overview: "M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z",
  positions: "M3 7h18v14H3z M8 7V3h8v4 M3 12h18 M10 12v3h4v-3",
  market: "M3 20V4 M3 20h18 M6 15l5-6 4 3 6-7",
  stress: "M3 16l4-5 4 8 4-15 3 8h3",
  margin: "M3 5h18v14H3z M3 9h18 M7 15h4",
  counterparties:
    "M3 21v-9h7v9 M14 21V3h7v18 M6 15h1 M17 7h1 M17 11h1 M17 15h1",
  cashflows: "M3 7h15 M14 3l4 4-4 4 M21 17H6 M10 13l-4 4 4 4",
  capital: "M12 3l9 4v6c0 5-9 9-9 9s-9-4-9-9V7z M8 12l3 3 5-6",
  limits: "M12 3L2 21h20z M12 9v5 M12 17v1",
  incidents: "M5 3h14v18H5z M9 7h6 M9 11h6 M9 15h3",
  approvals: "M5 3h14v18H5z M8 12l3 3 5-6",
  reports: "M4 3h11l5 5v13H4z M14 3v6h6 M8 13h8 M8 17h8",
  integration:
    "M7 7h10v10H7z M10 2v5 M14 2v5 M10 17v5 M14 17v5 M2 10h5 M17 10h5 M2 14h5 M17 14h5",
  users:
    "M8 11a4 4 0 1 0 0-8a4 4 0 0 0 0 8 M1 21v-3c0-5 14-5 14 0v3 M17 4a4 4 0 0 1 0 8 M18 15c4 0 5 2 5 6",
  audit: "M12 7v5l3 2 M21 12a9 9 0 1 1-3-7 M21 3v6h-6",
  settings: "M4 7h16 M4 17h16 M8 4v6 M16 14v6",
};
function navIcon(key) {
  return `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${navPaths[key] || navPaths.reports}"/></svg>`;
}
chart = function (values) {
  if (!values.length) return empty("Nhập lịch sử giá để xem phân tích.");
  const max = Math.max(0.01, ...values.map(Math.abs));
  return `<div class="chart-legend"><span><i></i>Lãi giả định</span><span><i class="loss"></i>Lỗ giả định</span><span>tỷ VND</span></div><div class="pnl-chart" role="img" aria-label="Lãi lỗ giả định theo lịch sử lợi suất; mốc giữa là 0, phía trên là lãi, phía dưới là lỗ. Đơn vị tỷ VND."><div class="pnl-grid">${[max, max / 2, 0, -max / 2, -max].map((v) => `<span><b>${num(v, 1)}</b></span>`).join("")}</div><div class="pnl-columns">${values.map((loss) => `<div title="${esc((loss > 0 ? "Lỗ: " : "Lãi: ") + num(Math.abs(loss)) + " tỷ")}"><i class="${loss > 0 ? "down" : ""}" style="height:${Math.max(0.5, (Math.abs(loss) / max) * 50)}%;${loss > 0 ? "top" : "bottom"}:50%"></i></div>`).join("")}</div></div><div class="chart-foot"><span>Đầu chuỗi hiển thị</span><span>${values.length} quan sát gần nhất</span><span>Cuối chuỗi</span></div>`;
};
function changeList(data) {
  return `<dl class="change-list">${Object.entries(data)
    .map(
      ([k, v]) =>
        `<div><dt>${esc(labels[k] || k)}</dt><dd>${esc(typeof v === "number" ? num(v) : words[v] || v)}</dd></div>`,
    )
    .join("")}</dl>`;
}
const baseRender = render;
render = function () {
  baseRender();
  const a = state.analytics;
  $("#title").textContent =
    route === "overview" ? "Tổng quan rủi ro" : pages[route][0];
  $("#data-context").innerHTML =
    `<div class="context-strip"><span><i class="status-dot"></i><strong>${a.sample_data ? "Dữ liệu minh họa" : "Dữ liệu nội bộ"}</strong> · ${a.price_asof ? "Ngày giá: " + esc(a.price_asof) : "Chưa có lịch sử giá"}</span><a href="#integration">Nguồn dữ liệu ↗</a></div>`;
  document.querySelectorAll("#nav a").forEach((link) => {
    const span = link.querySelector("span");
    if (span) span.innerHTML = navIcon(link.dataset.route);
    link.onclick = () => {
      document.body.classList.remove("nav-open");
      $("#menu").setAttribute("aria-expanded", "false");
    };
  });
  if (route === "overview") {
    $("#page-actions").insertAdjacentHTML(
      "beforeend",
      '<button class="primary" id="overview-report">Xuất báo cáo ↓</button>',
    );
    $("#overview-report").onclick = async () => {
      try {
        save(
          new Blob(
            [
              JSON.stringify(
                await api(
                  `report?confidence=${confidence}&shock=${shock}&rate=${rate}`,
                ),
                null,
                2,
              ),
            ],
            { type: "application/json" },
          ),
          "risk-report.json",
        );
      } catch (e) {
        toast(e.message);
      }
    };
    const groups = {};
    a.positions.forEach((x) => {
      const g = words[x.type] || x.type;
      groups[g] = (groups[g] || 0) + x.value;
    });
    $("#content").innerHTML =
      kpis([
        ["Tổng giá trị danh mục", num(a.nav), "tỷ VND · Vị thế đã phê duyệt"],
        [
          `VaR ${num(a.confidence * 100, Number.isInteger(a.confidence * 100) ? 0 : 1)}% · 1 ngày`,
          num(a.var),
          a.var == null
            ? "Chưa đủ lịch sử giá"
            : num(a.metrics.var_pct) + "% tổng giá trị danh mục",
        ],
        [
          "Vi phạm hạn mức",
          a.breaches.length,
          "Vượt ngưỡng chính sách nội bộ",
          a.breaches.length ? "negative" : "",
        ],
        [
          "Tài khoản cần bổ sung",
          a.margin.filter((x) => x.breach).length,
          "Tài sản bảo đảm sau chiết khấu",
          a.margin.some((x) => x.breach) ? "negative" : "",
        ],
      ]) +
      `<div class="overview-grid">${panel("Lãi lỗ theo lịch sử lợi suất", `<div class="panel-body">${chart(a.losses)}</div>`, a.var == null ? "Chưa đủ dữ liệu" : a.observations + " quan sát dùng tính VaR")}${panel(
        "Cơ cấu tài sản",
        `<div class="panel-body allocation">${
          Object.entries(groups)
            .map(
              ([name, value]) =>
                `<div><div class="allocation-line"><strong>${esc(name)}</strong><span>${num(value)} tỷ · ${num(a.nav ? (100 * value) / a.nav : 0, 1)}%</span></div><div class="track"><div style="width:${a.nav ? (100 * value) / a.nav : 0}%"></div></div></div>`,
            )
            .join("") || empty("Chưa có vị thế được phê duyệt.")
        }<div class="allocation-note"><span>${a.positions.length} vị thế trong danh mục</span><a href="#positions">Xem chi tiết ↗</a></div></div>`,
      )}</div>` +
      `<div class="section-caption"><h2>Không gian xử lý</h2><a href="#limits">Xem chính sách hạn mức ↗</a></div><section class="panel action-list">${[
        [
          "margin",
          "Tài sản bảo đảm",
          "Tài khoản cần bổ sung",
          a.margin.filter((x) => x.breach).length,
        ],
        [
          "counterparties",
          "Rủi ro đối tác",
          "Đối tác vượt hạn mức",
          a.counterparties.filter((x) => x.breach).length,
        ],
        [
          "cashflows",
          "Lịch dòng tiền",
          "Ngày dự kiến thiếu tiền",
          a.cashflows.filter((x) => x.balance < 0).length,
        ],
        ["approvals", "Phê duyệt thay đổi", "Mở hàng đợi xử lý", "→"],
      ]
        .map(
          ([key, title, note, value]) =>
            `<a href="#${key}" class="action-link"><span><strong>${title}</strong><small>${note}</small></span><span class="action-count ${typeof value === "number" && value > 0 ? "attention" : ""}">${value}</span></a>`,
        )
        .join("")}</section>` +
      breaches(a);
  }
  document
    .querySelectorAll(".kpi")
    .forEach((el, i) =>
      el.insertAdjacentHTML(
        "beforeend",
        `<span class="kpi-index">${String(i + 1).padStart(2, "0")}</span>`,
      ),
    );
  if (route === "approvals")
    document.querySelectorAll("td details").forEach((detail, i) => {
      const row = state.rows[i];
      if (row)
        detail.innerHTML = `<summary>Xem nội dung đề nghị</summary>${changeList(JSON.parse(row.data))}${row.reason ? `<p class="muted">Lý do: ${esc(row.reason)}</p>` : ""}`;
    });
  document
    .querySelectorAll("[data-decide]")
    .forEach(
      (b) =>
        (b.onclick = () => openDecision(b.dataset.decide, b.dataset.value)),
    );
  enhanceTables();
};
function enhanceTables() {
  document.querySelectorAll("#content table").forEach((t) => {
    let sortIndex = -1,
      ascending = true;
    const body = t.tBodies[0],
      isData = !!t.closest("#data-table");
    let page = 0;
    const size = 20,
      all = () => Array.from(body.rows);
    let footer;
    if (isData) {
      footer = document.createElement("div");
      footer.className = "table-pagination";
      t.closest(".panel").append(footer);
    }
    function apply() {
      const query =
        isData && $("#search")
          ? $("#search").value.toLocaleLowerCase().trim()
          : "";
      const matches = all().filter((r) =>
        r.textContent.toLocaleLowerCase().includes(query),
      );
      const pages = Math.max(1, Math.ceil(matches.length / size));
      page = Math.min(page, pages - 1);
      all().forEach((r) => (r.hidden = true));
      (isData
        ? matches.slice(page * size, (page + 1) * size)
        : matches
      ).forEach((r) => (r.hidden = false));
      if (footer) {
        footer.innerHTML = `<span>${matches.length ? `${page * size + 1}–${Math.min((page + 1) * size, matches.length)}` : "0"} / ${matches.length} bản ghi${!matches.length ? " · Không có kết quả phù hợp" : ""}</span><div><button type="button" class="prev" aria-label="Trang trước" ${page === 0 ? "disabled" : ""}>←</button><span>${page + 1} / ${pages}</span><button type="button" class="next" aria-label="Trang sau" ${page === pages - 1 ? "disabled" : ""}>→</button></div>`;
        footer.querySelector(".prev").onclick = () => {
          page--;
          apply();
        };
        footer.querySelector(".next").onclick = () => {
          page++;
          apply();
        };
      }
    }
    Array.from(t.tHead.rows[0].cells).forEach((th, index) => {
      if (["Thao tác", "Nội dung", "Chi tiết"].includes(th.textContent.trim()))
        return;
      const label = th.textContent;
      th.setAttribute("aria-sort", "none");
      th.innerHTML = `<button type="button" class="sort-column" aria-label="Sắp xếp theo ${esc(label)}">${esc(label)}</button>`;
      th.querySelector("button").onclick = () => {
        ascending = sortIndex === index ? !ascending : true;
        sortIndex = index;
        const rows = all();
        rows.sort((a, b) => {
          const x = a.cells[index].textContent.trim(),
            y = b.cells[index].textContent.trim();
          const numeric =
            /^[−-]?\d[\d.,]*%?$/.test(x) && /^[−-]?\d[\d.,]*%?$/.test(y);
          const toNumber = (s) =>
            Number(
              s
                .replace(/\./g, "")
                .replace(",", ".")
                .replace("%", "")
                .replace("−", "-"),
            );
          return (
            (numeric
              ? toNumber(x) - toNumber(y)
              : x.localeCompare(y, "vi", { numeric: true })) *
            (ascending ? 1 : -1)
          );
        });
        rows.forEach((r) => body.append(r));
        t.querySelectorAll("th").forEach((x) =>
          x.setAttribute("aria-sort", "none"),
        );
        th.setAttribute("aria-sort", ascending ? "ascending" : "descending");
        page = 0;
        apply();
      };
    });
    if (isData && $("#search"))
      $("#search").oninput = () => {
        page = 0;
        apply();
      };
    apply();
    all().forEach((r) =>
      Array.from(r.cells).forEach((cell) => {
        if (/^[−-]?\d[\d.,]*%?$/.test(cell.textContent.trim())) {
          cell.classList.add("numeric");
          t.tHead.rows[0].cells[cell.cellIndex]?.classList.add("numeric");
        }
      }),
    );
    // Apply alignment to the whole column, including blank/missing values.
    Array.from(t.tHead.rows[0].cells).forEach((header, index) => {
      if (header.classList.contains("numeric")) {
        all().forEach((row) => row.cells[index]?.classList.add("numeric"));
      }
    });
  });
}
let decisionTarget;
function openDecision(id, value) {
  const row = state.rows.find((x) => x.id === id);
  if (!row) return;
  decisionTarget = { id, value };
  $("#decision-title").textContent =
    value === "approve" ? "Phê duyệt đề nghị" : "Từ chối đề nghị";
  $("#decision-detail").innerHTML =
    `<p class="muted">${esc(pages[row.kind]?.[0] || row.kind)} · Người lập: ${esc(row.maker)}</p>${changeList(JSON.parse(row.data))}`;
  $("#decision-submit").textContent =
    value === "approve" ? "Xác nhận phê duyệt" : "Xác nhận từ chối";
  $("#decision-submit").className = value === "approve" ? "primary" : "danger";
  $("#decision-error").textContent = "";
  $("#decision-form").reset();
  $("#decision-dialog").showModal();
}
$("#decision-close").onclick = $("#decision-cancel").onclick = () =>
  $("#decision-dialog").close();
$("#decision-form").onsubmit = async (e) => {
  e.preventDefault();
  const reason = new FormData(e.target).get("reason").trim();
  if (!reason) {
    $("#decision-error").textContent = "Vui lòng nhập lý do quyết định.";
    return;
  }
  const button = $("#decision-submit");
  button.disabled = true;
  try {
    await api(`approvals/${decisionTarget.id}/${decisionTarget.value}`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    });
    $("#decision-dialog").close();
    toast("Đã ghi nhận quyết định.");
    await navigate();
  } catch (err) {
    $("#decision-error").textContent = err.message;
  } finally {
    button.disabled = false;
  }
};
function commandResults() {
  const query = $("#command-search")
    .value.normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
  const links = Array.from(document.querySelectorAll("#nav a")).filter((link) =>
    link.textContent
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .includes(query),
  );
  $("#command-results").innerHTML =
    links
      .map(
        (link) =>
          `<a href="${link.getAttribute("href")}">${esc(pages[link.dataset.route][0])}<small>${esc(pages[link.dataset.route][2])}</small></a>`,
      )
      .join("") || '<p class="empty">Không tìm thấy phân hệ phù hợp.</p>';
  $("#command-results")
    .querySelectorAll("a")
    .forEach((a) => (a.onclick = () => $("#command-dialog").close()));
}
function openCommand() {
  commandResults();
  $("#command-dialog").showModal();
  $("#command-search").focus();
}
$("#command-open").onclick = openCommand;
$("#command-close").onclick = () => $("#command-dialog").close();
$("#command-search").oninput = commandResults;
document.addEventListener("keydown", (e) => {
  if (
    (e.ctrlKey || e.metaKey) &&
    e.key.toLowerCase() === "k" &&
    !$("#workspace").hidden
  ) {
    e.preventDefault();
    openCommand();
  }
  if (
    e.key === "ArrowDown" &&
    document.activeElement === $("#command-search")
  ) {
    e.preventDefault();
    $("#command-results a")?.focus();
  }
});
const baseEditor = openEditor;
openEditor = function (kind, row) {
  baseEditor(kind, row);
  const hints = {
    value: "Nhập giá trị theo đơn vị tỷ VND.",
    adv: "Giá trị giao dịch bình quân một ngày, đơn vị tỷ VND.",
    haircut: "Ví dụ: 0,15 tương ứng mức chiết khấu 15%.",
    maintenance: "Ví dụ: 0,50 tương ứng LTV tối đa 50%.",
    beta: "Hệ số nhạy cảm với biến động thị trường.",
    duration: "Duration điều chỉnh, đơn vị năm.",
  };
  Object.entries(hints).forEach(([key, hint]) => {
    const input = $(`#fields [name="${key}"]`);
    if (input)
      input.insertAdjacentHTML(
        "afterend",
        `<small class="form-help">${hint}</small>`,
      );
  });
};
