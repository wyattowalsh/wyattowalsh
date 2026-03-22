# Living Arts Data Enrichment — Full Send

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make all 4 living art generators (ink_garden, topography, cosmic_genesis, unfurling_spiral) dramatically more data-driven by expanding GitHub data collection and deeply wiring new signals into every visual layer.

**Architecture:** Three-phase approach: (1) Expand `fetch_metrics` and `fetch_history` to collect PRs, issues, releases, commit frequency patterns, star velocity, topic clusters, and language byte-level detail. (2) Refactor all 4 generators to consume the full data surface — repos drive terrain/species, topics become labels/constellations, languages drive color palettes, contribution patterns drive weather/seasons, PR/issue activity drives insects/wildlife/aurora, star velocity drives particle intensity. (3) Add new visual elements that only exist because the data exists: topic constellation overlays, language diversity rings, streak flames, PR merge auroras, issue resolution weather.

**Tech Stack:** Python 3.13, GitHub REST + GraphQL APIs, existing `_github_http.py` helpers, numpy, OKLCH color science from `shared.py`

---

## Current State Audit

### Data Currently Fetched

| Source | Fields | Used By |
|--------|--------|---------|
| `fetch_metrics.collect()` | stars, forks, watchers, followers, following, public_repos, public_gists, orgs_count, network_count, open_issues_count, contributions_last_year, total_commits, total_prs, total_issues, total_repos_contributed, contributions_calendar, languages, top_repos, traffic_* | cosmic_genesis, unfurling_spiral (partially), ink_garden + topography (via normalize_live_metrics) |
| `fetch_history.collect_history()` | account_created, stars timeline, forks timeline, repos timeline, contributions_monthly, current_metrics | cosmic_genesis, unfurling_spiral |

### Data Fetched but UNUSED by Art Generators

- **`languages`** (byte-level, 18 languages) — only cosmic_genesis uses it for nebula hues; ink_garden/topography ignore it entirely
- **`top_repos[].topics`** (250 unique topics!) — completely unused
- **`top_repos[].description`** — completely unused
- **`top_repos[].forks`** (per-repo forks) — unused
- **`public_gists`** — unused
- **`following`** — only unfurling_spiral uses it for flow frequency
- **`total_prs`**, **`total_issues`**, **`total_repos_contributed`** — unused
- **`traffic_*`** (views, clones, referrers) — unused
- **`latest_stargazer`**, **`latest_fork_owner`** — unused

### Data NOT Fetched That Could Be

| Data | API | Visual Potential |
|------|-----|-----------------|
| PR merge history | GraphQL `pullRequests` | Aurora / merge glow effects, PR velocity sparklines |
| Issue open/close timeline | GraphQL `issues` | Weather systems (storms = open issues, clearing = resolutions) |
| Release timeline | REST `/repos/{o}/{r}/releases` | Milestone markers, eruption events |
| Commit frequency by hour/day | GraphQL `contributionsCollection` | Day/night cycle, circadian patterns |
| Repo creation dates (all) | Already in `fetch_history.repos` | Geological strata layers |
| Star velocity (rate of new stars) | Derived from star timeline | Particle emission rate, glow intensity |
| Code review activity | GraphQL `contributionsCollection.pullRequestReviewContributions` | Pollination / cross-fertilization effects |
| Dependency count | REST `/repos/{o}/{r}/dependency-graph` | Root system complexity |

---

## Task 1: Expand Data Collection (`fetch_metrics.py` + `fetch_history.py`)

### Files
- Modify: `scripts/fetch_metrics.py`
- Modify: `scripts/fetch_history.py`
- Modify: `scripts/art/shared.py` (update `normalize_live_metrics`)

### New Fields in `fetch_metrics.collect()`

Add to the GraphQL query block (~line 175):

```python
# PR + Issue + Review contributions
totalPullRequestReviewContributions
restrictedContributionsCount
```

Add new REST collectors:

```python
def _collect_commit_hour_distribution(owner, token):
    """Aggregate commit hours from recent events to get circadian pattern."""
    # GET /users/{owner}/events?per_page=100
    # Filter PushEvent, extract commit timestamps, bucket by hour
    # Returns: {0: count, 1: count, ..., 23: count}

def _collect_recent_prs(owner, token):
    """Fetch recent merged PRs across repos for merge velocity."""
    # GraphQL: user.pullRequests(first: 50, states: MERGED, orderBy: UPDATED_AT)
    # Returns: [{merged_at, additions, deletions, repo_name}]

def _collect_recent_issues(owner, token):
    """Fetch recent issues for open/close ratio."""
    # GraphQL: user.issues(first: 50, orderBy: UPDATED_AT)
    # Returns: {open_count, closed_count, avg_close_days}

def _collect_releases(owner, repo, token):
    """Fetch releases for the profile repo."""
    # REST: /repos/{owner}/{repo}/releases?per_page=20
    # Returns: [{tag_name, published_at, name}]
```

### New Fields in `fetch_history.collect_history()`

Add:

```python
def _compute_star_velocity(stars_timeline):
    """Compute stars per month over last 6 months."""
    # Bucket star events by month, compute rate
    # Returns: {recent_rate: float, peak_rate: float, trend: "rising"|"falling"|"stable"}

def _compute_contribution_streaks(contributions_monthly):
    """Find longest contribution streak and current streak."""
    # Returns: {longest_streak_months: int, current_streak_months: int, streak_active: bool}
```

### Update `normalize_live_metrics` in `shared.py`

Pass through new fields and derive computed signals:

```python
# In normalize_live_metrics, after existing transforms:

# 5. Derived signals
if metrics.get("contributions_calendar"):
    # Compute hour distribution from calendar (approximate)
    metrics.setdefault("commit_hour_distribution", {})

# 6. Topic aggregation across all repos
all_topics = defaultdict(int)
for r in metrics.get("repos", []):
    for t in (r.get("topics") or []):
        all_topics[t] += 1
metrics["topic_clusters"] = dict(
    sorted(all_topics.items(), key=lambda x: x[1], reverse=True)
)

# 7. Language diversity index (Shannon entropy)
lang_bytes = metrics.get("languages", {})
if lang_bytes:
    total = sum(lang_bytes.values())
    if total > 0:
        probs = [b / total for b in lang_bytes.values()]
        metrics["language_diversity"] = -sum(
            p * math.log2(p) for p in probs if p > 0
        )
        metrics["language_count"] = len(lang_bytes)

# 8. Star velocity from history
if history and history.get("stars"):
    metrics["star_velocity"] = _compute_star_velocity_from_events(
        history["stars"]
    )

# 9. Contribution streaks
if metrics.get("contributions_monthly"):
    metrics["contribution_streaks"] = _compute_contribution_streaks(
        metrics["contributions_monthly"]
    )
```

**Commit:** `feat(data): expand GitHub data collection with PRs, issues, releases, derived signals`

---

## Task 2: Enrich Ink Garden (`ink_garden.py`)

### Files
- Modify: `scripts/art/ink_garden.py`

### 2a. Smarter Species Classification

Replace the current simplistic `_classify_species` with a richer system that uses topics, language, star count, age, fork count, and description keywords:

```python
def _classify_species(repo: dict) -> str:
    stars = repo.get("stars", 0)
    age = repo.get("age_months", 0)
    lang = repo.get("language")
    topics = set(repo.get("topics") or [])
    forks = repo.get("forks", 0)
    desc = (repo.get("description") or "").lower()

    # Topic-driven species (highest priority)
    if topics & {"ai", "machine-learning", "deep-learning", "neural-network"}:
        return "wisteria"  # NEW: cascading neural vines
    if topics & {"database", "sql", "data", "etl", "pipeline"}:
        return "oak"  # deep-rooted, foundational
    if topics & {"web", "frontend", "react", "vue", "next"}:
        return "fern"  # delicate fronds, rapid iteration
    if topics & {"cli", "tool", "utility", "devops", "infrastructure"}:
        return "bamboo"  # fast-growing, utilitarian
    if topics & {"game", "graphics", "creative", "art", "music"}:
        return "wildflower"  # colorful, expressive

    # Fork-heavy repos → spreading species
    if forks > stars * 0.5 and forks > 5:
        return "banyan"  # NEW: aerial roots = forks

    # Then fall through to existing star/age/lang logic
    if stars >= 100: return "oak"
    if stars >= 20 and age >= 24: return "birch"
    if lang in ("Rust", "Go", "C", "C++"): return "conifer"
    if lang in ("JavaScript", "TypeScript", "HTML", "CSS"): return "fern"
    if lang == "Shell": return "bamboo"
    if age < 6: return "seedling"
    if stars < 5 and age < 18: return "shrub"
    return "wildflower"
```

Add new species definitions to `SPECIES` dict:
- `"wisteria"`: cascading vine growth with neural-network-like branching
- `"banyan"`: aerial root tendrils proportional to fork count

### 2b. Topics as Botanical Annotations

Currently the annotation labels just show repo names. Enrich them with topic tags:

```python
# In the labels section (~line 2084), for each repo:
topics = repo.get("topics", [])[:3]
if topics:
    topic_label = " · ".join(topics)
    # Add as italic sub-annotation below the repo name
```

### 2c. Language-Driven Color Palettes

Currently ink_garden uses LANG_HUES for leaf/bloom colors. Expand to use `languages` byte distribution to set the overall garden palette:

```python
# Dominant language sets garden "season":
# Python-heavy → lush green summer
# JS/TS-heavy → autumn golds
# Rust/C++ → winter evergreen
# Mixed → spring diversity
lang_bytes = metrics.get("languages", {})
dominant_lang = max(lang_bytes, key=lang_bytes.get) if lang_bytes else None
```

This drives: sky wash color, ground tone, atmospheric mist color, border tint.

### 2d. Contribution Streaks → Growth Vigor

```python
streaks = metrics.get("contribution_streaks", {})
streak_months = streaks.get("current_streak_months", 0)
# streak_months drives:
# - Branch thickness multiplier (1.0 + streak * 0.05)
# - Bloom density multiplier
# - Leaf opacity boost
# - If streak_active: add golden glow to newest growth
```

### 2e. PR Activity → Pollination (Insects)

Currently insects are randomly placed. Wire them to PR data:

```python
total_prs = metrics.get("total_prs", 0) or 0
# PR count drives:
# - Number of butterflies (1 per 20 PRs, capped at 8)
# - Bee count (1 per 50 PRs, capped at 4)
# - If recent merged PRs: add pollen particles between trees
```

### 2f. Issues → Weather

```python
open_issues = metrics.get("open_issues_count", 0)
# open_issues > 20: add rain drops
# open_issues > 50: add storm clouds
# open_issues == 0: add sunbeams through canopy
```

### 2g. Star Velocity → Fireflies

```python
star_vel = metrics.get("star_velocity", {})
rate = star_vel.get("recent_rate", 0)
# rate > 5/month: add fireflies (glowing particles with trails)
# rate > 20/month: fireflies become more numerous + brighter
```

### 2h. Full Repo List (Remove MAX_REPOS=10 Cap)

Currently `repos[:MAX_REPOS]` limits to 10. With live data providing 150 repos, increase the cap and use a tiered system:
- Top 5 by stars → full trees
- Next 10 → shrubs/small plants
- Next 15 → ground cover / moss patches
- Remaining → background texture density

**Commit:** `feat(ink-garden): enrich with topics, languages, PRs, issues, streaks, star velocity`

---

## Task 3: Enrich Topography (`topography.py`)

### Files
- Modify: `scripts/art/topography.py`

### 3a. Languages → Biome Zones

Currently `LANG_BIOME` maps individual languages to biome types, but the overall map doesn't have distinct biome zones. Create language-proportional regions:

```python
# Partition the map into biome zones proportional to language bytes
# Python (52%) → large forest zone in center
# JavaScript (20%) → grassland band on east side
# TypeScript (6%) → adjacent grassland
# etc.
# Each zone gets its own vegetation symbols and color tint
```

### 3b. Topics → Place Names

The map has a legend area but no place names. Use top topics as geographic labels:

```python
# Top 5 topics become named peaks/valleys:
# "machine-learning" → "Mt. Learning" at highest peak
# "database" → "Data Lake" at lowest point
# "agents" → "Agent Valley"
# Rendered in italic cartographic font
```

### 3c. Star Velocity → River Flow Rate

```python
star_vel = metrics.get("star_velocity", {})
# Higher star velocity → wider, faster rivers with more tributaries
# Low velocity → dry creek beds (dashed lines)
```

### 3d. Contribution Streaks → Trails

```python
streaks = metrics.get("contribution_streaks", {})
# Streak length → trail length across the map
# Active streak → trail rendered as solid line with blazes
# Broken streak → trail becomes dashed/faded
```

### 3e. PR/Issue Activity → Weather Symbols

```python
# Standard cartographic weather symbols:
# High PR merge rate → sun symbol in legend
# Many open issues → storm symbol
# Both → partial clouds
```

### 3f. Followers → Settlement Symbols

```python
followers = metrics.get("followers", 0)
# followers > 100 → add small town symbol at map center
# followers > 500 → town becomes city
# followers > 1000 → city becomes capital
# Rendered as standard cartographic settlement circles
```

### 3g. Full Repo List → Terrain Density

Same tiered approach as ink_garden:
- Top repos → major peaks with named summits
- Medium repos → foothills
- Small repos → rolling terrain texture

**Commit:** `feat(topography): enrich with biome zones, place names, weather, settlements`

---

## Task 4: Enrich Cosmic Genesis (`cosmic_genesis.py`)

### Files
- Modify: `scripts/art/cosmic_genesis.py`

### 4a. PR Merges → Aurora Effects

```python
recent_prs = metrics.get("recent_merged_prs", [])
# Each recent merged PR creates a shimmering aurora band
# Color = language hue of the PR's repo
# Width proportional to additions + deletions
# Positioned in upper arc of the canvas
```

### 4b. Topics → Constellation Overlay

```python
topic_clusters = metrics.get("topic_clusters", {})
# Top 8 topics form constellation patterns
# Each topic = a named star cluster
# Connected by faint lines (like constellation art)
# Labeled with topic name in small text
```

### 4c. Language Diversity → Nebula Richness

Currently uses top 3 languages for nebula hues. Expand:

```python
# ALL languages get nebula wisps, sized by byte proportion
# More language diversity = more colorful, complex nebula field
# Shannon entropy metric drives nebula complexity
diversity = metrics.get("language_diversity", 1.0)
# diversity > 3.0 → dense multi-colored nebula
# diversity < 1.5 → sparse, monochromatic
```

### 4d. Star Velocity → Attractor Density / Particle Emission

```python
star_vel = metrics.get("star_velocity", {})
rate = star_vel.get("recent_rate", 0)
# Higher velocity → more attractor iterations (denser pattern)
# → more contribution particles per month
# → brighter glow on cells
```

### 4e. Gists → Comet Trails

```python
public_gists = metrics.get("public_gists", 0)
# Each gist = a comet trail crossing the field
# Capped at 10 comets
# Color: warm yellow/orange
# Trail length proportional to gist content
```

**Commit:** `feat(cosmic-genesis): add aurora, constellations, enhanced nebula, comets`

---

## Task 5: Enrich Unfurling Spiral (`unfurling_spiral.py`)

### Files
- Modify: `scripts/art/unfurling_spiral.py`

### 5a. Full Language Byte Palette

Currently uses LANG_HUES for dot colors. Make the phyllotaxis spiral encode full language distribution:

```python
# Each spiral point colored by language, with point SIZE
# proportional to that language's byte count
# Creates a visible pie-chart-like distribution in the spiral
```

### 5b. Topics → Connecting Arc Labels

```python
# Topic clusters form named arcs between spiral points
# Points sharing a topic get connected by faint curves
# Arc labeled with topic name
```

### 5c. PR Reviews → Cross-Pollination Lines

```python
total_reviews = metrics.get("total_pr_reviews", 0)
# Review contributions create dotted cross-lines between
# non-adjacent spiral points (showing collaboration)
```

### 5d. Contribution Streaks → Pulse Waves

```python
streaks = metrics.get("contribution_streaks", {})
# Active streak → concentric pulse rings emanating from center
# Ring count = streak months
# If streak is broken, rings fade/dissolve
```

### 5e. Repos as Spiral Points with Descriptions

```python
# Each spiral point gets a tiny tooltip annotation
# using repo description as hover text (CSS title attribute)
# This makes the SVG interactive when viewed directly
```

**Commit:** `feat(unfurling-spiral): language palette, topic arcs, streak pulses`

---

## Task 6: Wire New Data Through Pipeline

### Files
- Modify: `scripts/art/shared.py` — helpers for new visual elements
- Modify: `scripts/art/animate.py` — pass enriched metrics through
- Modify: `.github/workflows/profile-updater.yml` — ensure new data flows

### Shared Helpers

Add to `shared.py`:

```python
def compute_star_velocity(stars_timeline: list[dict]) -> dict:
    """Compute star velocity metrics from timeline events."""

def compute_contribution_streaks(monthly: dict) -> dict:
    """Find longest and current contribution streaks."""

def language_season(lang_bytes: dict) -> str:
    """Map dominant language to garden season."""

def topic_to_place_name(topic: str) -> str:
    """Convert a topic slug to cartographic place name."""
```

**Commit:** `feat(shared): add star velocity, streak, season, and place name helpers`

---

## Task 7: Integration Testing

### Files
- Create: `tests/test_data_enrichment.py`

### Tests

```python
def test_normalize_live_metrics_computes_topic_clusters():
    """Verify topic aggregation from repos."""

def test_normalize_live_metrics_computes_language_diversity():
    """Verify Shannon entropy calculation."""

def test_star_velocity_computation():
    """Verify star rate calculation from timeline."""

def test_contribution_streak_detection():
    """Verify streak finding in monthly data."""

def test_ink_garden_generates_with_full_data():
    """Smoke test: ink_garden.generate() with enriched metrics dict."""

def test_topography_generates_with_full_data():
    """Smoke test: topography.generate() with enriched metrics dict."""

def test_classify_species_topic_driven():
    """Verify topic-based species classification."""
```

Run: `uv run pytest tests/test_data_enrichment.py -v`

**Commit:** `test: add data enrichment integration tests`

---

## Execution Order

1. **Task 1** (data collection) — must be first, everything depends on it
2. **Tasks 2-5** (generator enrichment) — can be parallelized across 4 agents
3. **Task 6** (pipeline wiring) — after generators are updated
4. **Task 7** (testing) — after everything is wired

## Verification

```bash
# Fetch live data
uv run python -m scripts.fetch_metrics --owner wyattowalsh --repo wyattowalsh --output /tmp/metrics.json
uv run python -m scripts.fetch_history --owner wyattowalsh --repo wyattowalsh --output /tmp/history.json

# Generate all 4 art styles with enriched data
uv run python -m scripts.art.animate --profile wyattowalsh --metrics-path /tmp/metrics.json --history-path /tmp/history.json --svg --frames 3

# Generate ink garden + topography
uv run python -m scripts.cli generate living-art --metrics-path /tmp/metrics.json --history-path /tmp/history.json --svg-only --svg-frames 3

# Run tests
uv run pytest tests/test_data_enrichment.py -v
```
