## Why

Authoritative assurance is currently weakened by appended stale coverage, repeated Pydantic source warnings, report-only type errors, brittle dependency-version assertions, and the absence of a docs CI lane. These gaps hide regressions and block legitimate dependency updates.

## What Changes

- Make dependency contract tests semantic rather than patch-version-specific.
- Make development dependency synchronization lockfile-enforced.
- Remove the unused YAML-source warning from ordinary configuration construction.
- Make authoritative coverage fresh, shard-safe, reproducible, and gated at a
  95.0% line-coverage floor.
- Eliminate all configured type errors and enforce a checked-in per-path/rule warning ceiling that permits debt reduction but rejects regressions.
- Add frozen docs test, typecheck, and build assurance plus isolated docs dependency updates.
- Require coverage-expansion tests to drive supported behavior rather than
  source line numbers, caller inspection, or call-order surrogates.
- Replace the third-party starred-list CLI with one repository-owned, strict
  GraphQL pagination pass that derives and transactionally publishes both
  deterministic Markdown views through the shared HTTPS-only transport.
- Fail closed when starred-list consumers or explicitly requested word-cloud
  outputs are absent, empty, or invalid.
- Require fresh, validated QR and matched light/dark banner outputs so a no-op
  or failed renderer cannot upload stale checked-out profile assets.
- Keep updater annotations and logs actionable by disabling the exact
  known-broken achievements integration and classifying only recognized,
  optional capability gaps as informational fallbacks.
- Bound transient and positively identified rate-limit retries for the
  starred-list traversal, extract flattened artifacts into their owned
  destinations, require an exact structurally valid profile-asset fleet at
  producer and finalizer boundaries, and scope the current upstream
  download-action deprecation suppression to the exact affected steps.

## Capabilities

### New Capabilities

- `quality-gate-ratchets`: Deterministic Python/docs validation, coverage freshness, dependency contracts, and type non-regression behavior.

### Modified Capabilities

None. This repository did not previously have OpenSpec capability documents.

## Impact

Affected surfaces include Python tool configuration, CLI development commands,
configuration tests, coverage outputs, type-check configuration, docs package
metadata, Dependabot, GitHub collectors, starred-list/word-cloud generation,
QR/banner generation, and CI workflows. The generator CLIs now make their
existing output contracts observable through nonzero exits when requested
outputs are missing, invalid, stale, or incomplete.
