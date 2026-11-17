# TCBS iFlash OpenAPI — read-only integration

Implemented from user-supplied `tcbs-openapi-v1.0.0-vi.pdf` (50 pages), reviewed on 17/11/2026. The PDF itself is not copied into the public repository. Official base URL was verified against https://developers.tcbs.com.vn/docs/v1.0.0/introduction/ : https://openapi.tcbs.com.vn.

## Available functions

- `GET /api/tcbs/status`: authenticated capability/configuration status; never returns a token.
- `POST /api/tcbs/preview`: admin/analyst/integration can preview sample data, uploaded JSON, or live GET results. Stores a per-user normalized snapshot, not API keys/OTP/JWT.
- `POST /api/tcbs/snapshots/{id}/submit`: sends non-demo daily-price snapshots into the existing maker/checker workflow. Known identical prices are skipped; changed prices use existing record IDs and versions. Own snapshot access only; repeat submissions rejected. Audit links snapshot, source and approval IDs.

| Resource | Official endpoint | PDF pages |
|---|---|---|
| assets | GET /aion/v1/accounts/{accountNo}/se | 18 |
| cash | GET /aion/v1/accounts/{accountNo}/cashInvestments | 18–19 |
| risk | GET /hydros/v1/account/{accountNo}/risk | 15–16 |
| quotes | GET /tartarus/v1/tickerCommons | 21–22 |
| history | GET /nyx/v2/stock/bars-long-term | 35 |

Each resource has explicit shape validation. Monetary balances/marketValue are converted under the VND source-unit assumption into billions of VND; verify units against real responses before use. Prices remain in source units. Rtt and risk-policy values remain provider values; no Rtt→LTV conversion is assumed. Account-level iFlash data is not a replacement for an enterprise-wide FSS FLEX feed.

## Current connection status

The user has documentation only, without an API Key. No real TCBS calls, API-key exchange, OTP handling or automatic refresh have been performed. MockTransport tests verify GET construction and error handling; browser tests use synthetic data. No live-provider certification is claimed.

After iFlash is enabled and an API key exists, follow TCBS's documented exchange (PDF p.4) using API Key + Smart OTP to obtain a JWT. The application accepts a `TCBS_BEARER_TOKEN` environment variable on the server; start/restart the application under that environment. Do not paste credentials into chat, commit them, put them in URLs, or use the JSON upload box for them. The portal's API key + OTP exchange requires a separate authorized user action; it is not implemented by this update. The configured JWT is shared at the server integration level, so grant the read-preview roles only to the intended team. Expired/revoked token errors are displayed without exposing the upstream response/token. No token refresh is automatic.

The HTTP client uses the fixed official origin, no user-provided URL, no redirects, 15-second timeout, GET-only endpoint allowlist and a bounded response check. Account/symbol path parameters are validated. The HTTP request runs outside the event loop. It never implements order placement/cancellation, cash transfers or derivative transactions.

## History and model controls

- Only daily stock bars (`resolution=D`, `type=stock`) are fetched; 1–500 bars per request.
- Convert timezone-aware tradingDate to Asia/Ho_Chi_Minh, reject duplicate dates, non-positive/non-finite closes and the current/future day to avoid incomplete bars.
- Uploaded JSON is explicitly labelled unverified-source; sample data cannot be submitted.
- Price approval does not automatically create portfolio positions. Beta, sector/book, ADV and instrument characteristics require reviewed input. No invented default risk parameters are inserted.
- Snapshot quotes and uploaded prices are not corporate-action-adjusted by this application. Price adjustments, price-unit reconciliation, completeness, calendar alignment and licensed data entitlements still need provider/UAT validation.
- Cash responses whose totalCount exceeds the returned rows are rejected rather than silently using a partial page. The supplied cash endpoint spec does not document request pagination parameters; automatic pagination has not been guessed.
- No WebSocket streaming, scheduling, source-switch for existing demo positions or historical backfill automation is included.

## Verification

30 API tests pass, including TCBS unit conversion, Rtt preservation, viewer/CSRF permissions, missing-token behavior, invalid inputs, isolation of snapshots, submit idempotence, maker/checker approval, mocked live GET and error redaction. Browser checks cover five sample resources, disabled live mode with no token, centered numeric data, malformed JSON errors, history submit, no JS exceptions and no page overflow at 320/390/768/1024/1440px. One existing Starlette/httpx test-client deprecation warning remains.
