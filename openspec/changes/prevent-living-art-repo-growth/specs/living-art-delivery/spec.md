## ADDED Requirements

### Requirement: Living-art media metadata is deterministic and versioned
The living-art manifest SHALL declare a manifest version and, for every canonical asset, its style, variant, media type, bytes, dimensions, frame count, ordered per-frame durations, aggregate duration, SHA-256 digest, backend, and local path or immutable URL.

#### Scenario: Repeated manifest generation
- **WHEN** the same media files are scanned twice
- **THEN** all media descriptors SHALL be byte-for-byte equivalent apart from explicitly run-specific metadata

#### Scenario: Legacy field consumer
- **WHEN** a consumer reads only the pre-v2 manifest fields
- **THEN** names, repository-local paths, styles, variants, channels, byte counts, totals, and counts SHALL remain available with their existing meanings

### Requirement: Media growth is rejected before git write
The updater SHALL validate per-file and aggregate living-art byte budgets before the sole writer stages or commits generated media.

#### Scenario: Oversized asset
- **WHEN** a generated GIF exceeds its accepted budget
- **THEN** finalization SHALL stop before git staging and report the path, observed bytes, and budget

#### Scenario: Accepted fleet
- **WHEN** every style and the aggregate fleet satisfy their budgets
- **THEN** the artifact handoff SHALL proceed without adding a second git writer

### Requirement: GIF publication is staged and serialized
Every repo-owned writer SHALL assemble and optimize a GIF in a private
same-directory stage while holding the stable lock for its logical output path.
It SHALL publish the completed candidate with one atomic replacement only after
the public output revision is confirmed unchanged.

#### Scenario: Generation or optimization failure
- **WHEN** assembly, decoding, or final validation fails before publication
- **THEN** the prior public GIF SHALL remain complete and unchanged, or the path SHALL remain absent when no prior GIF existed

#### Scenario: Concurrent repo-owned writer
- **WHEN** two processes attempt to publish the same logical GIF
- **THEN** the stable per-output lock SHALL serialize them and a detected revision conflict SHALL fail without automatically overwriting or retrying the newer revision

#### Scenario: Concurrent independent styles
- **WHEN** processes publish different canonical GIF names
- **THEN** their independent path locks SHALL permit the publications to proceed concurrently

### Requirement: Artifact handoff has one media authority
The producer SHALL transfer exactly the six canonical primary GIFs and no
derived manifest, gallery, or docs-mirror payload. The sole writer SHALL treat
the downloaded artifact as untrusted input, validate the complete inventory
before destination mutation, and regenerate every derived surface from it.

#### Scenario: Invalid staged inventory
- **WHEN** the staged fleet is missing a canonical GIF or contains an unexpected, non-regular, symlinked, corrupt, wrong-dimension, wrong-loop, invalid-frame-duration, over-frame-limit, below-runtime-floor, or over-budget entry
- **THEN** finalization SHALL stop before changing a destination or staging a git path

#### Scenario: Mutation-phase publication failure
- **WHEN** a primary replacement, companion regeneration, or public-mirror write fails after destination mutation begins
- **THEN** finalization SHALL restore both managed destination surfaces to their byte-for-byte pre-call state while preserving unmanaged collateral, or report that rollback itself failed

#### Scenario: Stale persisted companions
- **WHEN** the checkout contains stale, missing, or corrupt primary or public manifests and galleries
- **THEN** the sole writer SHALL regenerate them and the complete docs mirror from the validated six-GIF fleet before git staging

#### Scenario: Persisted postconditions
- **WHEN** finalization reports successful living-art publication
- **THEN** persisted manifests and galleries SHALL match their generated objects, primary and public GIF hashes SHALL match, and stable manifest payloads SHALL be identical apart from `generated_at` and `output_dir`

### Requirement: Explicit budget mappings are authoritative
Omitting a budget mapping SHALL select the canonical six-style defaults. An
explicit mapping, including an empty mapping, SHALL define the exact expected
asset set independently of the aggregate budget selection.

#### Scenario: Explicit empty mapping
- **WHEN** validation receives an empty mapping and an empty manifest with an explicit zero total budget
- **THEN** validation SHALL pass without substituting canonical defaults

#### Scenario: Unexpected asset under empty mapping
- **WHEN** validation receives an empty mapping and any asset
- **THEN** that asset SHALL be rejected as unexpected

### Requirement: Style optimization preserves the product contract
Optimization SHALL preserve all six registered styles, deterministic seed behavior, dimensions, animation loop, readable visual identity, and existing public generator commands unless a separate approved change says otherwise.

#### Scenario: Per-style candidate
- **WHEN** an encoder or renderer candidate reduces bytes
- **THEN** it SHALL be accepted only if focused contracts and visual review show no regression

### Requirement: Repository delivery remains the default
Forks and unconfigured installations SHALL continue to publish and consume repository-local living-art paths without requiring an external account or token.

#### Scenario: No external backend configured
- **WHEN** the generator/updater runs with default configuration
- **THEN** it SHALL produce the existing repository and docs-showcase surfaces

### Requirement: Optional external delivery is immutable and reader-first
If explicitly approved, external media SHALL use public content-addressed immutable objects, a least-privilege publisher without git-write permission, dual-publish verification, and consumer cutover before tracked-media retirement.

#### Scenario: Pilot upload
- **WHEN** one style is uploaded for the pilot
- **THEN** its remote bytes, SHA-256, media type, GitHub rendering, docs rendering, and repository rollback SHALL be verified before broader publication

#### Scenario: Full cutover
- **WHEN** all styles are dual-published and verified
- **THEN** consumers MAY switch to immutable URLs while retaining an explicit repository-path rollback

### Requirement: Historical media remains recoverable
Normal automation SHALL NOT delete content-addressed published media or rewrite Git history.

#### Scenario: Old revision reference
- **WHEN** an older README or docs revision references a historical object
- **THEN** the referenced object SHALL remain available unless a later explicit reachability migration authorizes deletion
