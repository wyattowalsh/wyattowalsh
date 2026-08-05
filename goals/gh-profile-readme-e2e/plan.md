# Plan — gh-profile-readme-e2e (v4)

> **Executable DAG:** [`task-graph.json`](./task-graph.json) (machine-readable nodes, deps, locks, parallel groups, dual tracks).  
> **Facts:** [`facts.md`](./facts.md) · **Gate history:** v1–v3 annotated → parallelize + hyperfine; this revision is codebase-audited.

---

## 0. Goal

Maximally enhance/refine/finalize/assure the live GitHub profile README end-to-end: ship the unpushed fleet after Wave 0, finish residual structure (dark banner, shared SVGO, F2 CLI packages), measure 6–8 section-order candidates under fixed **Banner → Connect**, land the winner with durable order + neighbor-aware rewrite anchors, verify local + remote under git discipline.

---

## 1. Codebase audit findings (plan corrections)

These are **evidence-backed** fixes to earlier plan versions:

| Finding | Evidence | Plan impact |
|---------|----------|-------------|
| Dark bug is real TypeError path | `generate.py` L319–325: `to_banner_config(**cli_overrides, dark_mode=True, output_path=…)` while `cli_overrides` already has `output_path` | B1–B2 remain critical; test must assert no TypeError / both files |
| F2 package **docs lead code** | `scripts/AGENTS.md` already describes `cli/generate/` domain modules; code is still monolithic `generate.py` (~1930 LOC); `docs/.../architecture.mdx` still says `generate.py` | C8a/C8b must **reconcile** AGENTS (already half-correct) + architecture MDX, not invent a third layout |
| Package module names | AGENTS: `banner`, `qr`, `word_cloud`, `art`, `readme_cmd`, `all_cmd` | Use **`readme_cmd`** not ad-hoc `readme.py` |
| `preview.py` couples to callables | Imports `banner`, `qr`, `word_cloud`, `readme_sections`, `skills`, `generative_art` from `.generate` | C6 re-export contract is ship-blocker |
| Order-hardcoded tests are multi-file | `test_readme_gfm_ux.py` regexes assume Living→Tech, Tech→Metrics; `test_readme_sections.py` fixtures; `test_profile_workflow.py` order | E4.4a–c three parallel test leaves before E4.4d |
| SVGO scope wider than banner | `readme_svg.write_raw` / `render_and_write`; `generative.py` SVG outs; **`word_clouds/generate.py` writes SVG** without SVGO | D4c hooks word_clouds (soft-fail) |
| Living art “12” path hits | README may list each `living-*.gif` more than once; contracts assert **6 styles**, not raw string count | Scorer/locks use style set == 6, featured cards ≥ 10 |
| Markers beyond H2 | `TOP_BADGES`, `FEATURED_PROJECTS`, `SKILLS`, `waka`, `BLOG_POSTS` | Reorders only move H2 blocks below Connect; markers stay section-local |
| `ReadmeSectionsSettings` has no order field yet | `scripts/config.py` L394+ | E4.1 adds SSOT carefully with pydantic + YAML |
| Fleet already green contracts | profile_workflow: no anmol098, finalize sole writer, plugin_music no | A5 is verify-only, not rewrite |

---

## 2. Design thesis (`/agents:design`)

| Dial | Choice |
|------|--------|
| Audience | Mixed recruiter + technical peer |
| Mode | Editorial portfolio + badge/status surface |
| Register | Technical-premium; expressive living art |
| Fixed band | Banner → Connect |
| Locks | 10 featured wrap; 6 living GIFs wrap-flow; no tech teaser; card `@media` dark; GFM no tables-as-UX |
| Scoring heuristics | Hick, Miller, Proximity, Jakob, content resilience |
| Proof | Suite + remote CI + visual top 2–3 candidates |
| System precedence | Extend generators/config — no second pipeline |

### Rubric weights

| Criterion | W |
|-----------|---|
| First-fold clarity | 25% |
| Scan path / Hick | 20% |
| Hierarchy / chunking | 15% |
| Proof density balance | 15% |
| Dark/light resilience | 10% |
| GFM/mobile wrap | 15% |

---

## 3. Orchestration model

```text
DECOMPOSE → nodes in task-graph.json
CLASSIFY  → gate | read | write | verify | merge
MAXIMIZE  → parallelGroup fanout (W1=13, E1=8, …)
CONFLICT  → locks L-CLI, L-BAN, L-SVG, L-RS, L-README, L-GIT
DISPATCH  → explore | general-purpose | code-reviewer | human | cap
TRACK     → CAP awaits parallelGroup before dependent nodes
```

### Dual tracks (max parallelism)

```text
                    W0 → W1 fanout
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
     G0→G1→A2 ship           E1–E3 composition (goals-only)
              │                     │
              ▼                     │
     B → D → C structure            │
              │                     │
              └──────────┬──────────┘
                         ▼
                   E4 join (needs C10 + winner)
                         ▼
                        F assure
```

**Composition track must not touch `scripts/` or live `README.md` until E4.**

---

## 4. Team + locks

See `task-graph.json` → `locks` and node `lane`/`lock` fields.

| Lock | Paths | Serial holder |
|------|-------|---------------|
| L-CLI | `scripts/cli/generate*`, `preview.py` | C* |
| L-BAN | `scripts/banner.py` | D3 (after B) |
| L-SVG | svg_optimize, generative, readme_svg, word_clouds write | D* (serialize on conflict) |
| L-RS | readme_sections, config order field | E4.1–2 |
| L-README | README.md | E4.3, E4.5 |
| L-GIT | commits/pushes | CAP only |

---

## 5. Hyperfine graph (summary)

**Full node list:** [`task-graph.json`](./task-graph.json) (`nodes[]` with `id`, `deps`, `parallelGroup`, `agent`, `verify`).

### Counts

| Wave | Nodes | Max concurrent agents |
|------|-------|----------------------|
| G | 2 | human |
| W0 | 5 | 1 CAP |
| W1 | 14 | **13 explore** |
| A | 5 | 3 post-push |
| B | 6 | 2 |
| D | 9 | 4 wire (prefer lock-safe) |
| C | 18 | 1 writer + 2 test/docs |
| E1–E3 | 15 | **8 skeletons** + scorer + 4 E3 |
| E4 | 10 | 1 RS + 3 test files |
| F | 5 | 3 |
| **Total** | **~89** | peak ~13 inventory / 8 composition |

### Critical path

`G0 → G1 → A2 → B* → D* → C* → E4* → F*`  
(see `task-graph.json` `criticalPath`)

### Target package layout (aligned with AGENTS.md)

```text
scripts/cli/generate/
  __init__.py      # generate_app + re-exports for preview
  _common.py
  banner.py
  qr.py
  word_cloud.py
  art.py           # generative_art, animated, living_art, timelapse
  readme_cmd.py    # skills, supplemental_metrics, readme_sections, wakatime
  all_cmd.py
```

### Candidate skeletons (E1 parallel)

| ID | Below Connect |
|----|----------------|
| S0 | Featured → Living → Tech → Metrics → WordClouds → dyn |
| S1 | Featured → Metrics → Living → Tech → WordClouds |
| S2 | Living → Featured → Tech → Metrics → WordClouds |
| S3 | Featured → Tech → Living → Metrics → WordClouds |
| S4 | Featured → Metrics → WordClouds → Living → Tech |
| S5 | Featured → Tech → Metrics → WordClouds → Living |
| S6 | Featured → Living → Metrics → WordClouds → Tech |
| S7 | Featured → Tech → WordClouds → Metrics → Living |

Dynamic blocks (Skills markers, Waka, Blog) **travel with their H2 region or stay end-stable** — CAP freezes policy in E1.0: *prefer keep Waka/Blog after Word Clouds unless winner explicitly moves them*.

---

## 6. Spawn recipes

### W1 (one shot)

```text
Spawn 13 explore agents → W1.01..W1.13
cwd: repo root; write only goals/gh-profile-readme-e2e/inventory/*
Await all → CAP W1.14
```

### E1 (one shot)

```text
After E1.0, spawn 8 agents CMP-0..7
Each writes exactly one composition/candidates/0N-*.md
Forbidden: scripts/**, README.md, tests/**
```

### D-wire

```text
After D2: prefer parallel D4a, D4b, D4c (distinct files).
If agent runtime can't multi-lock L-SVG, run D3 then D4a→D4b→D4c serial.
D5 tests parallel with last wires once API stable.
```

### C

```text
Single writer for all C1–C6.
Optional parallel C7a|C7b after C6; C8a|C8b after tests (different doc files).
```

### Subagent contract

```text
Mission: <node ids from task-graph.json>
Owned files: <node.files or out>
Do not edit: other locks + secrets
Evidence: path:line, command, exit code
Output: findings, edits, verify, blockers
Stop: no push; no force; no secret print
```

---

## 7. Verification map (facts → nodes)

| Fact | Nodes |
|------|-------|
| fact-wave0 | G0 |
| fact-push-first | A2–A5 |
| fact-dark-banner | B1–B4 |
| fact-svgo | D2–D5 (incl D4c) |
| fact-f2 | C1–C7, C8a |
| fact-header-fixed | E4.4d |
| fact-fleet-locks | E4.4d, A4 |
| fact-reorder-count | E1.1–E1.8 |
| fact-reorder-measure | E2.*, E3.* |
| fact-reorder-hybrid | E1 + E4.1–2 |
| fact-winner-shipped | E4.3–E4.5 |
| fact-gfm | E4.4d, F1 |
| fact-waka / finalize / lowlighter | A5, F3 |
| fact-assurance | F1–F4 |
| fact-git-discipline | CAP commits |

---

## 8. Failure recovery

| Failure | Action |
|---------|--------|
| G0 incomplete | No push; structure/composition goals-only OK |
| A2 object/push error | Diagnose; **never force-push** |
| A3 remote red | File + triage; structure can continue; careful on further pushes |
| B1 doesn't fail | Bug already fixed? Keep regression test |
| C6 preview ImportError | Block C10 until re-exports complete |
| E4.5 order drift | Fix anchors E4.2; do not “done” |
| Multi-file test fail | E4.4a–c ownership; re-run E4.4d |
| Scope creep redesign | CAP rejects (fact-out-scope) |

---

## 9. Git discipline

- Atomic conventional commits per leaf group  
- **Ask before every push**  
- No force-push / history rewrite / default PRs  
- Stay on `main` unless requested  
- CAP owns L-GIT  

Subjects: dark fix · SVGO helper · F2 split · order SSOT · winner apply · order contracts.

---

## 10. Done

All [`facts.md`](./facts.md) lines verified. `task-graph.json` critical path complete. Local full suite green. Remote CI green after final push. Winner live + regenerate-stable. Banner→Connect + fleet locks + GFM held.

---

## 11. `/goal` bootstrap

1. Load this plan + `task-graph.json`.  
2. CAP: W0 → fanout W1 → merge.  
3. Human G0/G1.  
4. A ship.  
5. **Parallel:** structure B→D→C **and** composition E1–E3.  
6. Join E4 → F → facts checklist.
