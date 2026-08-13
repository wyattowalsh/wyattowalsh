## 1. Dependency and Configuration Contracts

- [x] 1.1 Replace literal dependency-version assertions with semantic name and placement checks
- [x] 1.2 Add `--locked` to normal development sync wrappers and update command tests
- [x] 1.3 Remove the YAML-only option from base configuration and add warning-as-error tests

## 2. Coverage

- [x] 2.1 Remove global coverage append behavior
- [x] 2.2 Isolate concurrent coverage, report, JUnit, and log paths
- [x] 2.3 Measure two clean full-suite baselines and set the deterministic floor

## 3. Type Checking

- [x] 3.1 Rebaseline diagnostics against the locked dependency set
- [x] 3.2 Partition and resolve configured errors in conflict-free path buckets
- [x] 3.3 Narrow overrides to surviving warning paths and gate every configured error plus warning-count regressions

## 4. Docs Assurance

- [x] 4.1 Pin the supported Node and pnpm policy and untrack build metadata
- [x] 4.2 Expand docs server tests
- [x] 4.3 Add docs Dependabot configuration and an independent frozen CI job
- [x] 4.4 Prove frozen install and generated typecheck from a clean docs checkout

## 5. Validation

- [x] 5.1 Run locked Python lint, type, test, and fresh coverage assurance
- [x] 5.2 Run frozen docs tests, typecheck, and production build

## 6. Behavior-Driven Coverage Repair

- [x] 6.1 Remove source-line and caller-frame renderer branch forcing
- [x] 6.2 Add real element-budget state and semantic renderer tests
- [x] 6.3 Reproduce the full coverage floor twice on one frozen fingerprint

## 7. Workflow Annotation Hygiene

- [x] 7.1 Collapse third-party metrics validation and recovery into one fail-closed step
- [x] 7.2 Prove an accepted last-known-good recovery does not create an intentional failed step
