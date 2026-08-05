# Grill notes — gh-profile-readme-e2e

**Goal (confirmed):** Maximally enhance, refine, finalize, and assure the GitHub profile README end-to-end — generators, CI/finalize, assets, composition, verification.

**Slug:** `gh-profile-readme-e2e`

## Locked prior fleet decisions (do not re-grill unless user reopens)

- Full train through Wave F intent
- Living Art: wrap-flow, all 6 visible
- Delete Tech Stack teaser shields
- Card dark: SVG `@media` only (dual picture only if QA fails)
- Keep all 10 featured
- First-party Waka; keep + enrich lowlighter
- Atomic conventional commits; ask before push; no PRs
- Hard PAT gate until eradicate attestation

## In-flight state

- `main` ahead of origin by ~53 commits (unpushed fleet work)
- F2 CLI split residual; F4 systemic SVGO partial; F7 optional

## Grill answers

| # | Topic | Answer |
|---|--------|--------|
| Q1 | Done definition | **2 + dash of 3** — full structural perfection (F2, SVGO, residual ST) + light creative redesign (composition/density experiments), not a full redesign-first program |
| Q2 | Creative dash size | **2 — light composition**: polish + 1–2 layout moves if QA forces (section order / density / hero rhythm); no full creative spike branch |
| Q3 | Push vs finish | **1 — push-then-build**: Wave 0 PAT attest → push existing train → remote CI smoke → then F2/SVGO/composition with ask-before-push |
| Q4 | Wave 0 vs push | **1 — gate holds**: no push until explicit `Wave 0 done` attestation (rotate/scrub; no secrets in chat) |
| Q5 | Residual order | **1 — structure → assure → light composition**: F2 CLI split → systemic SVGO → full suite green → then ≤2 composition moves if QA |
| Q6 | F2 split shape | **1 — domain packages** under `scripts/cli/generate/` (banner, qr, word_cloud, art, readme, all_cmd); public CLI stays `readme generate …` |
| Q7 | SVGO scope | **1 — shared helper + SVG-owning generators** (banner, generative/living static, readme cards); soft-fail if svgo missing; no mass CI re-optimize of all committed SVGs |
| Q8 | Composition moves | **Experiment reorders**: try a bunch of section reorders; analyze/measure/synthesize; ship the best final order (not density-only). Still GFM-safe; keep fleet locks (10 featured, 6 living art wrap-flow, SVG media dark, no tech teaser). |
| Q9 | Measure reorders | **4 — rubric + heuristics**: scripted fold/weight/H2 ranking + visual confirm of top 2–3; user confirms final |
| Q10 | Assurance bar | **1 — local suite + remote green**: full test suite + CI green after push; workflow contracts; generate smoke where secrets allow; composition winner + GFM contracts green |
| Q11 | Reorder implementation | **3 — hybrid**: manual README skeletons for scoring, then durable config/order + rewrite anchors for the winner |
| Q12 | Grill close | **1 — closed**; residual gaps → Plannotator interview bundle only |

### Live README section order
Banner → Connect → Featured (10) → Living Art (6 wrap-flow) → Tech Stack (details) → Metrics → Word Clouds → (dynamic sections/Waka as assembled)

### Composition experiment note
User wants multi-variant reorder exploration + measurement + synthesis, not a single pre-picked reorder.

### Asset inventory (SVGO context)
- Banner already optional SVGO; ~25 img SVGs, ~21 readme/*.svg cards

### Generate commands (F2 inventory)
banner, qr, word-cloud, generative, animated, living-art, timelapse, skills, supplemental-metrics, readme-sections, wakatime, all

### Notes
- `scripts/cli/generate.py` still ~1930 LOC (F2 residual)
