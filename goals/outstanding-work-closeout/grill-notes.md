# Grill notes — outstanding-work-closeout

Decisions so far. One open question at a time; do not treat later audit items as decided.

## Decided

1. **Scope.** Implement every verified code, docs, test, and workflow fix. Name these human gates and do not invent or fake them: revoke the classic PAT, clear the Actions billing lock, write living-art `accepted[]`, approve production Redis admin, and look at the live profile badges.
2. **Dirty tree.** Reconcile the uncommitted `dev` diff in place. Keep the lowlighter SVG deletion and make the docs match the tests. Restore generative and showcase files the generator still writes. Keep the 1200×630 banner default only if it matches the pinned SVGs; otherwise revert that size change. Do not commit until asked.
3. **Daily publisher.** Leave `main` and the default branch alone. On `dev`, state and test that a schedule event loads `main` until an explicit cutover. Billing stays a human gate.
4. **Failure policy.** Required surfaces fail closed. Optional secret-backed cards (Spotify, X, WakaTime) stay omit-and-continue. A blog network error keeps the previous marker block. A feed that parses and is empty may say there are no posts. Missing README or skills markers exit non-zero. Languages and habits cards fail when the collector failed.
5. **Docs.** Fix every command, import, path, or behavior that is false. Refresh line counts only in files this goal already edits. No repo-wide line-count rewrite.
6. **Banner.** Leave banner drawing alone except the size-default check from the dirty diff. Do not delete unread knobs, vendor an Octocat, or implement unused effects.
7. **Dependabot.** Land a cleaned Python lock bump from #12 on `dev`, and only Actions pins that are newer than `dev`. Then close #12 and #14. Do not merge those PRs into `main`.
8. **Git writes.** When the goal runs, it may commit on `dev`, push `dev`, and close #12 and #14. It may not push `main` or merge those PRs into `main`.

## Inferred from the decisions

- Pinned `banner.svg` is 1600×480, so the uncommitted 1200×630 default is reverted.
- Living-art stays six styles. Do not write `accepted[]`. Do not regenerate living-art GIFs or the pinned banner pair.
- Do not edit `.env` or `.claude/settings.local.json`. Do not check OpenSpec 9.5, 3.2, or 5.1–5.4.
- `preview skills` must not write the working-tree README. `preview generative` must not fail only because no metrics file was passed.
- Word-cloud `--renderer` applies to prompt and techs paths, and a non-typographic markdown run must not overwrite `wordcloud_typographic_by_*.svg`.
- `generate animated` passes `timeline=False` for every style and exits non-zero when the profile cannot be resolved.
- `generate all` runs WakaTime only when `WAKATIME_API_KEY` is set, and does not fail when it is absent.
