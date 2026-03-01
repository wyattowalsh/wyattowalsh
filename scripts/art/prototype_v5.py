"""
Generative Art Prototypes v5 — Animated Organic Hybrids
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Combines the best chaotic/organic forms from v4 with:
- CSS @keyframes animation (30s loops)
- Hybrid compositions (attractor + flow, dendrites + growth)
- Dramatic layered compositions with depth
- Nebula/turbulence backgrounds
- Per-path staggered reveal animations

Three showcase pieces, each a full 800x800 animated SVG.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path

import numpy as np

WIDTH = 800
HEIGHT = 800
CX = WIDTH / 2
CY = HEIGHT / 2
DURATION = 30  # seconds

PROFILES = {
    "wyatt": {
        "label": "wyattowalsh",
        "stars": 42, "forks": 12, "watchers": 8,
        "followers": 85, "following": 60,
        "public_repos": 35, "orgs_count": 3,
        "contributions_last_year": 1200, "total_commits": 4800,
        "open_issues_count": 5, "network_count": 18,
    },
    "prolific": {
        "label": "Prolific OSS",
        "stars": 5200, "forks": 890, "watchers": 340,
        "followers": 12000, "following": 150,
        "public_repos": 180, "orgs_count": 8,
        "contributions_last_year": 3800, "total_commits": 42000,
        "open_issues_count": 120, "network_count": 2400,
    },
    "newcomer": {
        "label": "New Developer",
        "stars": 3, "forks": 1, "watchers": 2,
        "followers": 8, "following": 45,
        "public_repos": 6, "orgs_count": 1,
        "contributions_last_year": 180, "total_commits": 320,
        "open_issues_count": 2, "network_count": 3,
    },
}


def _seed_hash(m: dict) -> str:
    s = "-".join(str(m.get(k, 0)) for k in sorted(m.keys()) if k != "label")
    return hashlib.sha256(s.encode()).hexdigest()

def _hf(h, a, b):
    return int(h[a:b], 16) / (16 ** (b - a))

# --- OKLCH ---
def _l2s(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1/2.4) - 0.055

def oklch(L, C, H):
    a = C * math.cos(math.radians(H))
    b = C * math.sin(math.radians(H))
    lc = L + 0.3963377774*a + 0.2158037573*b
    mc = L - 0.1055613458*a - 0.0638541728*b
    sc = L - 0.0894841775*a - 1.2914855480*b
    l_ = lc**3; m_ = mc**3; s_ = sc**3
    r = max(0, 4.0767416621*l_ - 3.3077115913*m_ + 0.2309699292*s_)
    g = max(0, -1.2684380046*l_ + 2.6097574011*m_ - 0.3413193965*s_)
    bv = max(0, -0.0041960863*l_ - 0.7034186147*m_ + 1.7076147010*s_)
    r = max(0, min(1, _l2s(r))); g = max(0, min(1, _l2s(g))); bv = max(0, min(1, _l2s(bv)))
    return f"#{int(r*255):02x}{int(g*255):02x}{int(bv*255):02x}"

PALETTES = {
    "bioluminescence": [
        (0.12,0.06,220),(0.25,0.12,200),(0.40,0.18,175),
        (0.55,0.20,160),(0.70,0.16,140),(0.85,0.08,120),
    ],
    "nebula": [
        (0.10,0.08,280),(0.25,0.14,300),(0.40,0.18,320),
        (0.55,0.16,200),(0.70,0.14,170),(0.88,0.06,60),
    ],
    "magma": [
        (0.08,0.06,0),(0.20,0.14,10),(0.35,0.20,25),
        (0.55,0.22,40),(0.75,0.18,55),(0.92,0.06,75),
    ],
    "aurora": [
        (0.15,0.08,260),(0.30,0.14,200),(0.50,0.20,160),
        (0.65,0.18,130),(0.75,0.14,100),(0.85,0.10,80),
    ],
    "deep_ocean": [
        (0.08,0.05,250),(0.18,0.10,230),(0.30,0.15,210),
        (0.45,0.18,195),(0.60,0.16,180),(0.78,0.10,170),
    ],
    "wildfire": [
        (0.10,0.08,350),(0.25,0.16,10),(0.45,0.22,25),
        (0.60,0.20,40),(0.78,0.14,55),(0.90,0.06,70),
    ],
    "fungal": [
        (0.12,0.06,30),(0.25,0.10,50),(0.38,0.14,80),
        (0.52,0.16,130),(0.65,0.12,170),(0.80,0.08,200),
    ],
}
PAL_NAMES = list(PALETTES.keys())

def pc(t, name, dark=True):
    stops = PALETTES.get(name, PALETTES["nebula"])
    t = max(0, min(1, t)); n = len(stops)
    idx = t*(n-1); i = int(idx); f = idx-i
    if i >= n-1: L,C,H = stops[-1]
    else:
        L0,C0,H0 = stops[i]; L1,C1,H1 = stops[i+1]
        dh = H1-H0
        if dh > 180: dh -= 360
        if dh < -180: dh += 360
        L = L0+(L1-L0)*f; C = C0+(C1-C0)*f; H = (H0+dh*f)%360
    if not dark: L = min(L+0.15, 0.75); C *= 1.2
    return oklch(L, C, H)


# --- Gradient noise ---
class Noise2D:
    def __init__(self, seed=0):
        rng = np.random.default_rng(seed)
        self.perm = np.tile(rng.permutation(256).astype(np.int32), 2)
        angles = rng.uniform(0, 2*np.pi, 256)
        self.grads = np.column_stack([np.cos(angles), np.sin(angles)])

    def _fade(self, t): return t*t*t*(t*(t*6-15)+10)

    def noise(self, x, y):
        xi = int(math.floor(x))&255; yi = int(math.floor(y))&255
        xf = x-math.floor(x); yf = y-math.floor(y)
        u = self._fade(xf); v = self._fade(yf)
        aa = self.perm[self.perm[xi]+yi]; ab = self.perm[self.perm[xi]+yi+1]
        ba = self.perm[self.perm[xi+1]+yi]; bb = self.perm[self.perm[xi+1]+yi+1]
        ga = self.grads[aa%256]; gb = self.grads[ab%256]
        gc = self.grads[ba%256]; gd = self.grads[bb%256]
        daa = ga[0]*xf+ga[1]*yf; dba = gc[0]*(xf-1)+gc[1]*yf
        dab = gb[0]*xf+gb[1]*(yf-1); dbb = gd[0]*(xf-1)+gd[1]*(yf-1)
        x1 = daa+u*(dba-daa); x2 = dab+u*(dbb-dab)
        return x1+v*(x2-x1)

    def fbm(self, x, y, octaves=4):
        val=0;amp=1;freq=1;ta=0
        for _ in range(octaves):
            val+=amp*self.noise(x*freq,y*freq); ta+=amp; amp*=0.5; freq*=2
        return val/ta


# =========================================================================
# PIECE 1: "Living Nebula" — Flowing attractor ribbons over turbulence
#   background with staggered CSS reveal animation
# =========================================================================

def generate_living_nebula(metrics: dict, dark_mode: bool = True) -> str:
    h = _seed_hash(metrics)
    rng = np.random.default_rng(int(h[:8], 16))

    # Attractor params from metrics
    a = -2.0 + _hf(h, 0, 4) * 4.0
    b = -2.0 + _hf(h, 4, 8) * 4.0
    c = -2.0 + _hf(h, 8, 12) * 4.0
    d = -2.0 + _hf(h, 12, 16) * 4.0
    use_dejong = int(h[16], 16) > 7

    n_traces = max(40, min(150, 40 + metrics.get("contributions_last_year", 0) // 12))
    steps_per = max(300, min(1500, 300 + metrics.get("total_commits", 0) // 6))

    pal_idx = int(h[17:19], 16) % len(PAL_NAMES)
    pal = PAL_NAMES[pal_idx]

    # Compute all traces
    all_paths = []  # list of (path_d_string, color, sw, base_opacity, distance_from_center)
    for t in range(n_traces):
        x = rng.uniform(-0.5, 0.5)
        y = rng.uniform(-0.5, 0.5)
        points = []
        for s in range(steps_per):
            if use_dejong:
                nx = math.sin(a*y) - math.cos(b*x)
                ny = math.sin(c*x) - math.cos(d*y)
            else:
                nx = math.sin(a*y) + c*math.cos(a*x)
                ny = math.sin(b*x) + d*math.cos(b*y)
            x, y = nx, ny
            sx = CX + x * 145
            sy = CY + y * 145
            if -20 <= sx <= WIDTH+20 and -20 <= sy <= HEIGHT+20:
                points.append((sx, sy))

        if len(points) < 15:
            continue

        # Break into color-segments
        seg_len = max(10, len(points) // 4)
        for si in range(0, len(points)-1, seg_len):
            seg = points[si:si+seg_len+1]
            if len(seg) < 3:
                continue

            tc = (t/n_traces + si/len(points)*0.3) % 1.0
            color = pc(tc, pal, dark_mode)

            frac = si / max(1, len(points))
            opacity = 0.12 + 0.35 * math.sin(frac * math.pi)
            sw = 0.3 + 0.9 * (1 - t/n_traces)

            # Build smooth path
            pd = f"M{seg[0][0]:.1f},{seg[0][1]:.1f}"
            for j in range(1, len(seg)-1, 2):
                if j+1 < len(seg):
                    pd += f" Q{seg[j][0]:.1f},{seg[j][1]:.1f} {seg[j+1][0]:.1f},{seg[j+1][1]:.1f}"
                else:
                    pd += f" L{seg[j][0]:.1f},{seg[j][1]:.1f}"

            # Distance from center (for animation ordering)
            avg_x = sum(p[0] for p in seg) / len(seg)
            avg_y = sum(p[1] for p in seg) / len(seg)
            dist = math.sqrt((avg_x-CX)**2 + (avg_y-CY)**2)

            all_paths.append((pd, color, sw, opacity, dist))

    # Sort by distance for reveal animation (center first)
    all_paths.sort(key=lambda p: p[4])

    # Build SVG
    bg1 = "#040410" if dark_mode else "#fafafe"
    bg2 = "#010108" if dark_mode else "#f0eef5"
    nebula_tint1 = pc(0.1, pal, dark_mode)
    nebula_tint2 = pc(0.6, pal, dark_mode)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">
<defs>
  <filter id="bloom" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="b1"/>
    <feGaussianBlur in="SourceGraphic" stdDeviation="7" result="b2"/>
    <feGaussianBlur in="SourceGraphic" stdDeviation="16" result="b3"/>
    <feColorMatrix in="b3" type="matrix" result="bright"
      values="1.8 0 0 0 0.12  0 1.8 0 0 0.12  0 0 1.8 0 0.12  0 0 0 0.5 0"/>
    <feMerge>
      <feMergeNode in="bright"/><feMergeNode in="b2"/>
      <feMergeNode in="b1"/><feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>
  <filter id="nebulaBg" x="0%" y="0%" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.003 0.004" numOctaves="6" seed="{int(h[20:24],16)%999}" result="turb"/>
    <feColorMatrix in="turb" type="matrix" result="tinted"
      values="0.08 0 0 0 0.02
              0 0.04 0 0 0.01
              0 0 0.15 0 0.06
              0 0 0 0.35 0"/>
  </filter>
  <filter id="glow" x="-100%" y="-100%" width="300%" height="300%">
    <feGaussianBlur stdDeviation="8" result="blur"/>
    <feColorMatrix in="blur" type="matrix"
      values="1.5 0 0 0 0.1  0 1.5 0 0 0.1  0 0 1.5 0 0.1  0 0 0 0.6 0"/>
  </filter>
  <radialGradient id="bg" cx="50%" cy="50%" r="60%">
    <stop offset="0%" stop-color="{bg1}"/>
    <stop offset="100%" stop-color="{bg2}"/>
  </radialGradient>
  <radialGradient id="vig" cx="50%" cy="50%" r="55%">
    <stop offset="35%" stop-color="black" stop-opacity="0"/>
    <stop offset="100%" stop-color="black" stop-opacity="0.65"/>
  </radialGradient>
</defs>
<style>
  @keyframes fadeIn {{
    from {{ opacity: 0; stroke-width: 0; }}
    to {{ opacity: var(--op); stroke-width: var(--sw); }}
  }}
  @keyframes pulse {{
    0%, 100% {{ opacity: 0.15; }}
    50% {{ opacity: 0.30; }}
  }}
  @keyframes drift {{
    0% {{ transform: translate(0, 0); }}
    33% {{ transform: translate(3px, -2px); }}
    66% {{ transform: translate(-2px, 3px); }}
    100% {{ transform: translate(0, 0); }}
  }}
  .trace {{
    animation: fadeIn 2s cubic-bezier(0.23, 1, 0.32, 1) forwards;
    opacity: 0;
  }}
  .nebula-layer {{
    animation: pulse 12s ease-in-out infinite;
  }}
  .star {{
    animation: pulse 3s ease-in-out infinite;
  }}
</style>
"""
    # Background
    svg += f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#bg)"/>\n'

    # Nebula background layer
    svg += f'<rect width="{WIDTH}" height="{HEIGHT}" filter="url(#nebulaBg)" class="nebula-layer"/>\n'

    # Starfield
    n_stars = max(30, min(120, metrics.get("stars", 10) + 30))
    for i in range(n_stars):
        sx = rng.uniform(20, WIDTH-20)
        sy = rng.uniform(20, HEIGHT-20)
        sr = rng.uniform(0.3, 1.2)
        sop = rng.uniform(0.1, 0.5)
        scolor = pc(rng.uniform(0, 1), pal, dark_mode)
        delay = rng.uniform(0, 5)
        svg += (f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="{sr:.1f}" '
                f'fill="{scolor}" class="star" '
                f'style="animation-delay:{delay:.1f}s;animation-duration:{2+rng.uniform(0,4):.1f}s"/>\n')

    # Attractor ribbons with staggered animation
    svg += '<g filter="url(#bloom)">\n'
    total = len(all_paths)
    for idx, (pd, color, sw, opacity, dist) in enumerate(all_paths):
        # Stagger delay: center paths appear first, ~80% of duration for all to appear
        delay = (idx / total) * DURATION * 0.75
        svg += (f'<path d="{pd}" fill="none" stroke="{color}" '
                f'stroke-linecap="round" stroke-linejoin="round" '
                f'class="trace" '
                f'style="--op:{opacity:.3f};--sw:{sw:.2f}px;'
                f'animation-delay:{delay:.2f}s"/>\n')
    svg += '</g>\n'

    # Center glow
    cg_color = pc(0.8, pal, dark_mode)
    svg += (f'<circle cx="{CX}" cy="{CY}" r="30" fill="{cg_color}" '
            f'opacity="0.06" filter="url(#glow)"/>\n')
    svg += (f'<circle cx="{CX}" cy="{CY}" r="4" fill="{cg_color}" opacity="0.6"/>\n')

    # Vignette
    if dark_mode:
        svg += f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#vig)"/>\n'

    svg += '</svg>\n'
    return svg


# =========================================================================
# PIECE 2: "Mycelium Network" — Dendrites + curl flow emanating from tips
# =========================================================================

def generate_mycelium(metrics: dict, dark_mode: bool = True) -> str:
    h = _seed_hash(metrics)
    rng = np.random.default_rng(int(h[:8], 16))
    noise = Noise2D(seed=int(h[8:16], 16))

    n_roots = max(3, min(7, 3 + metrics.get("orgs_count", 1)))
    max_depth = max(3, min(6, 3 + metrics.get("public_repos", 5) // 10))
    branch_prob = min(0.65, 0.35 + metrics.get("contributions_last_year", 0) / 4000)
    seg_length = max(18, min(40, 18 + metrics.get("total_commits", 0) // 600))
    noise_wander = 0.4 + _hf(h, 16, 20) * 0.7
    MAX_SEGMENTS = 5000

    pal_idx = int(h[20:22], 16) % len(PAL_NAMES)
    pal = PAL_NAMES[pal_idx]

    segments = []  # (x1,y1,x2,y2,depth,bid)
    tips = []  # terminal points for flow emanation

    def branch(x, y, angle, depth, length, bid):
        if depth > max_depth or length < 4 or len(segments) >= MAX_SEGMENTS:
            return
        n_segs = max(3, min(12, int(length / 4)))
        cx_, cy_ = x, y
        for s in range(n_segs):
            if len(segments) >= MAX_SEGMENTS:
                break
            n_val = noise.fbm(cx_*0.01 + bid*0.7, cy_*0.01, 3)
            pa = angle + n_val * noise_wander
            sl = length / n_segs * rng.uniform(0.7, 1.3)
            nx_ = cx_ + sl * math.cos(pa)
            ny_ = cy_ + sl * math.sin(pa)
            # Soft boundary
            if nx_ < 40 or nx_ > WIDTH-40: pa = math.pi - pa + rng.uniform(-0.3, 0.3)
            if ny_ < 40 or ny_ > HEIGHT-40: pa = -pa + rng.uniform(-0.3, 0.3)
            nx_ = cx_ + sl * math.cos(pa)
            ny_ = cy_ + sl * math.sin(pa)
            segments.append((cx_, cy_, nx_, ny_, depth, bid))
            cx_, cy_ = nx_, ny_
            angle = pa
            if len(segments) < MAX_SEGMENTS and rng.random() < branch_prob * (1 - depth/max_depth) * 0.45:
                fa = rng.uniform(0.3, 1.1) * rng.choice([-1, 1])
                branch(cx_, cy_, angle+fa, depth+1, length*rng.uniform(0.5, 0.7), bid+rng.integers(100))

        # Record tip
        tips.append((cx_, cy_, angle, depth))
        if depth < max_depth-1 and len(segments) < MAX_SEGMENTS and rng.random() < branch_prob:
            for _ in range(rng.integers(1, 3)):
                if len(segments) >= MAX_SEGMENTS: break
                fa = rng.uniform(0.25, 0.9) * rng.choice([-1, 1])
                branch(cx_, cy_, angle+fa, depth+1, length*rng.uniform(0.4, 0.65), bid+rng.integers(100))

    for i in range(n_roots):
        angle = i * 2 * math.pi / n_roots + rng.uniform(-0.4, 0.4)
        sr = rng.uniform(10, 40)
        sx = CX + sr * math.cos(angle)
        sy = CY + sr * math.sin(angle)
        branch(sx, sy, angle, 0, seg_length * (2.5 + rng.uniform(0, 1.5)), i*17)

    # Generate curl flow from tips (spore release / nutrient flow)
    flow_paths = []
    n_flow = min(len(tips), 80)
    flow_step = 1.8
    flow_steps = 60
    eps = 0.5
    ns = 0.004

    for ti in range(n_flow):
        tx, ty, ta, td = tips[ti % len(tips)]
        pts = [(tx, ty)]
        x, y = tx, ty
        for fs in range(flow_steps):
            nu = noise.fbm(x*ns, (y+500)*ns, 3)
            nd = noise.fbm(x*ns, (y-500)*ns, 3)
            nr = noise.fbm((x+500)*ns, y*ns, 3)
            nl = noise.fbm((x-500)*ns, y*ns, 3)
            vx = (nu - nd); vy = -(nr - nl)
            mag = math.sqrt(vx*vx + vy*vy) + 1e-10
            x += vx/mag * flow_step
            y += vy/mag * flow_step
            if x < -10 or x > WIDTH+10 or y < -10 or y > HEIGHT+10:
                break
            pts.append((x, y))
        if len(pts) > 5:
            flow_paths.append((pts, td))

    # Build SVG
    bg1 = "#030308" if dark_mode else "#fafafe"
    bg2 = "#010104" if dark_mode else "#f0eef5"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">
<defs>
  <filter id="bloom" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="b1"/>
    <feGaussianBlur in="SourceGraphic" stdDeviation="5" result="b2"/>
    <feGaussianBlur in="SourceGraphic" stdDeviation="12" result="b3"/>
    <feColorMatrix in="b3" type="matrix" result="bright"
      values="1.6 0 0 0 0.1  0 1.6 0 0 0.1  0 0 1.6 0 0.1  0 0 0 0.5 0"/>
    <feMerge>
      <feMergeNode in="bright"/><feMergeNode in="b2"/>
      <feMergeNode in="b1"/><feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>
  <filter id="softGlow" x="-80%" y="-80%" width="260%" height="260%">
    <feGaussianBlur stdDeviation="6" result="blur"/>
    <feColorMatrix in="blur" type="matrix"
      values="1.3 0 0 0 0.05  0 1.3 0 0 0.05  0 0 1.3 0 0.05  0 0 0 0.4 0"/>
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
  @keyframes growIn {{
    from {{ stroke-dashoffset: var(--len); opacity: 0.5; }}
    to {{ stroke-dashoffset: 0; opacity: var(--op); }}
  }}
  @keyframes flowIn {{
    from {{ stroke-dashoffset: var(--len); opacity: 0; }}
    to {{ stroke-dashoffset: 0; opacity: var(--op); }}
  }}
  @keyframes nodeGlow {{
    0%, 100% {{ r: var(--r); opacity: 0.2; }}
    50% {{ r: calc(var(--r) * 1.6); opacity: 0.5; }}
  }}
  .branch {{
    stroke-dasharray: var(--len);
    stroke-dashoffset: var(--len);
    animation: growIn var(--dur) cubic-bezier(0.23, 1, 0.32, 1) forwards;
  }}
  .flow {{
    stroke-dasharray: var(--len);
    stroke-dashoffset: var(--len);
    animation: flowIn var(--dur) cubic-bezier(0.4, 0, 0.2, 1) forwards;
  }}
  .node {{
    animation: nodeGlow 4s ease-in-out infinite;
  }}
</style>
"""
    svg += f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#bg)"/>\n'

    # Branches
    svg += '<g filter="url(#bloom)">\n'
    for idx, (x1, y1, x2, y2, depth, bid) in enumerate(segments):
        tc = (depth/max_depth*0.6 + (bid%100)/100*0.4) % 1.0
        color = pc(tc, pal, dark_mode)
        sw = max(0.3, 2.8 * (1 - depth/max_depth)**1.5)
        op = max(0.1, 0.55 * (1 - depth/max_depth*0.5))

        mx = (x1+x2)/2 + rng.uniform(-1.5, 1.5)
        my = (y1+y2)/2 + rng.uniform(-1.5, 1.5)
        pd = f"M{x1:.1f},{y1:.1f} Q{mx:.1f},{my:.1f} {x2:.1f},{y2:.1f}"

        seg_len = math.sqrt((x2-x1)**2 + (y2-y1)**2)
        # Animate: deeper branches appear later
        delay = (depth / max_depth) * DURATION * 0.4 + (idx / len(segments)) * DURATION * 0.3
        dur = 1.0 + depth * 0.3

        svg += (f'<path d="{pd}" fill="none" stroke="{color}" '
                f'stroke-linecap="round" class="branch" '
                f'style="--len:{seg_len:.0f};--op:{op:.3f};--sw:{sw:.1f};'
                f'--dur:{dur:.1f}s;animation-delay:{delay:.2f}s;stroke-width:{sw:.2f}"/>\n')

    # Flow from tips
    for fi, (pts, td) in enumerate(flow_paths):
        tc = (0.6 + fi/len(flow_paths)*0.4) % 1.0
        color = pc(tc, pal, dark_mode)
        sw = 0.4
        op = 0.15

        pd = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
        path_len = 0
        for j in range(1, len(pts)-1, 2):
            if j+1 < len(pts):
                pd += f" Q{pts[j][0]:.1f},{pts[j][1]:.1f} {pts[j+1][0]:.1f},{pts[j+1][1]:.1f}"
                path_len += math.sqrt((pts[j+1][0]-pts[j-1][0])**2 + (pts[j+1][1]-pts[j-1][1])**2)
            else:
                pd += f" L{pts[j][0]:.1f},{pts[j][1]:.1f}"

        delay = DURATION * 0.5 + fi / len(flow_paths) * DURATION * 0.4
        dur = 3.0

        svg += (f'<path d="{pd}" fill="none" stroke="{color}" '
                f'stroke-linecap="round" class="flow" '
                f'style="--len:{max(1,path_len):.0f};--op:{op:.3f};'
                f'--dur:{dur:.1f}s;animation-delay:{delay:.2f}s;stroke-width:{sw}"/>\n')

    # Glowing nodes at roots and major branch points
    root_pts = set()
    for x1, y1, x2, y2, depth, bid in segments:
        if depth < 2:
            root_pts.add((round(x1), round(y1)))
    for bx, by in list(root_pts)[:30]:
        r = 3
        color = pc(0.85, pal, dark_mode)
        svg += (f'<circle cx="{bx}" cy="{by}" fill="{color}" '
                f'class="node" style="--r:{r}px" r="{r}" '
                f'filter="url(#softGlow)"/>\n')

    svg += '</g>\n'

    # Center organism
    cg = pc(0.9, pal, dark_mode)
    svg += f'<circle cx="{CX}" cy="{CY}" r="6" fill="{cg}" opacity="0.4" filter="url(#softGlow)"/>\n'
    svg += f'<circle cx="{CX}" cy="{CY}" r="2" fill="{cg}" opacity="0.8"/>\n'

    if dark_mode:
        svg += f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#vig)"/>\n'

    svg += '</svg>\n'
    return svg


# =========================================================================
# PIECE 3: "Tidal Bloom" — Differential growth rings + curl flow field
#   organic wrinkled forms floating in a flowing current
# =========================================================================

def generate_tidal_bloom(metrics: dict, dark_mode: bool = True) -> str:
    h = _seed_hash(metrics)
    rng = np.random.default_rng(int(h[:8], 16))
    noise = Noise2D(seed=int(h[8:16], 16))

    # Differential growth params
    n_initial = max(80, min(160, 80 + metrics.get("public_repos", 10) * 2))
    growth_steps = max(100, min(300, 100 + metrics.get("contributions_last_year", 0) // 6))
    split_dist = max(2.5, min(5.0, 2.5 + metrics.get("followers", 0) / 1000))
    repel_dist = split_dist * 0.85
    noise_mag = 1.0 + _hf(h, 16, 20) * 1.5
    attract = 0.002 + _hf(h, 20, 24) * 0.003

    pal_idx = int(h[24:26], 16) % len(PAL_NAMES)
    pal = PAL_NAMES[pal_idx]

    n_rings = max(2, min(4, 2 + metrics.get("orgs_count", 1)))

    # Grow the rings
    all_rings = []
    for ri in range(n_rings):
        base_r = 40 + ri * (200 / n_rings)
        points = []
        for i in range(n_initial):
            angle = i * 2 * math.pi / n_initial
            x = CX + base_r * math.cos(angle)
            y = CY + base_r * math.sin(angle)
            points.append([x, y])

        ring_growth = max(40, growth_steps - ri * 40)
        for step in range(ring_growth):
            n = len(points)
            if n > 3000:
                break

            for i in range(n):
                x, y = points[i]
                dx = x - CX; dy = y - CY
                dist = math.sqrt(dx*dx + dy*dy) + 1e-10
                ox = dx/dist; oy = dy/dist
                nx_ = noise.fbm(x*0.008 + step*0.07 + ri, y*0.008, 3)
                ny_ = noise.fbm(x*0.008, y*0.008 + step*0.07 + ri, 3)
                push = noise_mag * (0.4 + 0.6 * noise.fbm(x*0.004 + ri, y*0.004, 2))
                points[i][0] += ox*push + nx_*noise_mag*0.6
                points[i][1] += oy*push + ny_*noise_mag*0.6
                points[i][0] -= dx * attract
                points[i][1] -= dy * attract

            for i in range(n):
                for di in [-2, -1, 1, 2]:
                    j = (i+di) % n
                    dx = points[i][0]-points[j][0]
                    dy = points[i][1]-points[j][1]
                    d = math.sqrt(dx*dx+dy*dy)+1e-10
                    if d < repel_dist and abs(di) > 1:
                        f = (repel_dist-d)*0.25
                        points[i][0] += dx/d*f
                        points[i][1] += dy/d*f

            smoothed = []
            for i in range(n):
                p = (i-1)%n; nx__ = (i+1)%n
                sx = points[i][0]*0.6 + points[p][0]*0.2 + points[nx__][0]*0.2
                sy = points[i][1]*0.6 + points[p][1]*0.2 + points[nx__][1]*0.2
                smoothed.append([sx, sy])
            points = smoothed

            new_points = []
            for i in range(n):
                new_points.append(points[i])
                j = (i+1)%n
                dx = points[j][0]-points[i][0]
                dy = points[j][1]-points[i][1]
                d = math.sqrt(dx*dx+dy*dy)
                if d > split_dist:
                    mx = (points[i][0]+points[j][0])/2 + rng.normal(0, 0.2)
                    my = (points[i][1]+points[j][1])/2 + rng.normal(0, 0.2)
                    new_points.append([mx, my])
            points = new_points

        all_rings.append(points)

    # Background curl flow
    n_flow = max(40, min(200, 40 + metrics.get("total_commits", 0) // 30))
    flow_scale = 0.003 + _hf(h, 28, 32) * 0.003
    flow_steps = 80
    flow_step_size = 2.5
    flow_paths = []

    for fi in range(n_flow):
        x = rng.uniform(20, WIDTH-20)
        y = rng.uniform(20, HEIGHT-20)
        pts = [(x, y)]
        for fs in range(flow_steps):
            nx_ = x * flow_scale; ny_ = y * flow_scale
            nu = noise.fbm(nx_, ny_+0.5, 3)
            nd = noise.fbm(nx_, ny_-0.5, 3)
            nr = noise.fbm(nx_+0.5, ny_, 3)
            nl = noise.fbm(nx_-0.5, ny_, 3)
            vx = (nu-nd); vy = -(nr-nl)
            mag = math.sqrt(vx*vx+vy*vy)+1e-10
            x += vx/mag*flow_step_size
            y += vy/mag*flow_step_size
            if x<-10 or x>WIDTH+10 or y<-10 or y>HEIGHT+10: break
            pts.append((x, y))
        if len(pts) > 8:
            flow_paths.append(pts)

    # Build SVG
    bg1 = "#040410" if dark_mode else "#fafafe"
    bg2 = "#010108" if dark_mode else "#f0eef5"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">
<defs>
  <filter id="bloom" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="b1"/>
    <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="b2"/>
    <feGaussianBlur in="SourceGraphic" stdDeviation="14" result="b3"/>
    <feColorMatrix in="b3" type="matrix" result="bright"
      values="1.5 0 0 0 0.08  0 1.5 0 0 0.08  0 0 1.5 0 0.08  0 0 0 0.45 0"/>
    <feMerge>
      <feMergeNode in="bright"/><feMergeNode in="b2"/>
      <feMergeNode in="b1"/><feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>
  <filter id="dof" x="-20%" y="-20%" width="140%" height="140%">
    <feGaussianBlur stdDeviation="3"/>
    <feColorMatrix type="saturate" values="0.5"/>
  </filter>
  <radialGradient id="bg" cx="50%" cy="50%" r="60%">
    <stop offset="0%" stop-color="{bg1}"/>
    <stop offset="100%" stop-color="{bg2}"/>
  </radialGradient>
  <radialGradient id="vig" cx="50%" cy="50%" r="55%">
    <stop offset="35%" stop-color="black" stop-opacity="0"/>
    <stop offset="100%" stop-color="black" stop-opacity="0.55"/>
  </radialGradient>
</defs>
<style>
  @keyframes drawRing {{
    from {{ stroke-dashoffset: var(--len); }}
    to {{ stroke-dashoffset: 0; }}
  }}
  @keyframes flowDraw {{
    from {{ stroke-dashoffset: var(--len); opacity: 0; }}
    to {{ stroke-dashoffset: 0; opacity: var(--op); }}
  }}
  .ring {{
    stroke-dasharray: var(--len);
    stroke-dashoffset: var(--len);
    animation: drawRing var(--dur) cubic-bezier(0.23, 1, 0.32, 1) forwards;
  }}
  .bgflow {{
    stroke-dasharray: var(--len);
    stroke-dashoffset: var(--len);
    animation: flowDraw var(--dur) cubic-bezier(0.4, 0, 0.2, 1) forwards;
  }}
</style>
"""
    svg += f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#bg)"/>\n'

    # Background flow (behind growth, with depth-of-field blur)
    svg += '<g filter="url(#dof)">\n'
    for fi, pts in enumerate(flow_paths):
        tc = (fi / len(flow_paths)) % 1.0
        color = pc(tc * 0.5, pal, dark_mode)  # muted background colors

        pd = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
        path_len = 0
        for j in range(1, len(pts)-1, 2):
            if j+1 < len(pts):
                pd += f" Q{pts[j][0]:.1f},{pts[j][1]:.1f} {pts[j+1][0]:.1f},{pts[j+1][1]:.1f}"
                path_len += math.sqrt((pts[j+1][0]-pts[max(0,j-1)][0])**2 + (pts[j+1][1]-pts[max(0,j-1)][1])**2)
            else:
                pd += f" L{pts[j][0]:.1f},{pts[j][1]:.1f}"

        delay = fi / len(flow_paths) * DURATION * 0.3
        dur = 4.0

        svg += (f'<path d="{pd}" fill="none" stroke="{color}" stroke-width="0.6" '
                f'stroke-linecap="round" class="bgflow" '
                f'style="--len:{max(1,path_len):.0f};--op:0.08;--dur:{dur:.1f}s;'
                f'animation-delay:{delay:.2f}s"/>\n')
    svg += '</g>\n'

    # Differential growth rings (foreground, sharp, with bloom)
    svg += '<g filter="url(#bloom)">\n'
    for ri, points in enumerate(all_rings):
        if len(points) < 3:
            continue

        tb = ri / n_rings
        color = pc(0.3 + tb * 0.5, pal, dark_mode)
        opacity = 0.25 + 0.25 * (1 - tb)
        sw = 0.6 + 1.0 * (1 - tb)

        pd = f"M{points[0][0]:.1f},{points[0][1]:.1f}"
        path_len = 0
        for i in range(1, len(points)-1, 2):
            if i+1 < len(points):
                pd += f" Q{points[i][0]:.1f},{points[i][1]:.1f} {points[i+1][0]:.1f},{points[i+1][1]:.1f}"
                path_len += math.sqrt((points[i+1][0]-points[max(0,i-1)][0])**2 +
                                       (points[i+1][1]-points[max(0,i-1)][1])**2)
            else:
                pd += f" L{points[i][0]:.1f},{points[i][1]:.1f}"
        pd += " Z"

        delay = ri * DURATION * 0.15
        dur = 6.0 + ri * 2

        svg += (f'<path d="{pd}" fill="none" stroke="{color}" '
                f'stroke-linecap="round" stroke-linejoin="round" class="ring" '
                f'style="--len:{max(1,path_len):.0f};--op:{opacity:.3f};--sw:{sw:.1f};'
                f'--dur:{dur:.1f}s;animation-delay:{delay:.2f}s;'
                f'stroke-width:{sw:.2f}"/>\n')

        # Subtle fill
        fill_c = pc(tb * 0.4, pal, dark_mode)
        svg += (f'<path d="{pd}" fill="{fill_c}" fill-opacity="{opacity*0.08:.4f}" '
                f'stroke="none" class="ring" '
                f'style="--len:{max(1,path_len):.0f};--op:1;--dur:{dur:.1f}s;'
                f'animation-delay:{delay:.2f}s"/>\n')

    svg += '</g>\n'

    if dark_mode:
        svg += f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#vig)"/>\n'

    svg += '</svg>\n'
    return svg


# =========================================================================
# Main
# =========================================================================

ART_TYPES = [
    ("nebula", "Living Nebula", generate_living_nebula),
    ("mycelium", "Mycelium Network", generate_mycelium),
    ("tidal", "Tidal Bloom", generate_tidal_bloom),
]

if __name__ == "__main__":
    out_dir = Path(".github/assets/img")
    out_dir.mkdir(parents=True, exist_ok=True)

    for pname, metrics in PROFILES.items():
        print(f"\n--- {metrics['label']} ---")
        for slug, label, gen_func in ART_TYPES:
            svg = gen_func(metrics, dark_mode=True)
            out = out_dir / f"proto-v5-{slug}-{pname}-dark.svg"
            out.write_text(svg, encoding="utf-8")
            print(f"  {label}: {len(svg)//1024} KB → {out}")

    print("\nDone! Open proto-v5-* files in browser.")
