## Why

The production Fumadocs deployment failed because middleware defaulted to the Edge runtime while importing the Node-only scrypt verifier. The prior deployment also treated process-local filesystem telemetry and in-memory login throttling as if they were durable serverless services, so unavailable state could break public routes or provide misleading admin protection.

## What Changes

- Upgrade the locked docs peer group to supported, security-fixed Next.js 16,
  Fumadocs 16, Fumadocs MDX 15, and React 19.2 patch releases; migrate the
  protected-route boundary from middleware to Node-only Proxy.
- Introduce explicit disabled, filesystem, and Redis telemetry modes with production defaulting to disabled unless Redis is configured.
- Make telemetry best-effort for public/business routes and truthful at the ingestion/dashboard APIs.
- Make production admin availability require both valid credentials and a distributed rate limiter; retain in-memory limiting for local development only.
- Negotiate admin-login responses by `Accept`: browser form submissions use
  bounded same-origin POST/Redirect/GET responses, while API clients retain
  truthful JSON status codes and retry semantics.
- Add deterministic configuration, auth, session, route, atomic-write, local-concurrency, failure, and privacy tests.

## Capabilities

### New Capabilities

- `docs-runtime-state`: Runtime selection, telemetry adapters, admin readiness, rate-limiting, and failure semantics for the deployed docs application.

### Modified Capabilities

None. This repository did not previously have OpenSpec capability documents.

## Impact

Affected surfaces include docs Proxy, package/lock metadata, server
configuration, password/session/auth modules, telemetry storage and routes,
docs tests, environment documentation, and Vercel runtime behavior. The safe
default adds no external service and leaves production custom telemetry/admin
unavailable rather than falsely durable.
