## Context

Next 15.5 middleware defaulted to the Edge runtime. The prior middleware imported the configuration module, which imported the Node-only scrypt implementation, so Vercel could not bundle it. The custom telemetry store wrote one JSON file under the process working directory and the login route stored attempts in a process-local `Map`; neither was a truthful production-serverless persistence or security boundary.

## Goals / Non-Goals

**Goals:**

- Restore the production docs build with the smallest supported runtime change.
- Make storage mode and admin readiness explicit and testable.
- Keep public/search behavior available when observability is disabled or degraded.
- Preserve local filesystem telemetry for development.
- Define a transactional Redis extension point without requiring a provider for the safe default.

**Non-Goals:**

- Splitting the scrypt verifier into an Edge-safe implementation.
- Using Vercel Blob as a mutable event database or limiter.
- Provisioning Redis or enabling custom production telemetry without maintainer approval.
- Changing the password verifier or session token wire formats.

## Decisions

1. **Use Node-only Proxy on a security-fixed Next 16/Fumadocs peer group.**
   Next 16 makes Proxy's Node runtime explicit and removes the need for a
   runtime declaration. Upgrade Next, Fumadocs, Fumadocs MDX, React, and their
   lockfile as one bounded transaction rather than retaining vulnerable
   transitive packages or adding override piles.
2. **Select telemetry mode once from server configuration.** The mode union is `disabled | filesystem | redis`. Production defaults to disabled; local development defaults to filesystem. Explicit invalid or production-unsafe selections fail closed to disabled/unavailable rather than silently choosing another writable backend.
3. **Return a storage result.** Recording a batch returns received/stored/mode so ingestion can be truthful. Business-route observation helpers catch and bound telemetry failures instead of replacing the route response.
4. **Separate credentials from readiness.** Password/session validity is independent from production admin availability. Production additionally requires a distributed limiter; local development may use a bounded in-memory limiter.
5. **Keep Redis conditional.** The interface and disabled/filesystem adapters land first. Redis dependencies, persistence, HMAC client identifiers, and live configuration require a separate approved task group.
6. **Negotiate login representations with `Accept`.** Explicit HTML navigation
   receives a 303 PRG with a bounded error code and sanitized `next`; missing,
   wildcard-only, malformed, or JSON-preferred requests receive the JSON API
   contract. Request `Content-Type`, User-Agent, and fetch metadata do not
   select the response representation.
7. **Finalize the response before telemetry.** Observations record the actual
   returned status, and authentication result events are emitted only when
   password verification ran. Telemetry failure never changes the response.

## Risks / Trade-offs

- **Custom production telemetry is temporarily unavailable** -> The UI and API state this explicitly; public behavior remains healthy.
- **Node Proxy can have a cold-start cost** -> The matcher remains limited to admin paths, so public docs requests do not execute it.
- **Best-effort observation can lose events** -> Disabled/degraded state is observable; security decisions never depend on telemetry writes.
- **A config mistake could expose a local-only limiter in production** -> Configuration validation and readiness tests prohibit the in-memory backend in production.

## Migration Plan

1. Upgrade the compatible docs peer group, migrate middleware to Proxy, and
   prove the frozen production build and zero-advisory production audit.
2. Land the explicit mode/interface plus disabled and filesystem adapters.
3. Make route telemetry best-effort and admin readiness fail closed.
4. Add the negotiated login handler and verify browser PRG plus JSON machine semantics.
5. Deploy with production telemetry/admin disabled and verify public docs/search.
6. Only after separate approval, add Redis, provision it, inject credentials, and enable production admin.
7. Roll back by restoring the previous deployment; no persisted wire format changes are required for the safe-default phase.

## Open Questions

None for the safe default. Redis provider, region, cost, retention, and activation remain an explicit maintainer-gated extension.
