## 1. Runtime Repair

- [x] 1.1 Configure the initial protected-route middleware to use the Node.js runtime
- [x] 1.2 Add initial middleware matcher/runtime and password/session contract tests
- [x] 1.3 Prove a frozen production build no longer contains the Edge `node:crypto` failure
- [x] 1.4 Upgrade the compatible docs peer group, migrate middleware to Proxy, and prove a zero-advisory frozen build

## 2. Explicit Storage Modes

- [x] 2.1 Add disabled, filesystem, and Redis backend configuration with safe environment defaults
- [x] 2.2 Define the telemetry store/write-result interface
- [x] 2.3 Implement and test the disabled adapter
- [x] 2.4 Preserve and harden the local filesystem adapter
- [x] 2.5 Make filesystem replacement atomic and recover the write queue after failures

## 3. Route and Admin Semantics

- [x] 3.1 Make public/business-route observations best-effort
- [x] 3.2 Return truthful telemetry ingestion counts and mode
- [x] 3.3 Separate credential validity from production admin readiness
- [x] 3.4 Restrict the in-memory limiter to non-production mode and fail production closed
- [x] 3.5 Validate login return destinations as same-origin `/admin` paths
- [x] 3.6 Add Accept-negotiated HTML PRG and JSON login responses with bounded headers, errors, and telemetry semantics

## 4. Safe-Default Assurance

- [x] 4.1 Add disabled/local/outage/config/auth/privacy tests
- [x] 4.2 Run frozen docs tests, typecheck, production build, and route smoke
- [x] 4.3 Update docs and environment examples for shipped modes
- [x] 4.4 Re-run frozen tests, typecheck, production build, route smoke, and production dependency audit

## 5. Optional Redis Extension

- [ ] 5.1 Obtain explicit provider, region, cost, retention, and activation approval
- [ ] 5.2 Add Redis event storage and distributed rate limiting with HMAC identifiers
- [ ] 5.3 Prove concurrency, pruning, outage, privacy, and multi-instance limiter behavior
- [ ] 5.4 Provision, deploy, smoke, and explicitly enable production admin
