## ADDED Requirements

### Requirement: Protected routes use a compatible secure server runtime
The docs application SHALL use a security-fixed Next.js/Fumadocs peer group
and execute the protected-route Proxy on the Node.js runtime while preserving
the existing admin and admin-API matcher surface.

#### Scenario: Production Proxy build
- **WHEN** the locked docs application is built for production
- **THEN** the Proxy bundle SHALL compile without an unsupported `node:crypto` import error and the production dependency audit SHALL contain no known vulnerability

#### Scenario: Protected route matching
- **WHEN** a request targets `/admin/:path*` or `/api/admin/:path*`
- **THEN** Proxy SHALL enforce the existing configured, authenticated, and unauthenticated route behavior

### Requirement: Telemetry storage mode is explicit
The docs application SHALL expose `disabled`, `filesystem`, and `redis` telemetry modes. Development SHALL default to `filesystem`; production SHALL default to `disabled`. Redis mode SHALL require explicit backend selection, complete credentials, and an injected approved adapter; until that optional adapter exists, Redis SHALL remain unavailable and SHALL NOT fall back to filesystem storage.

#### Scenario: Unconfigured production deployment
- **WHEN** the application runs in production without an explicitly selected, fully configured, injected Redis adapter
- **THEN** telemetry mode SHALL be `disabled` and no filesystem write SHALL be attempted

#### Scenario: Local development
- **WHEN** the application runs outside production without an explicit backend override
- **THEN** telemetry mode SHALL be `filesystem`

#### Scenario: Production filesystem override
- **WHEN** production explicitly requests the single-process filesystem backend
- **THEN** telemetry SHALL fail closed without reading or writing the configured path

### Requirement: Public behavior is independent of telemetry availability
Page, search, and other business routes SHALL preserve their primary response when telemetry is disabled or its configured backend fails.

#### Scenario: Search telemetry failure
- **WHEN** search succeeds and telemetry persistence fails
- **THEN** the search response SHALL still be returned successfully

#### Scenario: Disabled telemetry
- **WHEN** a route records an observation in disabled mode
- **THEN** the operation SHALL return a truthful zero-stored result without throwing

### Requirement: Telemetry ingestion reports truthful counts
The telemetry ingestion API SHALL report whether validated events were received and stored, together with the active mode.

#### Scenario: Disabled ingestion
- **WHEN** a valid batch containing three events is posted in disabled mode
- **THEN** the response SHALL report `received: 3`, `stored: 0`, and `mode: "disabled"`

#### Scenario: Malformed ingestion
- **WHEN** a request body is malformed or violates the accepted event contract
- **THEN** the API SHALL return status 400 without storing an event

#### Scenario: Enabled backend failure
- **WHEN** an enabled telemetry backend cannot persist an otherwise valid batch
- **THEN** the ingestion API SHALL return status 503 rather than describing the payload as invalid

### Requirement: Production admin readiness includes distributed throttling
Production admin access SHALL require valid password/session configuration and an approved distributed rate limiter. An in-memory limiter SHALL be selectable only outside production.

#### Scenario: Credentials without distributed limiter
- **WHEN** production credentials are valid but no distributed limiter is configured
- **THEN** protected admin routes SHALL report service unavailable

#### Scenario: Local limiter
- **WHEN** local development uses the in-memory limiter
- **THEN** five attempts within sixty seconds SHALL be allowed according to the configured contract and subsequent attempts SHALL be rejected until expiry

#### Scenario: Distributed limiter outage
- **WHEN** the production limiter backend is unavailable
- **THEN** a JSON admin-login client SHALL fail closed with status 503 and an HTML form client SHALL receive a 303 redirect to the bounded unavailable UI without a session

### Requirement: Admin login responses are explicitly negotiated
Admin login SHALL select HTML or JSON behavior from the request `Accept`
header. Explicit HTML navigation SHALL use POST/Redirect/GET. Missing,
wildcard-only, malformed, zero-quality HTML, or JSON-preferred requests SHALL
use the JSON API representation.

#### Scenario: Browser login failure
- **WHEN** an explicit HTML client is invalid, rate-limited, unavailable, or encounters a bounded server failure
- **THEN** the response SHALL be a 303 same-origin redirect containing only a bounded error code and sanitized admin destination

#### Scenario: JSON login result
- **WHEN** a JSON/default client submits a login request
- **THEN** it SHALL receive the truthful `200`, `400`, `401`, `429`, `500`, or `503` status with the bounded JSON result schema

#### Scenario: Rate-limit representation parity
- **WHEN** an HTML or JSON login request is rate-limited
- **THEN** both representations SHALL carry the same bounded `Retry-After` semantics and SHALL NOT create a session

#### Scenario: Telemetry failure
- **WHEN** login telemetry rejects after the primary response is finalized
- **THEN** status, headers, cookies, body, and redirect location SHALL remain unchanged

### Requirement: Admin redirects remain same-origin
Login return destinations SHALL be parsed by one shared validator and SHALL be restricted to same-origin `/admin` paths.

#### Scenario: Valid admin destination
- **WHEN** the return value is `/admin?window=7`
- **THEN** successful login SHALL redirect to that same-origin path

#### Scenario: Ambiguous or external destination
- **WHEN** the return value is absolute, protocol-relative, backslash-prefixed, encoded to escape the admin prefix, or outside `/admin`
- **THEN** successful login SHALL redirect to `/admin`

### Requirement: Filesystem writes are atomic and recoverable
The local filesystem adapter SHALL replace the store atomically and SHALL allow later writes to proceed after an individual write fails.

#### Scenario: Interrupted write
- **WHEN** a temporary store write fails before replacement
- **THEN** the prior valid store SHALL remain readable

#### Scenario: Queue recovery
- **WHEN** one queued write rejects and a later valid write is submitted
- **THEN** the later write SHALL execute instead of inheriting a permanently rejected queue

### Requirement: Telemetry and limiter diagnostics preserve privacy
The application SHALL NOT log or return secret values, backend credentials, raw client IP addresses, or unbounded telemetry payloads.

#### Scenario: Redacted health output
- **WHEN** backend health is requested or an operation fails
- **THEN** diagnostics SHALL expose only the adapter mode and a bounded non-secret reason

#### Scenario: Distributed limiter identifier
- **WHEN** a production limiter key is derived from a client address
- **THEN** the persisted identifier SHALL be HMAC-derived and SHALL NOT contain the raw address
