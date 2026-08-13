## Context

The Python suite appends coverage into a persistent file, configuration emits repeated source warnings, `ty` is entirely report-only, dependency tests hard-code patch-level strings, and CI omits the Fumadocs application. These issues are independent but converge on the same requirement: deterministic, current-state assurance.

## Goals / Non-Goals

**Goals:** semantic dependency contracts; locked dev sync; warning-free config; fresh shard-safe coverage; type non-regression; independent frozen docs CI.

**Non-Goals:** suppressing diagnostics, mixing dependency upgrades with cleanup, making all existing warnings immediately fatal, or running production docs builds inside the profile finalizer.

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

## Risks / Trade-offs

- **Coverage can fluctuate across optional platforms** -> Set the floor only
  from the locked CI-equivalent environment, make credential/tool fallbacks
  deterministic in tests, retain explicit integration skips, and preserve
  headroom below the measured baseline.
- **Type-tool upgrades can reclassify diagnostics** -> Rebaseline against the accepted locked dependency set and preserve rule/path evidence.
- **Docs CI increases runtime** -> Use a separate bounded job and cache the package store; do not weaken its build step.

## Migration Plan

Land semantic tests and warning fixes first, then enable the independently reversible coverage, type, and docs-workflow gates against the locked dependency sets. Settle or supersede overlapping dependency PRs before remote integration.

## Open Questions

None. Exact stable dependency versions are resolved immediately before their own bounded update transaction.
