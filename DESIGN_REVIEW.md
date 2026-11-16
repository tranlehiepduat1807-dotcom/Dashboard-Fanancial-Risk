GATE: OPEN 38 (rounds used up)

# Enterprise redesign · 16/11/2026

## Design system

White surfaces, cool-gray canvas, navy text; blue #1a4be0 for actions and selected navigation. Amber/red are reserved for risk states. Geist is hosted locally with its OFL license. Body 14px, labels 12–13px, panel headings 16–17px, page headings 26–28px; tabular numerals align monetary values. Borders and a 6/8px control/panel radius replace mixed decorative treatments. Desktop sidebar and collapsible mobile navigation share accessible focus and current-page states.

The existing product is an operational dashboard. Its tables, multiple analytical panels, chart legends and numerical emphasis are retained. The dealt palette was white-link-blue (the first dark palette conflicted with the existing light application); type pairing Geist, using the sans family for readability. No stock photography, invented customer evidence, scene, full-screen marketing hero or promotional animation was introduced. Data remains explicitly simulated. No third-party brand logo was copied.

## Verification

- Browser renders inspected at 1440px and 390px; module review galleries cover every main view.
- Sites: 15 interaction checks pass; existing numerical tests pass; JavaScript syntax passes.
- GitHub: 19 interaction checks pass (five modules/charts, date presets, detail drawer and mobile navigation).
- GitHub: all three original inline script blocks, including data and financial calculations, match the baseline byte-for-byte after text decoding. Presentation code adds a responsive segmented-chart legend.
- The checker reports no collision, page overflow or focus-visibility FAIL on either application. Internal data tables intentionally scroll horizontally and vertically.
- Desktop/mobile performance checks are recorded separately below when complete.

## Gate interpretation and remaining findings

The landing-page gate is OPEN, not PASS. It also applies promotional-page constraints (full-screen hero, visual ratios, closing CTA, no chart captions, number sizes below headings, .wrap grid) to a data application. Those constraints were not used to replace the requested enterprise dashboard. The subtitle contrast on Sites is 5.58:1 (above WCAG AA for normal text, below this skill's stricter 7:1 body target). No formal waivers were applied. Scrollable table clips and deliberate KPI hierarchy remain identified by the marketing checker; they are disclosed rather than hidden from it.

- cut-text | table.dt > tbody > tr:nth-of-type(4) > td.w:nth-of-type(5) "Đang áp mức tăng giá trị rủi ro 20% cho " | 1 of 3 lines hidden by the overflow of section#v-overview > div.panel.flush > div.tblwrap
- no-visual | section#v-overview "Điều kiện bù trừ CKPS" | pictures, effects and mocks cover 12% of this section; a feature section needs a visual (about 25% or more)
- card-visual | section#v-overview > section.panel.ckps > div.ck-grid "FAR hiện tại 176,19% Khoảng cách đến 260" | 5 cards hold only text: no picture, icon, UI fragment or effect in any of them
- card-visual | section#v-overview > div.panel.rail "Vốn khả dụng 8.662,1 Chi tiết vốn khả dụ" | 6 cards hold only text: no picture, icon, UI fragment or effect in any of them
- cta | section#v-overview | the hero has no button (the nav's does not count)
- copy-headline | h1#pgTitle "Tổng quan ATTC" | "Tổng quan ATTC" does not name what is sold (rui ro, rui, from flags); only the line under it does
- copy-headings | div.grid.g-58 > div.panel > div.phead > h2 "Diễn biến tỷ lệ vốn khả dụng" | "Diễn biến tỷ lệ vốn khả dụng" names no product, part, place or section (2 headings like it; at most one brand line per page) (and 1 more like it: "Danh sách cảnh báo sớm")
- heading-scale | div.grid.g-hero > div.panel.hero > div.hero-val > span.n "176,19%" | the figure "176,19%" is set at 46px, larger than the h1 (27px) (and 1 more like it: "-187,1 tỷ")
- heading-scale | section.panel.ckps > div.ck-grid > div.ck-tile:nth-of-type(1) > strong "176,19%" | the figure "176,19%" is set at 25px, larger than the section headings (h2 17px); 8 more like it
- text-contrast | nav#nav > a:nth-of-type(2) > i "02" | a caption, label or muted line in #637992 on #ffffff reads 4.49:1 (needs 4.5:1); 4 like it, like "03", "04", "05"
- text-contrast | span#srcName "ATTC_sample_data" | a caption, label or muted line in #ffffff on #ffffff reads 1:1 (needs 4.5:1)
- links | nav#nav > a.on "01 Tổng quan ATTC" | "01 Tổng quan ATTC" goes to #/overview, which is not on this page
- links | nav#nav > a:nth-of-type(2) "02 Rủi ro thị trường" | "02 Rủi ro thị trường" goes to #/market, which is not on this page
- links | nav#nav > a:nth-of-type(3) "03 Rủi ro thanh toán" | "03 Rủi ro thanh toán" goes to #/settlement, which is not on this page
- links | nav#nav > a:nth-of-type(4) "04 Tập trung & tín nhiệm" | "04 Tập trung & tín nhiệm" goes to #/concentration, which is not on this page
- links | nav#nav > a:nth-of-type(5) "05 Kiểm tra sức chịu đựng & cảnh báo sớm" | "05 Kiểm tra sức chịu đựng & cảnh báo sớm" goes to #/stress, which is not on this page
- links | section#v-overview > section.panel.ckps > a.ck-detail-link "Phân tích điều kiện bù trừ CKPS →" | "Phân tích điều kiện bù trừ CKPS →" goes to #/stress, which is not on this page
- field-label | input#fromInput | a input[type=date] without a label you can see: only an aria-label names it
- field-label | input#toInput | a input[type=date] without a label you can see: only an aria-label names it
- hero-screen | section#v-overview "Tỷ lệ vốn khả dụng Dưới 180% 176,19% ngư" | the hero ends at 2271px on a 900px screen, 1371px below the fold: it ends at the fold, 1px either way (SR-1)
- section-height | section#v-overview "Tỷ lệ vốn khả dụng Dưới 180% 176,19% ngư" | the section starts at 143px, 143px below the screen grid (0 x 900px): sections start on whole screens (SR-2)
- one-section | section#v-overview > section.panel.ckps "Điều kiện bù trừ CKPSKhông đáp ứng điều " | a band: a box 95% of the section wide on a ground of its own that holds the heading or the intro: the section's own ground is the band (SR-4)
- one-heading | section#v-overview > section.panel.ckps > div.phead > h2 "Điều kiện bù trừ CKPS" | the hero holds an h2 (5): its heading is the h1, and an h2 opens the next section (SR-5)
- container-edges | div#app > div.main > header.topbar "Tổng quan ATTC Vốn khả dụng, cơ cấu rủi " | the nav's content runs 280px from the left and 32px from the right (read from its outermost blocks: no .wrap): 280 and 32px are not one margin; the margin is 64-120px at 1440px (one container, equal margins, 2px either way) (SR-6)
- container-edges | section#v-overview "Tỷ lệ vốn khả dụng Dưới 180% 176,19% ngư" | the content of section 1 runs 280px from the left and 32px from the right (read from its outermost blocks: no .wrap): 280 and 32px are not one margin; the margin is 64-120px at 1440px (one container, equal margins, 2px either way) (SR-6)
- container-edges | a.skip-enterprise "Đến nội dung" | a <a> at the top of the page, outside header.nav, main, footer.closing and nav.actionbar (SR-6)
- container-edges | div#app "R/MRisk ManagementAn toàn tài chính Menu" | a <div> at the top of the page, outside header.nav, main, footer.closing and nav.actionbar (SR-6)
- container-edges | div.stack > div.panel:nth-of-type(1) > div.phead > h2 "Tỷ trọng rủi ro hiện tại" | the h2 starts 649px right of the container's left: every h1 and h2 starts on it, 2px either way (SR-6)
- container-edges | div.stack > div.panel:nth-of-type(2) > div.phead > h2 "Cấu phần rủi ro theo thời gian" | the h2 starts 649px right of the container's left: every h1 and h2 starts on it, 2px either way (SR-6)
- container-edges | section#v-overview > section.panel.ckps > div.ck-action > b "Ưu tiên xử lý" | 1 text block starts on a left line at x 324, 44px from the container's left: text starts on the container's left, or on one split line (x 760, 856, 952) (and 4 more like it: x 305, "Điều kiện bù trừ CKPS", "Diễn biến tỷ lệ vốn khả ") (SR-6)
- row-lines | section#v-overview > section.panel.ckps > div.ck-grid "FAR hiện tại176,19%Khoảng cách đến 260%−" | a row of 5 items: its first item starts at 305px, the container's left line at 280px; its last item ends at 1383px, the container's right line at 1408px (2px either way) (SR-7)
- row-lines | section#v-overview > section.panel.ckps > div.ck-two.ck-alerts "ATTC · 180%Dưới ngưỡng ATTCBù trừ CKPS ·" | a row of 2 items: its first item starts at 305px, the container's left line at 280px; its last item ends at 1383px, the container's right line at 1408px (2px either way) (SR-7)
- row-lines | section#v-overview > div.panel.flush > div.tblwrap "Mức độNhómTín hiệuGiá trị quan sátNguyên" | a sideways scroller: 214px of it hidden behind overflow-x: auto (SR-7)
- split-pair | section#v-overview > div.grid.g-58 "Diễn biến tỷ lệ vốn khả dụng 60 phiên, 2" | the split's columns are off the page's one pair of lines: its right column starts at x 904, on none of the split lines 760 (k=5), 856 (k=6), 952 (k=7) (SR-8)
- row-gap | section#v-overview > section.panel.ckps > div.ck-grid > div.ck-tile:nth-of-type(5) "Điều kiện liên tục Chuỗi bị đứt" | stretched alone across the last row (320px) while the 2 like it above are 152px
- cut-text | tbody > tr:nth-of-type(1) > td:nth-of-type(3) > span.strong "Tỷ lệ ATTC dưới 180%" | runs past the edge of its box section#v-overview > div.panel.flush (and 3 more like it: "Vượt hạn mức nội bộ: Ven", "Tạm ứng ≥5% VCSH: Strate", "Tập trung tổ chức phát h")
- heading-scale | section#v-overview > div.panel.rail > div.m:nth-of-type(1) > div.v "8.662,1" | the figure "8.662,1" is set at 24px, larger than the section headings (h2 16px); 5 more like it
- container | page | no .wrap

## Final performance and scope
Font files were compressed to WOFF2, 112,148 bytes total. Font-weight, broken-request and layout-shift checks pass. The performance script still flags total transfer (4,621.7 KiB in its accounting), driven by the existing HTML with embedded data/Excel content. CPU-load warnings mean timing results should not be treated as production guarantees. This redesign preserves the original data payload; it does not claim to fix data-delivery architecture. The metric rail was subsequently balanced to fit all seven market metrics without an orphan row. Final galleries and interaction QA were rerun.
