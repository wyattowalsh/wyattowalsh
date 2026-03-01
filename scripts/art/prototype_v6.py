"""
Generative Art Prototypes v6 — Meaningful Data Mappings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The connection between GitHub data and visual form should be
*metaphorical*, not mechanical. Each metric shapes a specific
aspect of the visual narrative.

CONCEPT: "Digital Ecosystem"
Your GitHub profile as a living ecosystem:

- **Repos = species** in your ecosystem. Each repo is a distinct organism
  with its own DNA (language→color, stars→luminosity, age→size).
  They cluster by language into biomes.

- **Contributions = seasons & weather**. Monthly contribution patterns
  become atmospheric conditions — dense months create storms/auroras,
  quiet months create calm drifts. The year's rhythm is visible.

- **Stars/forks = pollination**. Each star event creates a burst of
  pollen/spores that drift outward. Forks create root connections
  underground. The community interaction literally grows the ecosystem.

- **Followers = gravity**. More followers = stronger gravitational
  center = denser, more complex structures pulled inward.

- **Orgs = tectonic plates**. Each org creates a distinct landmass
  that the ecosystem grows on. Multiple orgs = archipelago.

- **Account age = geological strata**. Older accounts have deeper,
  more layered structures. New accounts are fresh volcanic islands.

Three artworks with these metaphors:
1. "Ecosystem" — repos as organisms in a living garden
2. "Weather Map" — contribution patterns as atmospheric phenomena
3. "Root System" — stars/forks as above/below-ground network
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path
from collections import defaultdict

import numpy as np

WIDTH = 800
HEIGHT = 800
CX = WIDTH / 2
CY = HEIGHT / 2
DURATION = 30

# Language → color hue mapping (metaphor: each language is a biome)
LANG_HUES = {
    "Python": 210, "JavaScript": 50, "TypeScript": 220, "Java": 10,
    "C++": 290, "C": 260, "Go": 180, "Rust": 25, "Ruby": 350,
    "Swift": 15, "Kotlin": 280, "Shell": 120, "HTML": 30, "CSS": 200,
    "R": 240, "Jupyter Notebook": 170, "Scala": 340, "Lua": 245,
    "Dockerfile": 195, "Makefile": 100, None: 160,
}

PROFILES = {
    "wyatt": {
        "label": "wyattowalsh",
        "stars": 42, "forks": 12, "watchers": 8,
        "followers": 85, "following": 60,
        "public_repos": 35, "orgs_count": 3,
        "contributions_last_year": 1200, "total_commits": 4800,
        "open_issues_count": 5, "network_count": 18,
        "account_age_years": 8,
        # Mock repo data — in production this comes from the API
        "repos": [
            {"name": "gnn-mol", "language": "Python", "stars": 12, "age_months": 24},
            {"name": "ball", "language": "Python", "stars": 8, "age_months": 36},
            {"name": "portfolio", "language": "TypeScript", "stars": 5, "age_months": 18},
            {"name": "dotfiles", "language": "Shell", "stars": 3, "age_months": 60},
            {"name": "nba-db", "language": "Python", "stars": 6, "age_months": 48},
            {"name": "wyattowalsh", "language": "Python", "stars": 2, "age_months": 12},
            {"name": "research", "language": "Jupyter Notebook", "stars": 4, "age_months": 30},
        ],
        # Mock monthly contributions — seasonal rhythm
        "contributions_monthly": {
            "2025-01": 120, "2025-02": 95, "2025-03": 180, "2025-04": 210,
            "2025-05": 140, "2025-06": 60, "2025-07": 45, "2025-08": 80,
            "2025-09": 150, "2025-10": 200, "2025-11": 170, "2025-12": 90,
        },
        # Mock star events — pollination moments
        "star_events": [
            {"month": 1, "count": 3}, {"month": 3, "count": 5}, {"month": 4, "count": 8},
            {"month": 6, "count": 2}, {"month": 9, "count": 7}, {"month": 11, "count": 4},
        ],
    },
    "prolific": {
        "label": "Prolific OSS",
        "stars": 5200, "forks": 890, "watchers": 340,
        "followers": 12000, "following": 150,
        "public_repos": 180, "orgs_count": 8,
        "contributions_last_year": 3800, "total_commits": 42000,
        "open_issues_count": 120, "network_count": 2400,
        "account_age_years": 14,
        "repos": [
            {"name": f"project-{i}", "language": lang, "stars": stars, "age_months": age}
            for i, (lang, stars, age) in enumerate([
                ("Python", 1200, 84), ("JavaScript", 800, 96), ("TypeScript", 600, 48),
                ("Go", 400, 60), ("Rust", 350, 36), ("C++", 280, 108),
                ("Python", 200, 72), ("Shell", 150, 120), ("Ruby", 120, 90),
                ("Java", 100, 60), ("Python", 80, 24), ("TypeScript", 60, 36),
                ("Go", 40, 18), ("Rust", 30, 12), ("Python", 20, 6),
            ])
        ],
        "contributions_monthly": {
            "2025-01": 380, "2025-02": 420, "2025-03": 350, "2025-04": 400,
            "2025-05": 310, "2025-06": 280, "2025-07": 290, "2025-08": 320,
            "2025-09": 360, "2025-10": 400, "2025-11": 380, "2025-12": 310,
        },
        "star_events": [
            {"month": m, "count": c} for m, c in
            [(1,45),(2,38),(3,52),(4,60),(5,42),(6,35),(7,30),(8,38),(9,55),(10,65),(11,48),(12,40)]
        ],
    },
    "newcomer": {
        "label": "New Developer",
        "stars": 3, "forks": 1, "watchers": 2,
        "followers": 8, "following": 45,
        "public_repos": 6, "orgs_count": 1,
        "contributions_last_year": 180, "total_commits": 320,
        "open_issues_count": 2, "network_count": 3,
        "account_age_years": 1,
        "repos": [
            {"name": "hello-world", "language": "Python", "stars": 1, "age_months": 8},
            {"name": "todo-app", "language": "JavaScript", "stars": 2, "age_months": 5},
            {"name": "portfolio", "language": "HTML", "stars": 0, "age_months": 3},
        ],
        "contributions_monthly": {
            "2025-07": 10, "2025-08": 25, "2025-09": 30, "2025-10": 40,
            "2025-11": 35, "2025-12": 40,
        },
        "star_events": [{"month": 10, "count": 2}, {"month": 12, "count": 1}],
    },
}


def _sh(m):
    s = "-".join(str(m.get(k,0)) for k in sorted(m.keys()) if k not in ("label","repos","contributions_monthly","star_events"))
    return hashlib.sha256(s.encode()).hexdigest()

def _hf(h, a, b):
    return int(h[a:b], 16) / (16**(b-a))

def _l2s(c):
    return 12.92*c if c<=0.0031308 else 1.055*c**(1/2.4)-0.055

def oklch(L, C, H):
    a = C*math.cos(math.radians(H)); b = C*math.sin(math.radians(H))
    lc=L+0.3963377774*a+0.2158037573*b
    mc=L-0.1055613458*a-0.0638541728*b
    sc=L-0.0894841775*a-1.2914855480*b
    l_=lc**3;m_=mc**3;s_=sc**3
    r=max(0,4.0767416621*l_-3.3077115913*m_+0.2309699292*s_)
    g=max(0,-1.2684380046*l_+2.6097574011*m_-0.3413193965*s_)
    bv=max(0,-0.0041960863*l_-0.7034186147*m_+1.7076147010*s_)
    r=max(0,min(1,_l2s(r)));g=max(0,min(1,_l2s(g)));bv=max(0,min(1,_l2s(bv)))
    return f"#{int(r*255):02x}{int(g*255):02x}{int(bv*255):02x}"


class Noise2D:
    def __init__(self, seed=0):
        rng=np.random.default_rng(seed)
        self.perm=np.tile(rng.permutation(256).astype(np.int32),2)
        angles=rng.uniform(0,2*np.pi,256)
        self.grads=np.column_stack([np.cos(angles),np.sin(angles)])
    def _fade(self,t): return t*t*t*(t*(t*6-15)+10)
    def noise(self,x,y):
        xi=int(math.floor(x))&255;yi=int(math.floor(y))&255
        xf=x-math.floor(x);yf=y-math.floor(y)
        u=self._fade(xf);v=self._fade(yf)
        aa=self.perm[self.perm[xi]+yi];ab=self.perm[self.perm[xi]+yi+1]
        ba=self.perm[self.perm[xi+1]+yi];bb=self.perm[self.perm[xi+1]+yi+1]
        ga=self.grads[aa%256];gb=self.grads[ab%256]
        gc=self.grads[ba%256];gd=self.grads[bb%256]
        daa=ga[0]*xf+ga[1]*yf;dba=gc[0]*(xf-1)+gc[1]*yf
        dab=gb[0]*xf+gb[1]*(yf-1);dbb=gd[0]*(xf-1)+gd[1]*(yf-1)
        x1=daa+u*(dba-daa);x2=dab+u*(dbb-dab)
        return x1+v*(x2-x1)
    def fbm(self,x,y,octaves=4):
        val=0;amp=1;freq=1;ta=0
        for _ in range(octaves):
            val+=amp*self.noise(x*freq,y*freq);ta+=amp;amp*=0.5;freq*=2
        return val/ta


def bloom_filter(fid="bloom"):
    return f"""<filter id="{fid}" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="b1"/>
    <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="b2"/>
    <feGaussianBlur in="SourceGraphic" stdDeviation="14" result="b3"/>
    <feColorMatrix in="b3" type="matrix" result="bright"
      values="1.6 0 0 0 0.1  0 1.6 0 0 0.1  0 0 1.6 0 0.1  0 0 0 0.5 0"/>
    <feMerge>
      <feMergeNode in="bright"/><feMergeNode in="b2"/>
      <feMergeNode in="b1"/><feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>"""


# =========================================================================
# 1. "ECOSYSTEM" — Repos as organisms in a living garden
#
# Each repo is a distinct organism:
#   - Language → species color (hue from LANG_HUES)
#   - Stars → luminosity/glow intensity (brighter = more starred)
#   - Age → organism size & complexity (older = more elaborate)
#   - Same-language repos cluster together (biome formation)
#
# Organisms are organic branching forms (L-system-like)
# growing from a central substrate. The substrate layers
# represent account age (more years = deeper geological strata).
# =========================================================================

def generate_ecosystem(metrics: dict, dark_mode: bool = True) -> str:
    h = _sh(metrics)
    rng = np.random.default_rng(int(h[:8], 16))
    noise = Noise2D(seed=int(h[8:16], 16))

    repos = metrics.get("repos", [])
    followers = metrics.get("followers", 10)
    account_age = metrics.get("account_age_years", 1)
    orgs = metrics.get("orgs_count", 1)

    # Gravity: followers pull things toward center
    gravity = min(1.0, followers / 5000)
    # More gravity = tighter, denser composition
    spread = 300 * (1 - gravity * 0.5)

    # Group repos by language (biome clustering)
    biomes = defaultdict(list)
    for repo in repos:
        biomes[repo.get("language")].append(repo)

    # Assign angular sectors to biomes (tectonic plates = orgs)
    biome_list = sorted(biomes.items(), key=lambda x: -sum(r["stars"] for r in x[1]))
    n_biomes = len(biome_list)

    # Each organism: position, color, size, glow
    organisms = []
    for bi, (lang, lang_repos) in enumerate(biome_list):
        # Angular sector for this biome
        sector_start = bi * 2 * math.pi / max(1, n_biomes)
        sector_width = 2 * math.pi / max(1, n_biomes) * 0.8

        hue = LANG_HUES.get(lang, 160)

        for ri, repo in enumerate(lang_repos):
            stars = repo.get("stars", 0)
            age = repo.get("age_months", 6)

            # Position: within the biome sector, distance from center based on age
            angle = sector_start + sector_width * (ri + 0.5) / max(1, len(lang_repos))
            angle += rng.uniform(-0.2, 0.2)  # organic scatter
            dist = 40 + min(spread, age * 2.5) + rng.uniform(-20, 20)

            x = CX + dist * math.cos(angle)
            y = CY + dist * math.sin(angle)

            # Luminosity from stars
            luminosity = min(1.0, 0.3 + stars / 50)
            # Size from age
            size = max(8, min(60, age * 0.5 + 5))
            # Complexity (branching depth) from age
            complexity = max(2, min(5, age // 12 + 2))

            organisms.append({
                "x": x, "y": y, "hue": hue, "luminosity": luminosity,
                "size": size, "complexity": complexity, "stars": stars,
                "name": repo.get("name", ""),
                "angle": angle, "lang": lang,
            })

    # Build SVG
    bg1 = "#040410" if dark_mode else "#fafafe"
    bg2 = "#010108" if dark_mode else "#f0eef5"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">
<defs>
  {bloom_filter()}
  {bloom_filter("softBloom")}
  <filter id="glow" x="-100%" y="-100%" width="300%" height="300%">
    <feGaussianBlur stdDeviation="8"/>
    <feColorMatrix type="matrix"
      values="1.5 0 0 0 0.1  0 1.5 0 0 0.1  0 0 1.5 0 0.1  0 0 0 0.6 0"/>
  </filter>
  <radialGradient id="bg" cx="50%" cy="50%" r="60%">
    <stop offset="0%" stop-color="{bg1}"/>
    <stop offset="100%" stop-color="{bg2}"/>
  </radialGradient>
  <radialGradient id="vig" cx="50%" cy="50%" r="55%">
    <stop offset="35%" stop-color="black" stop-opacity="0"/>
    <stop offset="100%" stop-color="black" stop-opacity="0.6"/>
  </radialGradient>
</defs>
<style>
  @keyframes sprout {{
    from {{ transform: scale(0); opacity: 0; }}
    to {{ transform: scale(1); opacity: 1; }}
  }}
  @keyframes breathe {{
    0%, 100% {{ opacity: var(--op); }}
    50% {{ opacity: calc(var(--op) * 1.3); }}
  }}
  @keyframes starBurst {{
    0% {{ r: 0; opacity: 0.8; }}
    50% {{ opacity: 0.4; }}
    100% {{ r: var(--burst-r); opacity: 0; }}
  }}
  .organism {{
    transform-origin: var(--ox) var(--oy);
    animation: sprout 1.5s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
    opacity: 0;
  }}
  .branch-path {{
    animation: breathe 6s ease-in-out infinite;
  }}
  .star-ring {{
    animation: starBurst 4s ease-out infinite;
  }}
</style>
"""
    svg += f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#bg)"/>\n'

    # Geological strata — concentric rings representing account age
    svg += '<g opacity="0.06">\n'
    for yr in range(account_age):
        r = 30 + yr * (350 / max(1, account_age))
        stratum_hue = 200 + yr * 15
        color = oklch(0.25, 0.06, stratum_hue % 360)
        svg += f'<circle cx="{CX}" cy="{CY}" r="{r:.0f}" fill="none" stroke="{color}" stroke-width="0.8"/>\n'
    svg += '</g>\n'

    # Biome boundary fields — subtle colored regions
    for bi, (lang, lang_repos) in enumerate(biome_list):
        sector_start = bi * 2 * math.pi / max(1, n_biomes)
        sector_mid = sector_start + math.pi / max(1, n_biomes)
        hue = LANG_HUES.get(lang, 160)
        color = oklch(0.15, 0.08, hue)
        br = 200 + len(lang_repos) * 15
        bx = CX + br * 0.4 * math.cos(sector_mid)
        by = CY + br * 0.4 * math.sin(sector_mid)
        svg += f'<circle cx="{bx:.0f}" cy="{by:.0f}" r="{br * 0.5:.0f}" fill="{color}" opacity="0.04"/>\n'

    # Organisms
    svg += '<g filter="url(#bloom)">\n'
    for idx, org in enumerate(organisms):
        ox, oy = org["x"], org["y"]
        hue = org["hue"]
        lum = org["luminosity"]
        size = org["size"]
        complexity = org["complexity"]
        delay = (idx / max(1, len(organisms))) * DURATION * 0.6

        # Each organism is a branching form
        branches = []

        def grow(x, y, angle, depth, length, parent_hue):
            if depth > complexity or length < 2:
                return
            n_val = noise.fbm(x * 0.02 + idx, y * 0.02, 2)
            a = angle + n_val * 0.8

            ex = x + length * math.cos(a)
            ey = y + length * math.sin(a)

            # Color shifts slightly along branches
            branch_hue = (parent_hue + depth * 15) % 360
            branches.append((x, y, ex, ey, depth, branch_hue))

            # Fork
            if depth < complexity:
                spread_angle = 0.4 + rng.uniform(0, 0.4)
                grow(ex, ey, a - spread_angle, depth+1, length*rng.uniform(0.6, 0.8), branch_hue)
                grow(ex, ey, a + spread_angle, depth+1, length*rng.uniform(0.6, 0.8), branch_hue)
                if rng.random() < 0.3:  # occasional third branch
                    grow(ex, ey, a + rng.uniform(-0.2, 0.2), depth+1, length*rng.uniform(0.4, 0.6), branch_hue)

        # Grow from organism center outward
        n_stems = max(2, min(5, complexity))
        for si in range(n_stems):
            stem_angle = org["angle"] + si * 2 * math.pi / n_stems + rng.uniform(-0.3, 0.3)
            grow(ox, oy, stem_angle, 0, size * 0.4, hue)

        # Render organism group
        svg += f'<g class="organism" style="animation-delay:{delay:.2f}s;--ox:{ox:.0f}px;--oy:{oy:.0f}px">\n'

        for x1, y1, x2, y2, depth, bh in branches:
            color = oklch(0.3 + lum * 0.4, 0.12 + lum * 0.08, bh)
            sw = max(0.3, (2.0 - depth * 0.3) * (0.5 + lum * 0.5))
            op = max(0.15, (0.6 - depth * 0.08) * lum)

            mx = (x1+x2)/2 + rng.uniform(-1, 1)
            my = (y1+y2)/2 + rng.uniform(-1, 1)

            svg += (f'<path d="M{x1:.1f},{y1:.1f} Q{mx:.1f},{my:.1f} {x2:.1f},{y2:.1f}" '
                    f'fill="none" stroke="{color}" stroke-width="{sw:.2f}" '
                    f'opacity="{op:.3f}" stroke-linecap="round" class="branch-path" '
                    f'style="--op:{op:.3f};animation-delay:{delay + depth*0.3:.1f}s"/>\n')

            # Leaf/bud at branch tips
            if depth == complexity:
                tip_color = oklch(0.5 + lum * 0.3, 0.16 + lum * 0.06, bh)
                tip_r = 1 + lum * 2
                svg += (f'<circle cx="{x2:.1f}" cy="{y2:.1f}" r="{tip_r:.1f}" '
                        f'fill="{tip_color}" opacity="{op * 0.8:.3f}"/>\n')

        # Core glow — brighter for more-starred repos
        if org["stars"] > 0:
            glow_color = oklch(0.6 + lum * 0.2, 0.14, hue)
            glow_r = 4 + org["stars"] * 0.3
            svg += (f'<circle cx="{ox:.1f}" cy="{oy:.1f}" r="{min(15, glow_r):.1f}" '
                    f'fill="{glow_color}" opacity="{lum * 0.3:.3f}" filter="url(#glow)"/>\n')

            # Star burst rings (pollination metaphor)
            if org["stars"] > 3:
                burst_r = 10 + org["stars"] * 0.8
                burst_color = oklch(0.7, 0.10, hue)
                svg += (f'<circle cx="{ox:.1f}" cy="{oy:.1f}" r="2" '
                        f'fill="none" stroke="{burst_color}" stroke-width="0.5" '
                        f'class="star-ring" style="--burst-r:{min(30, burst_r):.0f};'
                        f'animation-delay:{delay + 1:.1f}s"/>\n')

        svg += '</g>\n'

    svg += '</g>\n'

    # Center: "seed" — the original account creation point
    seed_color = oklch(0.7, 0.10, 200)
    svg += f'<circle cx="{CX}" cy="{CY}" r="3" fill="{seed_color}" opacity="0.5"/>\n'

    if dark_mode:
        svg += f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#vig)"/>\n'

    svg += '</svg>\n'
    return svg


# =========================================================================
# 2. "WEATHER MAP" — Contribution patterns as atmospheric phenomena
#
# Monthly contributions → atmospheric density at angular positions
# (January=top, moving clockwise through the year)
# Dense months create storm cells with swirling flow lines
# Quiet months are clear sky regions
# Star events create lightning bolts / aurora flares
# The whole thing breathes with the seasonal rhythm
# =========================================================================

def generate_weather_map(metrics: dict, dark_mode: bool = True) -> str:
    h = _sh(metrics)
    rng = np.random.default_rng(int(h[:8], 16))
    noise = Noise2D(seed=int(h[8:16], 16))

    monthly = metrics.get("contributions_monthly", {})
    star_events = metrics.get("star_events", [])
    max_monthly = max(monthly.values()) if monthly else 100

    # Map months to angular positions (Jan=top, clockwise)
    month_angles = {}
    sorted_months = sorted(monthly.keys())
    for mi, month in enumerate(sorted_months):
        angle = -math.pi/2 + mi * 2 * math.pi / max(1, len(sorted_months))
        month_angles[month] = angle

    # Generate storm cells at high-activity months
    storm_centers = []
    for month, count in monthly.items():
        intensity = count / max(1, max_monthly)
        if intensity < 0.1:
            continue
        angle = month_angles.get(month, 0)
        dist = 100 + (1 - intensity) * 200  # high intensity = closer to center
        x = CX + dist * math.cos(angle)
        y = CY + dist * math.sin(angle)
        storm_centers.append((x, y, intensity, angle, month))

    # Generate flow field influenced by storm cells
    flow_paths = []
    n_flow = max(80, min(300, sum(monthly.values()) // 5))
    flow_steps = 100
    step_size = 2.0

    for fi in range(n_flow):
        # Start positions biased toward storm regions
        if fi < n_flow * 0.6 and storm_centers:
            sc = storm_centers[fi % len(storm_centers)]
            x = sc[0] + rng.normal(0, 40 * (1 - sc[2]))
            y = sc[1] + rng.normal(0, 40 * (1 - sc[2]))
        else:
            x = rng.uniform(40, WIDTH - 40)
            y = rng.uniform(40, HEIGHT - 40)

        pts = [(x, y)]
        for fs in range(flow_steps):
            # Base curl noise flow
            vx_n = noise.fbm(x*0.004, y*0.004+100, 3)
            vy_n = noise.fbm(x*0.004+100, y*0.004, 3)
            vx = vy_n; vy = -vx_n  # curl

            # Storm influence: each storm cell creates a vortex
            for sx, sy, si, sa, sm in storm_centers:
                dx = x - sx; dy = y - sy
                d = math.sqrt(dx*dx + dy*dy) + 1e-10
                if d < 150:
                    # Vortex: tangential velocity, strength inversely proportional to distance
                    strength = si * 80 / (d + 10)
                    vx += -dy / d * strength
                    vy += dx / d * strength

            mag = math.sqrt(vx*vx + vy*vy) + 1e-10
            x += vx/mag * step_size
            y += vy/mag * step_size
            if x<-10 or x>WIDTH+10 or y<-10 or y>HEIGHT+10:
                break
            pts.append((x, y))

        if len(pts) > 10:
            # Find which storm this flow is closest to (for coloring)
            avg_x = sum(p[0] for p in pts[:20]) / min(20, len(pts))
            avg_y = sum(p[1] for p in pts[:20]) / min(20, len(pts))
            closest_intensity = 0.3
            for sx, sy, si, sa, sm in storm_centers:
                d = math.sqrt((avg_x-sx)**2 + (avg_y-sy)**2)
                if d < 200 and si > closest_intensity:
                    closest_intensity = si
            flow_paths.append((pts, closest_intensity))

    # Lightning / aurora from star events
    lightning_bolts = []
    for se in star_events:
        month_idx = se["month"] - 1
        angle = -math.pi/2 + month_idx * 2 * math.pi / 12
        count = se["count"]
        for _ in range(count):
            # Lightning bolt from outer edge toward center
            start_r = rng.uniform(280, 360)
            sx = CX + start_r * math.cos(angle + rng.uniform(-0.2, 0.2))
            sy = CY + start_r * math.sin(angle + rng.uniform(-0.2, 0.2))
            bolt = [(sx, sy)]
            bx, by = sx, sy
            for seg in range(rng.integers(4, 10)):
                # Toward center with random jitter
                dx = CX - bx; dy = CY - by
                d = math.sqrt(dx*dx + dy*dy) + 1e-10
                step = rng.uniform(15, 35)
                bx += dx/d * step + rng.normal(0, 12)
                by += dy/d * step + rng.normal(0, 12)
                bolt.append((bx, by))
            lightning_bolts.append(bolt)

    # Build SVG
    bg1 = "#040412" if dark_mode else "#fafafe"
    bg2 = "#010108" if dark_mode else "#f0eef5"

    # Choose palette based on overall activity level
    total_contribs = sum(monthly.values()) if monthly else 0
    if total_contribs > 3000:
        pal_hue_base = 280  # intense purple storms
    elif total_contribs > 1000:
        pal_hue_base = 200  # blue-teal weather
    else:
        pal_hue_base = 160  # calm green-cyan

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">
<defs>
  {bloom_filter()}
  <filter id="lightning" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="blur"/>
    <feColorMatrix in="blur" type="matrix" result="bright"
      values="2 0 0 0 0.2  0 2 0 0 0.2  0 0 2 0 0.3  0 0 0 0.7 0"/>
    <feMerge>
      <feMergeNode in="bright"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>
  <radialGradient id="bg" cx="50%" cy="50%" r="60%">
    <stop offset="0%" stop-color="{bg1}"/>
    <stop offset="100%" stop-color="{bg2}"/>
  </radialGradient>
  <radialGradient id="vig" cx="50%" cy="50%" r="55%">
    <stop offset="35%" stop-color="black" stop-opacity="0"/>
    <stop offset="100%" stop-color="black" stop-opacity="0.5"/>
  </radialGradient>
</defs>
<style>
  @keyframes flowDraw {{
    from {{ stroke-dashoffset: var(--len); opacity: 0; }}
    to {{ stroke-dashoffset: 0; opacity: var(--op); }}
  }}
  @keyframes stormPulse {{
    0%, 100% {{ r: var(--r); opacity: var(--op); }}
    50% {{ r: calc(var(--r) * 1.15); opacity: calc(var(--op) * 1.3); }}
  }}
  @keyframes flash {{
    0% {{ opacity: 0; }}
    5% {{ opacity: 0.9; }}
    15% {{ opacity: 0.3; }}
    25% {{ opacity: 0.7; }}
    40% {{ opacity: 0; }}
    100% {{ opacity: 0; }}
  }}
  .flow {{
    stroke-dasharray: var(--len);
    stroke-dashoffset: var(--len);
    animation: flowDraw var(--dur) cubic-bezier(0.4, 0, 0.2, 1) forwards;
  }}
  .storm {{
    animation: stormPulse 5s ease-in-out infinite;
  }}
  .bolt {{
    animation: flash 4s ease-out infinite;
    opacity: 0;
  }}
</style>
"""
    svg += f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#bg)"/>\n'

    # Month markers (subtle clock face)
    svg += '<g opacity="0.08">\n'
    month_labels = ["J","F","M","A","M","J","J","A","S","O","N","D"]
    for mi in range(12):
        angle = -math.pi/2 + mi * 2 * math.pi / 12
        lx = CX + 375 * math.cos(angle)
        ly = CY + 375 * math.sin(angle)
        text_color = "#aaaacc" if dark_mode else "#555566"
        svg += f'<text x="{lx:.0f}" y="{ly:.0f}" text-anchor="middle" dominant-baseline="central" font-family="monospace" font-size="10" fill="{text_color}">{month_labels[mi]}</text>\n'
        # Tick line
        tx1 = CX + 355 * math.cos(angle)
        ty1 = CY + 355 * math.sin(angle)
        tx2 = CX + 365 * math.cos(angle)
        ty2 = CY + 365 * math.sin(angle)
        svg += f'<line x1="{tx1:.0f}" y1="{ty1:.0f}" x2="{tx2:.0f}" y2="{ty2:.0f}" stroke="{text_color}" stroke-width="0.5"/>\n'
    svg += '</g>\n'

    # Storm cell glows
    for sx, sy, si, sa, sm in storm_centers:
        r = 30 + si * 80
        hue = (pal_hue_base + si * 60) % 360
        color = oklch(0.2 + si * 0.2, 0.10 + si * 0.06, hue)
        svg += (f'<circle cx="{sx:.0f}" cy="{sy:.0f}" fill="{color}" '
                f'class="storm" style="--r:{r:.0f};--op:{si * 0.12:.3f}" r="{r:.0f}"/>\n')

    # Flow field
    svg += '<g filter="url(#bloom)">\n'
    for fi, (pts, intensity) in enumerate(flow_paths):
        hue = (pal_hue_base + intensity * 80) % 360
        L = 0.3 + intensity * 0.3
        C = 0.10 + intensity * 0.10
        color = oklch(L, C, hue)
        sw = 0.3 + intensity * 0.8
        op = 0.05 + intensity * 0.20

        pd = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
        path_len = 0
        for j in range(1, len(pts)-1, 2):
            if j+1 < len(pts):
                pd += f" Q{pts[j][0]:.1f},{pts[j][1]:.1f} {pts[j+1][0]:.1f},{pts[j+1][1]:.1f}"
                path_len += math.sqrt((pts[j+1][0]-pts[max(0,j-1)][0])**2 + (pts[j+1][1]-pts[max(0,j-1)][1])**2)
            else:
                pd += f" L{pts[j][0]:.1f},{pts[j][1]:.1f}"

        delay = fi / len(flow_paths) * DURATION * 0.6
        dur = 3.0 + (1 - intensity) * 3

        svg += (f'<path d="{pd}" fill="none" stroke="{color}" stroke-width="{sw:.2f}" '
                f'stroke-linecap="round" class="flow" '
                f'style="--len:{max(1,path_len):.0f};--op:{op:.3f};--dur:{dur:.1f}s;'
                f'animation-delay:{delay:.2f}s"/>\n')
    svg += '</g>\n'

    # Lightning bolts
    if lightning_bolts:
        svg += '<g filter="url(#lightning)">\n'
        for bi, bolt in enumerate(lightning_bolts):
            pd = f"M{bolt[0][0]:.1f},{bolt[0][1]:.1f}"
            for bx, by in bolt[1:]:
                pd += f" L{bx:.1f},{by:.1f}"
            bolt_color = oklch(0.85, 0.08, 60)
            delay = (bi / len(lightning_bolts)) * DURATION * 0.8 + rng.uniform(0, 5)
            dur = 3 + rng.uniform(0, 4)
            svg += (f'<path d="{pd}" fill="none" stroke="{bolt_color}" stroke-width="1.2" '
                    f'stroke-linecap="round" stroke-linejoin="round" class="bolt" '
                    f'style="animation-delay:{delay:.1f}s;animation-duration:{dur:.1f}s"/>\n')
        svg += '</g>\n'

    if dark_mode:
        svg += f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#vig)"/>\n'

    svg += '</svg>\n'
    return svg


# =========================================================================
# 3. "ROOT SYSTEM" — Stars/forks as above/below-ground network
#
# Above ground (top half): star events bloom as flowers/pollen bursts
#   rising upward from the surface. More stars = taller, more luminous.
# Below ground (bottom half): fork events grow as root networks
#   spreading downward. More forks = deeper, more branching.
# The surface line represents the present — events grow away from it.
# Total commits determine the soil richness (background texture density).
# =========================================================================

def generate_root_system(metrics: dict, dark_mode: bool = True) -> str:
    h = _sh(metrics)
    rng = np.random.default_rng(int(h[:8], 16))
    noise = Noise2D(seed=int(h[8:16], 16))

    stars = metrics.get("stars", 5)
    forks = metrics.get("forks", 2)
    total_commits = metrics.get("total_commits", 500)
    followers = metrics.get("followers", 10)
    contributions_last_year = metrics.get("contributions_last_year", 200)

    # Surface line — organic, not straight
    surface_y = HEIGHT * 0.5
    surface_points = []
    for sx in range(0, WIDTH + 5, 5):
        sy = surface_y + noise.fbm(sx * 0.008, 0, 3) * 15
        surface_points.append((sx, sy))

    # Stars → upward blooms (above surface)
    n_blooms = max(3, min(30, stars))
    blooms = []  # (x, height, luminosity, hue)
    for bi in range(n_blooms):
        bx = 40 + (bi / max(1, n_blooms - 1)) * (WIDTH - 80) if n_blooms > 1 else CX
        bx += rng.uniform(-20, 20)
        # Find surface y at this x
        sx_idx = max(0, min(len(surface_points)-1, int(bx / 5)))
        by = surface_points[sx_idx][1]
        # Height: more stars = taller on average
        bloom_h = 30 + rng.uniform(0, 1) ** 0.5 * min(200, stars * 3)
        lum = 0.3 + rng.uniform(0, 0.5)
        hue = (180 + bi * 137.508) % 360  # golden angle for color variety
        blooms.append((bx, by, bloom_h, lum, hue))

    # Forks → downward roots (below surface)
    n_roots = max(2, min(20, forks))
    root_segments = []  # (x1,y1,x2,y2,depth)
    MAX_ROOT_SEGS = 4000

    def grow_root(x, y, angle, depth, length, max_d):
        if depth > max_d or length < 3 or len(root_segments) >= MAX_ROOT_SEGS:
            return
        n_segs = max(2, min(8, int(length / 5)))
        cx_, cy_ = x, y
        for s in range(n_segs):
            if len(root_segments) >= MAX_ROOT_SEGS:
                break
            nv = noise.fbm(cx_ * 0.01 + depth, cy_ * 0.01, 2)
            a = angle + nv * 0.6
            sl = length / n_segs * rng.uniform(0.7, 1.3)
            nx_ = cx_ + sl * math.cos(a)
            ny_ = cy_ + sl * math.sin(a)
            # Keep below surface and in bounds
            if ny_ < surface_y - 10: ny_ = surface_y + 5
            if nx_ < 20 or nx_ > WIDTH - 20: a = math.pi - a
            nx_ = cx_ + sl * math.cos(a)
            ny_ = cy_ + sl * math.sin(a)
            root_segments.append((cx_, cy_, nx_, ny_, depth))
            cx_, cy_ = nx_, ny_
            angle = a
            if len(root_segments) < MAX_ROOT_SEGS and rng.random() < 0.4 * (1 - depth/max_d):
                fa = rng.uniform(0.3, 1.0) * rng.choice([-1, 1])
                grow_root(cx_, cy_, a+fa, depth+1, length*rng.uniform(0.5, 0.7), max_d)
        if depth < max_d - 1 and len(root_segments) < MAX_ROOT_SEGS:
            for _ in range(rng.integers(1, 3)):
                if len(root_segments) >= MAX_ROOT_SEGS: break
                fa = rng.uniform(0.2, 0.8) * rng.choice([-1, 1])
                grow_root(cx_, cy_, angle+fa, depth+1, length*rng.uniform(0.4, 0.6), max_d)

    root_max_depth = max(3, min(6, 3 + forks // 5))
    for ri in range(n_roots):
        rx = 60 + (ri / max(1, n_roots-1)) * (WIDTH - 120) if n_roots > 1 else CX
        rx += rng.uniform(-15, 15)
        sx_idx = max(0, min(len(surface_points)-1, int(rx / 5)))
        ry = surface_points[sx_idx][1]
        # Roots grow downward (angle around π/2 = straight down)
        root_angle = math.pi/2 + rng.uniform(-0.5, 0.5)
        grow_root(rx, ry, root_angle, 0, 20 + forks * 2, root_max_depth)

    # Build SVG
    bg_top = "#040418" if dark_mode else "#e8eeff"
    bg_bot = "#0a0804" if dark_mode else "#e8ddd0"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">
<defs>
  {bloom_filter()}
  {bloom_filter("rootBloom")}
  <filter id="pollenGlow" x="-80%" y="-80%" width="260%" height="260%">
    <feGaussianBlur stdDeviation="5"/>
    <feColorMatrix type="matrix"
      values="1.4 0 0 0 0.1  0 1.4 0 0 0.1  0 0 1.4 0 0.1  0 0 0 0.5 0"/>
  </filter>
  <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{bg_top}"/>
    <stop offset="48%" stop-color="{bg_top}"/>
    <stop offset="52%" stop-color="{bg_bot}"/>
    <stop offset="100%" stop-color="{bg_bot}"/>
  </linearGradient>
  <radialGradient id="vig" cx="50%" cy="50%" r="55%">
    <stop offset="40%" stop-color="black" stop-opacity="0"/>
    <stop offset="100%" stop-color="black" stop-opacity="0.5"/>
  </radialGradient>
</defs>
<style>
  @keyframes bloomUp {{
    from {{ transform: scaleY(0); opacity: 0; }}
    to {{ transform: scaleY(1); opacity: 1; }}
  }}
  @keyframes rootGrow {{
    from {{ stroke-dashoffset: var(--len); }}
    to {{ stroke-dashoffset: 0; }}
  }}
  @keyframes pollen {{
    0% {{ r: 1; opacity: 0.7; }}
    100% {{ r: var(--pr); opacity: 0; transform: translateY(var(--py)); }}
  }}
  .bloom-stem {{
    transform-origin: var(--ox) var(--oy);
    animation: bloomUp 2s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
    opacity: 0;
  }}
  .root {{
    stroke-dasharray: var(--len);
    stroke-dashoffset: var(--len);
    animation: rootGrow var(--dur) cubic-bezier(0.23, 1, 0.32, 1) forwards;
  }}
  .pollen-particle {{
    animation: pollen 5s ease-out infinite;
  }}
</style>
"""
    svg += f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#bg)"/>\n'

    # Soil texture (commits = richness)
    soil_density = min(1.0, total_commits / 20000)
    n_soil_particles = int(200 * soil_density)
    for si in range(n_soil_particles):
        sx = rng.uniform(10, WIDTH-10)
        sy = rng.uniform(surface_y + 10, HEIGHT - 10)
        sr = rng.uniform(0.3, 1.0)
        sop = rng.uniform(0.02, 0.06) * soil_density
        sc = oklch(0.2 + rng.uniform(0, 0.1), 0.05, 30 + rng.uniform(-15, 15))
        svg += f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="{sr:.1f}" fill="{sc}" opacity="{sop:.3f}"/>\n'

    # Roots (below ground)
    svg += '<g filter="url(#rootBloom)">\n'
    for ri, (x1, y1, x2, y2, depth) in enumerate(root_segments):
        hue = 25 + depth * 10  # warm earthy tones
        color = oklch(0.25 + 0.1 * (1 - depth/root_max_depth), 0.10, hue)
        sw = max(0.3, 2.0 * (1 - depth/root_max_depth)**1.5)
        op = max(0.1, 0.4 * (1 - depth/root_max_depth*0.5))

        seg_len = math.sqrt((x2-x1)**2 + (y2-y1)**2)
        delay = depth * DURATION * 0.08 + ri / max(1, len(root_segments)) * DURATION * 0.4
        dur = 1.5 + depth * 0.2

        mx = (x1+x2)/2 + rng.uniform(-1, 1)
        my = (y1+y2)/2 + rng.uniform(-1, 1)

        svg += (f'<path d="M{x1:.1f},{y1:.1f} Q{mx:.1f},{my:.1f} {x2:.1f},{y2:.1f}" '
                f'fill="none" stroke="{color}" stroke-width="{sw:.2f}" '
                f'stroke-linecap="round" class="root" '
                f'style="--len:{max(1,seg_len):.0f};--dur:{dur:.1f}s;'
                f'animation-delay:{delay:.2f}s;opacity:{op:.3f}"/>\n')
    svg += '</g>\n'

    # Surface line
    sp = f"M{surface_points[0][0]:.0f},{surface_points[0][1]:.0f}"
    for sx, sy in surface_points[1:]:
        sp += f" L{sx:.0f},{sy:.0f}"
    surface_color = oklch(0.3, 0.08, 100) if dark_mode else oklch(0.5, 0.12, 100)
    svg += f'<path d="{sp}" fill="none" stroke="{surface_color}" stroke-width="1.5" opacity="0.3"/>\n'

    # Blooms (above ground)
    svg += '<g filter="url(#bloom)">\n'
    for bi, (bx, by, bh, lum, hue) in enumerate(blooms):
        delay = DURATION * 0.1 + bi / max(1, len(blooms)) * DURATION * 0.5

        # Stem
        stem_color = oklch(0.3 + lum * 0.2, 0.08, 130)
        n_stem_pts = max(3, int(bh / 15))
        stem_pts = [(bx, by)]
        sx_, sy_ = bx, by
        for si in range(n_stem_pts):
            frac = (si + 1) / n_stem_pts
            sx_ = bx + noise.fbm(bx * 0.02 + si, by * 0.02, 2) * 15
            sy_ = by - bh * frac
            stem_pts.append((sx_, sy_))

        stem_d = f"M{stem_pts[0][0]:.1f},{stem_pts[0][1]:.1f}"
        for j in range(1, len(stem_pts)-1, 2):
            if j+1 < len(stem_pts):
                stem_d += f" Q{stem_pts[j][0]:.1f},{stem_pts[j][1]:.1f} {stem_pts[j+1][0]:.1f},{stem_pts[j+1][1]:.1f}"
            else:
                stem_d += f" L{stem_pts[j][0]:.1f},{stem_pts[j][1]:.1f}"

        svg += (f'<g class="bloom-stem" style="animation-delay:{delay:.2f}s;'
                f'--ox:{bx:.0f}px;--oy:{by:.0f}px">\n')

        svg += (f'<path d="{stem_d}" fill="none" stroke="{stem_color}" '
                f'stroke-width="1" opacity="0.4" stroke-linecap="round"/>\n')

        # Flower head at top
        tip_x, tip_y = stem_pts[-1]
        flower_color = oklch(0.5 + lum * 0.3, 0.18, hue)
        flower_r = 3 + lum * 5
        svg += (f'<circle cx="{tip_x:.1f}" cy="{tip_y:.1f}" r="{flower_r:.1f}" '
                f'fill="{flower_color}" opacity="{0.4 + lum * 0.4:.3f}"/>\n')

        # Glow
        glow_color = oklch(0.6 + lum * 0.2, 0.12, hue)
        svg += (f'<circle cx="{tip_x:.1f}" cy="{tip_y:.1f}" r="{flower_r * 2:.1f}" '
                f'fill="{glow_color}" opacity="{lum * 0.2:.3f}" filter="url(#pollenGlow)"/>\n')

        # Pollen particles drifting upward
        n_pollen = max(2, min(8, int(lum * 6)))
        for pi in range(n_pollen):
            px = tip_x + rng.uniform(-10, 10)
            py = tip_y + rng.uniform(-5, 5)
            pr = rng.uniform(5, 15)
            p_delay = delay + rng.uniform(0.5, 3)
            pollen_color = oklch(0.7, 0.10, (hue + 20) % 360)
            svg += (f'<circle cx="{px:.1f}" cy="{py:.1f}" r="1" '
                    f'fill="{pollen_color}" class="pollen-particle" '
                    f'style="--pr:{pr:.0f};--py:-{pr * 2:.0f}px;'
                    f'animation-delay:{p_delay:.1f}s;animation-duration:{3+rng.uniform(0,4):.1f}s"/>\n')

        svg += '</g>\n'

    svg += '</g>\n'

    if dark_mode:
        svg += f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#vig)"/>\n'

    svg += '</svg>\n'
    return svg


# =========================================================================
# Main
# =========================================================================

ART_TYPES = [
    ("ecosystem", "Ecosystem", generate_ecosystem),
    ("weather", "Weather Map", generate_weather_map),
    ("roots", "Root System", generate_root_system),
]

if __name__ == "__main__":
    out_dir = Path(".github/assets/img")
    out_dir.mkdir(parents=True, exist_ok=True)

    for pname, metrics in PROFILES.items():
        print(f"\n--- {metrics['label']} ---")
        for slug, label, gen_func in ART_TYPES:
            svg = gen_func(metrics, dark_mode=True)
            out = out_dir / f"proto-v6-{slug}-{pname}-dark.svg"
            out.write_text(svg, encoding="utf-8")
            print(f"  {label}: {len(svg)//1024} KB → {out}")

    print("\nDone! Open proto-v6-* files in browser.")
