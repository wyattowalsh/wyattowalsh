## ADDED Requirements

### Requirement: Dependency contracts are version-agnostic
Tests SHALL validate required package names, extras membership, and core-versus-optional placement without requiring a specific minimum-version literal.

#### Scenario: Legitimate package update
- **WHEN** a required optional dependency remains in the correct extra with a newer valid specifier
- **THEN** the dependency contract SHALL pass

#### Scenario: Missing required dependency
- **WHEN** a required package is removed or moved into core dependencies
- **THEN** the dependency contract SHALL fail with the package name

### Requirement: Development synchronization is locked
Install, lint, and test wrappers SHALL synchronize from the committed lockfile; only the explicit dependency-update command SHALL upgrade resolution.

#### Scenario: Lint dependency sync
- **WHEN** the lint wrapper installs its extra
- **THEN** it SHALL invoke `uv sync --locked`

### Requirement: Configuration construction is warning-free
Direct `ProjectConfig` construction SHALL NOT declare YAML-only source options, while YAML-backed construction SHALL retain UTF-8 loading.

#### Scenario: Direct construction
- **WHEN** warnings are treated as errors and `ProjectConfig()` is created
- **THEN** construction SHALL succeed without an unused-source warning

#### Scenario: UTF-8 YAML load
- **WHEN** a YAML-backed configuration contains UTF-8 text
- **THEN** loading SHALL preserve the text without warnings

### Requirement: Authoritative coverage is fresh, isolated, and at least 95%
An authoritative test run SHALL start from fresh coverage data, concurrent shards SHALL write unique data/report paths, combined coverage SHALL contain only live sources, and the run SHALL fail below 95.0% line coverage.

#### Scenario: Consecutive authoritative runs
- **WHEN** the full suite runs twice without source changes
- **THEN** both coverage totals SHALL be reproducible and SHALL omit deleted modules

#### Scenario: Parallel shards
- **WHEN** independent shards execute concurrently
- **THEN** they SHALL NOT write the same coverage, HTML, JUnit, or log path

#### Scenario: Coverage regression
- **WHEN** authoritative line coverage falls below 95.0%
- **THEN** the test command SHALL fail even when every test assertion passes

### Requirement: Type checking rejects errors and warning regressions
The repository SHALL reject every configured type error and any new or increased warning path/rule count. Overrides SHALL cover only surviving warning pairs and SHALL be narrowed or removed when those warnings clear.

#### Scenario: Configured error
- **WHEN** a change emits any configured type error
- **THEN** CI SHALL fail

#### Scenario: Warning regression
- **WHEN** a warning path/rule pair is new or exceeds its checked-in count
- **THEN** CI SHALL fail

#### Scenario: Cleared warning
- **WHEN** an overridden warning clears
- **THEN** the override or checked-in allowance SHALL be narrowed while the full check remains green

### Requirement: Docs have independent frozen assurance
CI SHALL run docs install, tests, typecheck, and production build independently from Python assurance. The frozen install SHALL use a repository-owned lifecycle policy, and typecheck SHALL generate the ignored Fumadocs and Next type surfaces before invoking TypeScript.

#### Scenario: Docs-only regression
- **WHEN** docs TypeScript or production build fails while Python remains green
- **THEN** the docs CI job SHALL fail independently with its own diagnostics

#### Scenario: Clean-checkout docs assurance
- **WHEN** `.source/` and `.next/` are absent after checkout
- **THEN** frozen install SHALL authorize only the declared required lifecycle, typecheck SHALL generate both owned type surfaces, and non-incremental TypeScript validation and production build SHALL pass without relying on prior local output

### Requirement: Coverage tests exercise supported behavior
Tests added to expand coverage SHALL trigger behavior through supported inputs,
configuration, or dependency seams and SHALL assert observable semantic output.
They SHALL NOT select production branches by source line number, caller-frame
inspection, or hard-coded call order.

#### Scenario: Renderer element budget
- **WHEN** a renderer uses a zero or sufficient real element budget
- **THEN** its deterministic SVG SHALL remain well formed and the expected semantic roles SHALL be absent or present according to that budget

#### Scenario: Harmless source movement
- **WHEN** production statements move without changing behavior
- **THEN** the coverage contract SHALL continue to exercise and verify the same observable behavior

### Requirement: Expected metrics recovery is annotation-clean
The profile updater SHALL validate and recover each third-party metrics SVG in
one fail-closed step. An invalid new SVG with a valid previous asset SHALL be an
informational recovery outcome, not an intentionally failed validation step.

#### Scenario: Invalid third-party render with valid previous asset
- **WHEN** a generated metrics SVG contains a known error payload and the previous SVG is valid
- **THEN** the workflow SHALL restore the previous asset without creating a GitHub warning or failure annotation

#### Scenario: Invalid third-party render without a valid previous asset
- **WHEN** neither the generated nor previous metrics SVG is valid
- **THEN** recovery SHALL fail the producer job before its artifact is uploaded

### Requirement: Starred-list inputs are strict, deterministic, and paired
The updater SHALL use the repository-owned `scripts.starred_lists` module to
traverse the starred-repository GraphQL connection once, validate the complete
response strictly through the shared HTTPS-only GitHub transport, derive both
public-repository Markdown views deterministically, and publish the language and
topic outputs as one rollback-protected pair. Authentication SHALL be read from
the `GITHUB_TOKEN` environment variable and SHALL NOT be accepted as a CLI
argument.

#### Scenario: Complete public starred-repository traversal
- **WHEN** the connection contains one or more valid pages with a stable total and acyclic cursors
- **THEN** every public repository SHALL be represented deterministically in the language view and in each qualifying topic view derived from the same traversal

#### Scenario: Invalid or drifting GraphQL traversal
- **WHEN** a page is malformed, duplicated, truncated, cyclic, contains an unsafe repository URL, or changes the advertised total
- **THEN** generation SHALL exit nonzero and SHALL NOT publish either newly rendered output

#### Scenario: Transient GraphQL transport failure
- **WHEN** a page request returns HTTP 429/502/503/504 or a retryable transport timeout
- **THEN** the traversal SHALL retry with bounded deterministic backoff inside an overall fetch deadline, without logging credentials or untrusted response text, and exhaustion SHALL leave both prior outputs unchanged

#### Scenario: Positively identified GraphQL rate limit
- **WHEN** GitHub returns HTTP 403 with a valid `Retry-After` header or zero-remaining/reset headers, or HTTP 200 whose nonempty error list consists exclusively of exact `RATE_LIMITED` types
- **THEN** the traversal SHALL honor the authoritative wait or a bounded documented fallback only when it fits inside the overall fetch deadline; generic 403, mixed errors, malformed headers, and message-only rate text SHALL remain one-shot failures

#### Scenario: Second output publication fails
- **WHEN** the first destination was replaced but the second replacement fails
- **THEN** the first destination SHALL be restored to its exact pre-call content and mode, and the operation SHALL fail

#### Scenario: Token handling
- **WHEN** the CLI is invoked locally or in GitHub Actions
- **THEN** the token SHALL be read only from `GITHUB_TOKEN` and SHALL NOT appear in the argument vector

### Requirement: Dynamic profile artifacts fail closed at producer and consumer boundaries
The workflow SHALL validate both starred-list Markdown outputs before artifact
upload. Generator CLIs SHALL exit nonzero whenever an explicitly requested word
cloud, QR target, or matched light/dark banner output does not materialize as
fresh, valid media at its required path.

#### Scenario: Invalid starred-list payload
- **WHEN** either generated Markdown file is empty, begins with an error payload, lacks the expected contents heading, or contains no public GitHub repository entry
- **THEN** the starred-list producer SHALL fail before uploading its artifact or starting dependent asset generation

#### Scenario: Requested word-cloud output is absent
- **WHEN** an explicitly requested Markdown source is missing, parses to no vocabulary, or the renderer returns without creating its output
- **THEN** the word-cloud command SHALL exit nonzero and the asset producer SHALL NOT upload a stale checked-out SVG as a successful result

#### Scenario: QR renderer does not produce the requested PNG
- **WHEN** QR generation is a no-op, leaves invalid or partial media, returns a different path, or raises after writing the target
- **THEN** the command SHALL exit nonzero, remove the failed target, and SHALL NOT upload stale checked-out QR bytes

#### Scenario: Configured QR filename escapes its output directory
- **WHEN** the configured QR `output_filename` contains a directory separator, parent component, absolute path, Windows drive, non-lowercase extension, or non-PNG extension
- **THEN** the command SHALL reject it before unlinking or otherwise mutating any output path

#### Scenario: One banner variant fails
- **WHEN** either the light or derived dark banner fails to create a fresh, non-empty, valid SVG
- **THEN** the paired banner command SHALL exit nonzero and the asset producer SHALL NOT upload a stale or incomplete banner pair

#### Scenario: Profile-asset fleet reaches an artifact boundary
- **WHEN** QR, word-cloud, and banner generation completes or the downloaded artifact reaches the finalizer
- **THEN** the boundary SHALL require exactly the canonical QR PNG, two typographic word-cloud SVGs, and light/dark banner SVGs as nonempty regular parseable media, and SHALL reject every missing, malformed, non-regular, or unexpected managed file before upload or commit

#### Scenario: Flattened artifact extraction
- **WHEN** upload-artifact stores generated files at its least common root
- **THEN** each consumer SHALL download the starred pair into `.github/assets`, profile assets and metrics into `.github/assets/img`, and staged artifacts into their explicit runner-temp destinations before owned-path validation or commit

#### Scenario: Workflow attempt revision identity
- **WHEN** any producer, matrix shard, assembler, probe, or finalizer checks out repository code during an initial or partial rerun attempt
- **THEN** every checkout SHALL use the immutable trigger `github.sha`, so artifacts from one run cannot mix code or generated media from a later branch head

#### Scenario: Branch target changes before publication
- **WHEN** the target branch advances or rewinds after a run's immutable trigger SHA, including during a push attempt
- **THEN** the finalizer SHALL publish nothing, SHALL NOT rebase generated commits, and SHALL use a trigger-SHA Git lease so the comparison and update remain atomic

#### Scenario: Non-branch manual dispatch
- **WHEN** full profile publication is manually dispatched from a tag or other non-branch ref
- **THEN** the finalizer SHALL fail closed rather than treating the ref name as a writable branch

#### Scenario: Known upstream action deprecation
- **WHEN** the reviewed `actions/download-artifact` pin emits its known Node 24 `DEP0005` warning
- **THEN** only the affected download step SHALL suppress that exact warning code, and every other action or repository warning SHALL remain visible

### Requirement: Updater fallback diagnostics remain actionable
The updater SHALL disable integrations that are already known to emit invalid
payloads for the account. Only explicitly recognized capability failures on
optional GitHub data SHALL be logged as informational fallbacks; every
unexpected request, pagination, response-shape, or GraphQL failure SHALL retain
warning or failure behavior.

#### Scenario: Known-broken achievements integration
- **WHEN** production or probe metrics inputs are assembled
- **THEN** the achievements plugin SHALL be disabled rather than invoked and recovered after it queries retired Projects (classic) fields

#### Scenario: Recognized optional capability gap
- **WHEN** an allowlisted optional endpoint returns an expected capability status or every GraphQL error matches a recognized capability class
- **THEN** the collector SHALL return its bounded fallback and log the condition at info level without a GitHub warning/failure annotation

#### Scenario: Unexpected upstream failure
- **WHEN** an HTTP status, response shape, pagination condition, or GraphQL error does not match the recognized optional capability contract
- **THEN** the condition SHALL remain a warning or hard failure according to the existing collector/workflow boundary

#### Scenario: README star-history enrichment
- **WHEN** the finalizer regenerates dynamic README sections that query GitHub GraphQL star history
- **THEN** the step SHALL authenticate with the run-scoped `github.token` through `GITHUB_TOKEN`, SHALL NOT place the token in the argument vector, and SHALL retain actionable repository/error fields for genuine failures
