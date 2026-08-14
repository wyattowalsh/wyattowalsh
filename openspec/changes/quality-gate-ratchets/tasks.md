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

## 8. Starred-List and Generated-Asset Integrity

- [x] 8.1 Replace the third-party starred-list CLI with one strict first-party GraphQL traversal using the shared HTTPS-only transport and environment-only token handling
- [x] 8.2 Render deterministic public-repository language/topic views and publish the pair transactionally with rollback coverage
- [x] 8.3 Validate both Markdown consumers before artifact upload and make every explicitly requested word-cloud output fail nonzero when absent
- [x] 8.4 Require fresh validated QR and light/dark banner outputs, with stale-target removal and fail-closed CLI coverage
- [x] 8.5 Require the exact five-file profile-asset fleet and parse its PNG/SVG media at producer and finalizer boundaries
- [x] 8.6 Reject configured QR filenames that can escape the output directory before any target mutation

## 9. Updater Log and Annotation Hygiene

- [x] 9.1 Disable the known-broken achievements plugin in production and probe configurations instead of recovering its error payload
- [x] 9.2 Downgrade only recognized optional GitHub capability gaps to bounded informational fallbacks while retaining warnings for unexpected failures
- [x] 9.3 Add bounded transient and positively identified rate-limit retry for the first-party starred traversal, exact artifact extraction destinations, and step-local suppression for the reviewed upstream `download-artifact` DEP0005 defect
- [x] 9.4 Pin every updater checkout to the immutable trigger SHA and prove the contract across all jobs
- [ ] 9.5 Prove the integrated remote updater run completes without GitHub warning/failure annotations or application warning/error fallbacks
- [x] 9.6 Authenticate finalizer README star-history enrichment with the run-scoped token and keep genuine failure logs actionable
- [x] 9.7 Classify only the exact GitHub App `repository.stargazers` timestamp denial as an informational no-sparkline capability fallback
