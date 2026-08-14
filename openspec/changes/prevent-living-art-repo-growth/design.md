## Context

The six living-art GIFs change daily and reachable historical versions consume roughly 2.20 GiB. The two current checkout surfaces contain identical bytes and therefore share Git blobs, so deleting one mirror alone does not address historical object growth. Prevention requires measurable media contracts, bounded encoders, and a gate before finalization.

## Goals / Non-Goals

**Goals:** deterministic manifest v2; size/fidelity baselines; independent style tuning; byte gates before git write; fork-safe repository default; optional immutable pilot.

**Non-Goals:** fewer styles, cadence changes, history rewriting, LFS migration, mutable Blob paths, automatic retention deletion, or an external-service requirement for forks.

## Decisions

1. Extend the manifest with versioned deterministic descriptors while preserving the existing reader-visible fields so consumers that ignore v2 fields continue to resolve repository-local paths.
2. Derive initial budgets from the accepted optimized baseline and gate non-regression before staging rather than inventing arbitrary absolute targets.
3. Benchmark common encoder settings, then choose a Pareto winner independently per style; no style must accept a visually inferior global setting.
4. Keep the repository backend as default. External delivery, if approved, uses a separate least-privilege publisher and immutable content-addressed paths.
5. External rollout is pilot -> dual publish -> reader cutover -> current tracked-media retirement. Each phase has an explicit approval and rollback.
6. Retain remote immutable objects indefinitely by default because historical revisions can reference them.
7. Assemble and optimize each GIF in a private same-directory stage while a
   stable path-derived advisory lock is held, then publish with one atomic
   replacement after confirming the public revision has not changed. This is a
   same-host cooperating-writer contract for the repository's macOS/Linux
   environments, not a distributed filesystem compare-and-swap guarantee.
8. Treat only the six canonical primary GIFs as cross-job authority. The sole
   finalizer validates that exact untrusted inventory before mutation and then
   regenerates the primary manifest/gallery and the entire docs mirror. Do not
   transfer or trust derived companion files.
9. Interpret `budgets=None` as the canonical default mapping. Any explicit
   mapping, including an empty mapping, is the exact expected fleet.
10. Treat primary GIFs, their derived companions, and the docs mirror as one
    publication transaction. Journal the pre-call managed state, restore it on
    a mutation-phase failure, and report a rollback failure rather than
    claiming that a partially restored fleet is safe.
11. Fetch metrics and history once, export the matrix from
    `LIVING_ART_STYLE_KEYS`, and render one style per isolated GitHub-hosted
    runner with canonical 120-frame, 400-pixel, four-worker settings. Each
    shard writes to a fresh directory and uploads one uniquely named GIF-only
    artifact. A read-only assembler merges all six artifacts and applies
    `stage_living_art_fleet()` before the existing sole writer can run.

## Risks / Trade-offs

- **Aggressive compression can damage style identity** -> Require deterministic fixtures, metadata contracts, and visual comparison per style.
- **Budgets can freeze accidental bloat** -> Record the initial measured floor, then ratchet downward only after an accepted candidate.
- **External hosting adds cost and vendor state** -> Keep it optional, pilot one style, project cost before cutover, and retain repo fallback.
- **Dual publishing adds temporary workflow complexity** -> Isolate credentials in a publisher job and remove the path only after cutover proof.
- **Advisory locking cannot stop a process that ignores the lock** -> Keep the
  guarantee scoped to repo-owned same-host writers, compare the public revision
  again before replacement, and fail rather than automatically retry a conflict.
- **Regenerating mirrors in the finalizer mutates multiple directories** ->
  Validate the complete stage before mutation, journal both managed surfaces,
  restore them on mutation failure, and prove rollback with injected failures.
  The ephemeral CI checkout remains an additional containment boundary.
- **A six-runner matrix consumes more concurrent runner capacity** -> Cap the
  matrix at six jobs, keep each shard bounded to four frame workers and 45
  minutes, retain workflow-level serialization per branch, and fail the fan-in
  unless every non-experimental shard succeeds.
- **Merged artifacts can overwrite colliding paths** -> Give every shard a
  canonical disjoint filename and a run/style-qualified immutable artifact
  name, then require the assembler's exact-six inventory and media validation.

## Migration Plan

1. Land manifest v2 readers/writers and size measurement without changing consumers.
2. Tune and integrate per-style encoder winners; set non-regression budgets.
3. Add the exact-six media-only handoff, sole-writer regeneration, persisted
   postconditions, and pre-staging workflow gate; prove the current updater.
4. Split generation into shared-input preparation, six isolated style shards,
   and a validated exact-six assembler; prove matrix and merged-artifact failure
   behavior before the finalizer dependency changes.
5. Stop here unless a public store/pilot is explicitly approved.
6. If approved, execute the reader-first external rollout and retain rollback indefinitely.

## Open Questions

External provider, region, cost ceiling, and pilot/cutover approval are intentionally deferred to maintainer gates; they are not required for prevention.
