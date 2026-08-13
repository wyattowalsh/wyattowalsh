## Why

Daily living-art revisions dominate repository growth: reachable historical GIF blobs account for roughly 2.20 GiB of a 5.28 GiB pack. Current duplicate checkout surfaces deduplicate as Git objects, so the immediate need is deterministic media budgets and encoding prevention rather than history rewriting.

## What Changes

- Add deterministic media metadata and a versioned living-art manifest contract.
- Publish each GIF from a private same-directory stage under a stable per-output
  process lock so repo-owned writers never expose partial GIFs or overwrite a
  concurrently published revision.
- Benchmark and tune each of the six styles independently while preserving visual and animation contracts.
- Enforce per-file and aggregate byte non-regression before the sole writer commits assets.
- Transfer only the exact six canonical primary GIFs between jobs, then have
  the sole writer revalidate animation/runtime constraints, regenerate and
  verify both manifests, both galleries, and the complete docs-showcase mirror
  from that single authoritative fleet. A failed multi-surface publication
  restores the pre-call managed state before finalization exits.
- Preserve repository publishing as the default for forks and daily six-style behavior unless separately approved.
- Define, but do not automatically activate, an immutable content-addressed Blob pilot with dual-publish, reader-first cutover, and indefinite retention.

## Capabilities

### New Capabilities

- `living-art-delivery`: Versioned media metadata, deterministic size budgets, repository publishing, and optional immutable external delivery.

### Modified Capabilities

None. This repository did not previously have OpenSpec capability documents.

## Impact

Affected surfaces include the living-art manifest/gallery builder, timelapse encoding, six style generators, workflow handoff/finalization, README/docs consumers, media tests, and public artifact documentation. History rewriting, force-pushing, LFS migration, cadence changes, and normal automated object deletion are excluded.
