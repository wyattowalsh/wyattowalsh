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

## Capabilities

### New Capabilities

- `quality-gate-ratchets`: Deterministic Python/docs validation, coverage freshness, dependency contracts, and type non-regression behavior.

### Modified Capabilities

None. This repository did not previously have OpenSpec capability documents.

## Impact

Affected surfaces include Python tool configuration, CLI development commands, configuration tests, coverage outputs, type-check configuration, docs package metadata, Dependabot, and CI workflows. Existing public generator and CLI behavior remains unchanged.
