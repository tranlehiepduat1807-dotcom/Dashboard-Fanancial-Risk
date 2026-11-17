# Visual refresh — 17/11/2026

Enterprise workspace. Operational dashboard using a navy navigation rail, light neutral canvas, teal actions, local Geist typography and semantic amber/red risk states. No real company logo or investment data was invented.

## Verified behavior

- Enterprise: 21 API tests pass, including preservation of selected confidence in exported reports.
- Enterprise browser regression on an isolated synthetic DB: 15 modules, command search/Ctrl+K, sorting, filtering, pagination and no-result state, decision modal with persisted rejection, form help and mobile navigation.
- Responsive checks at 320, 390, 768, 1024 and visual inspection at 1440px. No page-level overflow or JavaScript exception in the tested routes. Data tables deliberately scroll internally.
- Sites: numerical engine tests pass; module navigation and responsive smoke checks pass. Changes there are visual and chart colours; the enterprise server is a separate local application.
- Existing user passwords were not reset. The isolated QA database and credentials are ignored by Git and excluded from production packaging.

## Design gate limitations

The marketing-layout gate remains OPEN (16 findings), not PASS. It checked the Enterprise login page without authenticating, and the Sites dashboard. Full-screen promotional hero, creative moments, .wrap/section-height rules, closing CTAs and decorative visuals in numerical cards do not match this operational product. No formal waivers were applied. Authenticated interaction checks are separate; this is not a claim of complete accessibility conformance.

After the gate, the low-contrast login helper text and light focus outlines were darkened. The full marketing gate was not rerun after those targeted corrections. All original findings remain listed below for traceability.

## Recorded open findings

- **text-contrast** — form#login-form > p:nth-of-type(1) "Dùng tài khoản được quản trị viên cấp." — a caption, label or muted line in #7c8e90 on #f7f9f8 reads 3.24:1 (needs 4.5:1)
- **text-contrast** — form#login-form > small "Dữ liệu lưu trên máy chủ của tổ chức. Li" — a caption, label or muted line in #899999 on #f7f9f8 reads 2.81:1 (needs 4.5:1)
- **focus-visible** — a.skip "Đến nội dung chính" — Tab stop 1, a "Đến nội dung chính": its focus change is faint: 2.09:1 against the ground, 3:1 needed
- **focus-visible** — form#login-form > label:nth-of-type(1) > input — Tab stop 2, input "": its focus change is faint: 2.58:1 against the ground, 3:1 needed
- **focus-visible** — form#login-form > label:nth-of-type(2) > input — Tab stop 3, input "": its focus change is faint: 2.58:1 against the ground, 3:1 needed
- **focus-visible** — form#login-form > button.primary:nth-of-type(1) "Vào không gian làm việc →" — Tab stop 4, button "Vào không gian làm việc →": its focus change is faint: 2.13:1 against the ground, 3:1 needed
- **moment-none** — (the page) — a software page (--type) deals no moment: every kind carries one, two on a long page (moments.md)
- **hero-screen** — body — no sections found: nothing in <main>, or at the top of the page, to measure (SR-1)
- **section-height** — body — no sections found: nothing in <main>, or at the top of the page, to measure (SR-2)
- **section-air** — body — no sections found: nothing in <main>, or at the top of the page, to measure (SR-3)
- **one-section** — body — no sections found: nothing in <main>, or at the top of the page, to measure (SR-4)
- **one-heading** — body — no sections found: nothing in <main>, or at the top of the page, to measure (SR-5)
- **container-edges** — body — no sections found: nothing in <main>, or at the top of the page, to measure (SR-6)
- **row-lines** — body — no sections found: nothing in <main>, or at the top of the page, to measure (SR-7)
- **split-pair** — body — no sections found: nothing in <main>, or at the top of the page, to measure (SR-8)
- **container** — page — no .wrap
