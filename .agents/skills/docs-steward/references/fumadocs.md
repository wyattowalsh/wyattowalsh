# Fumadocs Reference

## 1. Version Snapshot (2026-08-13)

- `fumadocs-core`: `16.14.3`
- `fumadocs-ui`: `16.14.3`
- `fumadocs-mdx`: `15.2.3`
- `fumadocs-openapi`: `11.2.3`
- `next`: `16.3.0`

Source: live npm registry (`pnpm view <package> version`) on 2026-08-13.

Re-check before claiming "latest": see `version-refresh.md`.

## 2. Core Project Signals

- Next.js project with docs routes (App Router)
- Fumadocs package usage in `package.json`
- Source config and content ingestion setup

## 3. High-Value Sync Workflow

1. Validate Next + Fumadocs package alignment.
2. Validate source/content adapters and MDX ingestion.
3. Build-check docs routes and navigation generation.
4. Validate search/navigation coherence after content updates.

## 4. Advanced Configuration Focus

- Keep app-router docs structure explicit and consistent.
- Validate MDX pipeline options and remark/rehype plugin interactions.
- Keep docs UI theming aligned with site design tokens.
- Ensure API reference and guide content share consistent IA.

## 5. Health Checks

- Broken generated nav links from moved content
- MDX component import mismatches
- Next build issues from docs route dynamic params
- Stale generated indices after major content updates

## 6. Enhancement Priorities

- Strengthen docs homepage pathways by persona/task.
- Add canonical "start here" and "choose your path" docs.
- Consolidate repeated setup snippets with reusable components.
- Tighten code-sample quality and runtime expectations.

## 7. Common Anti-Patterns

- Treating Fumadocs as drop-in without Next routing review
- Mixing incompatible package major versions
- Deep nesting without breadcrumb/navigation support
- Sparse metadata causing weak discoverability

## 8. Command Skeletons

```bash
# Install/update
pnpm add next@latest fumadocs-core@latest fumadocs-ui@latest fumadocs-mdx@latest

# Build checks
pnpm next build
pnpm next lint
```

Use project scripts for stricter CI-equivalent checks.
