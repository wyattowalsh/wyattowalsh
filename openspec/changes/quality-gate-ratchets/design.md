## Context

The Python suite appends coverage into a persistent file, configuration emits repeated source warnings, `ty` is entirely report-only, dependency tests hard-code patch-level strings, and CI omits the Fumadocs application. These issues are independent but converge on the same requirement: deterministic, current-state assurance.

## Goals / Non-Goals

**Goals:** semantic dependency contracts; locked dev sync; warning-free config;
fresh shard-safe coverage; type non-regression; independent frozen docs CI;
strict, paired starred-list inputs; fail-closed word-cloud outputs; actionable
workflow annotations and fallback logs; fresh, validated QR/banner outputs.

**Non-Goals:** suppressing diagnostics, treating unexpected upstream failures as
normal capability gaps, mixing dependency upgrades with cleanup, making all
existing warnings immediately fatal, or running production docs builds inside
the profile finalizer.

## Decisions

1. Parse dependency requirement names rather than comparing literal strings.
2. Put `--locked` on normal sync wrappers; leave `uv lock --upgrade` as the explicit update path.
3. Remove `--cov-append` from default pytest options and give orchestration shards unique output roots.
4. Measure reproducible clean coverage before setting a floor; enforce 95.0%
   only after two unchanged-tree runs reproduce exact totals and source-file
   membership, preserving more than one percentage point of measured headroom.
5. Rebaseline `ty` against the locked dependency set, resolve all configured errors in conflict-free file components, narrow overrides to exact surviving warning paths/rules, and fail on every configured error or warning-ceiling increase.
6. Add a separate docs CI job using a pinned `pnpm/action-setup` step before `actions/setup-node` enables its pnpm cache; derive the pnpm version from `docs/package.json`. Give `docs/` its own workspace policy that authorizes only the required `esbuild` lifecycle, and make typecheck explicitly generate both Fumadocs and Next declarations so a clean checkout cannot inherit local build state. Remote dependency-PR disposition remains an integration gate, not a prerequisite for local workflow validation.
7. Exercise renderer limits through their real `max_elements` contract and
   semantic SVG roles. Tests must not change behavior by inspecting production
   source line numbers or by substituting equally brittle call ordinals.
8. Treat metrics validation and last-known-good recovery as one fail-closed
   operation. Expected recovery remains visible at info level without modeling
   the accepted fallback as a failed `continue-on-error` step.
9. Replace the third-party starred-list executable with
   `scripts.starred_lists`. Traverse the GitHub starred-repository connection
   once, strictly validate every page/cursor/count/repository shape through the
   shared HTTPS-only transport, derive public-repository language and topic
   Markdown deterministically, stage both payloads, and publish them as a
   rollback-protected pair. Read `GITHUB_TOKEN` only from the environment. Gate
   the artifact on its downstream Markdown contract and make every explicitly
   requested word-cloud source require a materialized output.
10. Do not invoke an upstream plugin whose retired Projects (classic) query is
    already known to produce an error payload for this account; disable
    achievements in production and probe configurations. Log only narrowly
    recognized optional HTTP/GraphQL capability gaps at info level. Preserve
    warnings for unexpected request failures, response shapes, pagination
    limits, and unrecognized GraphQL errors. Treat only an all-errors match of
    `FORBIDDEN` + `Resource not accessible by integration` at
    `repository.stargazers` with `saml_failure=false` as the run-token timestamp
    capability gap; omit the optional sparkline without logging the raw
    response.
11. Retry transient starred-list transport failures and positively identified
    GitHub rate limits with bounded delays inside a job-contained deadline.
    Treat artifact contents as flattened least-common-root files and download
    them directly into their owned destinations. Require the producer and
    finalizer to validate the same exact five-file profile-asset fleet. Until
    `actions/download-artifact#484` is resolved in a reviewed pin, suppress only
    its `DEP0005` warning inside each download step.
12. Pin every updater checkout to the immutable trigger `github.sha`. A rerun
    keeps that event SHA, while a branch ref can advance and otherwise mix
    successful artifacts from one revision with rerun shards from another.
13. Treat the generated QR and light/dark banner pair as fresh-output
    contracts. Remove each exact overwrite target before generation, validate
    the resulting media, clean partial/invalid output, and exit nonzero when a
    renderer fails, returns the wrong path, or produces no new file.

## Risks / Trade-offs

- **Coverage can fluctuate across optional platforms** -> Set the floor only
  from the locked CI-equivalent environment, make credential/tool fallbacks
  deterministic in tests, retain explicit integration skips, and preserve
  headroom below the measured baseline.
- **Type-tool upgrades can reclassify diagnostics** -> Rebaseline against the accepted locked dependency set and preserve rule/path evidence.
- **Docs CI increases runtime** -> Use a separate bounded job and cache the package store; do not weaken its build step.
- **A strict starred-list fetch can stop an otherwise renderable profile update**
  -> Preserve the last committed pair, publish neither output on any validation
  or write failure, and fail before downstream jobs can upload stale inputs.
- **GitHub GraphQL can return transient gateway failures during a long walk**
  -> Retry only allowlisted transient classes with deterministic backoff and an
  overall deadline; never publish a partial traversal.
- **Targeted action-warning suppression can outlive its cause** -> Keep it
  step-local, code-specific, coupled to the exact immutable action pin, and
  re-audit/remove it whenever that pin changes.
- **Info-level capability classification could conceal an upstream regression**
  -> Match only an explicit allowlist of optional status/error forms; retain
  warning behavior as the default for every unknown condition.

## Migration Plan

Land semantic tests and warning fixes first, then enable the independently
reversible coverage, type, and docs-workflow gates against the locked dependency
sets. Replace the starred-list producer and its workflow consumer gate in one
transaction so no intermediate revision depends on the removed third-party
CLI. Settle or supersede overlapping dependency PRs before remote integration.

## Open Questions

None. Exact stable dependency versions are resolved immediately before their own bounded update transaction.
