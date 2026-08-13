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
