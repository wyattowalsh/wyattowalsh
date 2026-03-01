"""
Generative Art Prototypes v8 — Light Theme, Actually Beautiful
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Previous versions failed because:
- Dark backgrounds (user prefers light)
- Too many thin, transparent strokes → washed-out look
- Overcomplicated data mappings distracted from visual beauty
- Bloom filters don't pop the same on dark bg in browser

This version: LIGHT backgrounds, BOLD color, STRONG visual presence.
Inspired by: watercolor, ink wash, botanical illustration, topographic maps.

Three distinct visual styles:
1. "Watercolor Cosmos" — Dense attractor as overlapping translucent dots,
   like pigment bleeding on wet paper. Rich saturated color pools.
2. "Ink Garden" — Thick-stroke organic branching with vivid gradients,
   like botanical ink drawings. Clear structure, bold presence.
3. "Topography" — Contribution data as contour/elevation map with
   filled color bands. Clean, informative, beautiful.
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

PROFILES = {
    "wyatt": {
        "label": "wyattowalsh", "stars": 42, "forks": 12, "watchers": 8,
        "followers": 85, "following": 60, "public_repos": 35, "orgs_count": 3,
        "contributions_last_year": 1200, "total_commits": 4800,
        "open_issues_count": 5, "network_count": 18,
        "repos": [
            {"name": "gnn-mol", "language": "Python", "stars": 12, "age_months": 24},
            {"name": "ball", "language": "Python", "stars": 8, "age_months": 36},
            {"name": "portfolio", "language": "TypeScript", "stars": 5, "age_months": 18},
            {"name": "dotfiles", "language": "Shell", "stars": 3, "age_months": 60},
            {"name": "nba-db", "language": "Python", "stars": 6, "age_months": 48},
            {"name": "wyattowalsh", "language": "Python", "stars": 2, "age_months": 12},
            {"name": "research", "language": "Jupyter Notebook", "stars": 4, "age_months": 30},
        ],
        "contributions_monthly": {
            "01":120,"02":95,"03":180,"04":210,"05":140,"06":60,
            "07":45,"08":80,"09":150,"10":200,"11":170,"12":90,
        },
    },
    "prolific": {
        "label": "Prolific OSS", "stars": 5200, "forks": 890, "watchers": 340,
        "followers": 12000, "following": 150, "public_repos": 180, "orgs_count": 8,
        "contributions_last_year": 3800, "total_commits": 42000,
        "open_issues_count": 120, "network_count": 2400,
        "repos": [
            {"name": f"p-{i}", "language": l, "stars": s, "age_months": a}
            for i,(l,s,a) in enumerate([
                ("Python",1200,84),("JavaScript",800,96),("TypeScript",600,48),
                ("Go",400,60),("Rust",350,36),("C++",280,108),
                ("Python",200,72),("Shell",150,120),("Ruby",120,90),
                ("Java",100,60),("Python",80,24),("TypeScript",60,36),
            ])
        ],
        "contributions_monthly": {
            "01":380,"02":420,"03":350,"04":400,"05":310,"06":280,
            "07":290,"08":320,"09":360,"10":400,"11":380,"12":310,
        },
    },
    "newcomer": {
        "label": "New Developer", "stars": 3, "forks": 1, "watchers": 2,
        "followers": 8, "following": 45, "public_repos": 6, "orgs_count": 1,
        "contributions_last_year": 180, "total_commits": 320,
        "open_issues_count": 2, "network_count": 3,
        "repos": [
            {"name": "hello-world", "language": "Python", "stars": 1, "age_months": 8},
            {"name": "todo-app", "language": "JavaScript", "stars": 2, "age_months": 5},
        ],
        "contributions_monthly": {"08":25,"09":30,"10":40,"11":35,"12":40},
    },
}

LANG_HUES = {
    "Python": 215, "JavaScript": 48, "TypeScript": 220, "Java": 8,
    "C++": 285, "C": 255, "Go": 178, "Rust": 22, "Ruby": 348,
    "Swift": 12, "Kotlin": 278, "Shell": 118, "HTML": 28, "CSS": 198,
    "Jupyter Notebook": 168, None: 155,
}

def _sh(m):
    s="-".join(str(m.get(k,0)) for k in sorted(m.keys()) if k not in ("label","repos","contributions_monthly"))
    return hashlib.sha256(s.encode()).hexdigest()
def _hf(h,a,b): return int(h[a:b],16)/(16**(b-a))
def _l2s(c): return 12.92*c if c<=0.0031308 else 1.055*c**(1/2.4)-0.055

def oklch(L,C,H):
    a=C*math.cos(math.radians(H));b=C*math.sin(math.radians(H))
    lc=L+0.3963377774*a+0.2158037573*b;mc=L-0.1055613458*a-0.0638541728*b
    sc=L-0.0894841775*a-1.2914855480*b
    l_=lc**3;m_=mc**3;s_=sc**3
    r=max(0,4.0767416621*l_-3.3077115913*m_+0.2309699292*s_)
    g=max(0,-1.2684380046*l_+2.6097574011*m_-0.3413193965*s_)
    bv=max(0,-0.0041960863*l_-0.7034186147*m_+1.7076147010*s_)
    r=max(0,min(1,_l2s(r)));g=max(0,min(1,_l2s(g)));bv=max(0,min(1,_l2s(bv)))
    return f"#{int(r*255):02x}{int(g*255):02x}{int(bv*255):02x}"

class Noise2D:
    def __init__(self,seed=0):
        rng=np.random.default_rng(seed);self.perm=np.tile(rng.permutation(256).astype(np.int32),2)
        a=rng.uniform(0,2*np.pi,256);self.grads=np.column_stack([np.cos(a),np.sin(a)])
    def _f(self,t): return t*t*t*(t*(t*6-15)+10)
    def noise(self,x,y):
        xi=int(math.floor(x))&255;yi=int(math.floor(y))&255;xf=x-math.floor(x);yf=y-math.floor(y)
        u=self._f(xf);v=self._f(yf)
        aa=self.perm[self.perm[xi]+yi];ab=self.perm[self.perm[xi]+yi+1]
        ba=self.perm[self.perm[xi+1]+yi];bb=self.perm[self.perm[xi+1]+yi+1]
        ga=self.grads[aa%256];gb=self.grads[ab%256];gc=self.grads[ba%256];gd=self.grads[bb%256]
        x1=(ga[0]*xf+ga[1]*yf)+u*((gc[0]*(xf-1)+gc[1]*yf)-(ga[0]*xf+ga[1]*yf))
        x2=(gb[0]*xf+gb[1]*(yf-1))+u*((gd[0]*(xf-1)+gd[1]*(yf-1))-(gb[0]*xf+gb[1]*(yf-1)))
        return x1+v*(x2-x1)
    def fbm(self,x,y,oct=4):
        v=0;a=1;f=1;t=0
        for _ in range(oct): v+=a*self.noise(x*f,y*f);t+=a;a*=0.5;f*=2
        return v/t


# =========================================================================
# 1. "WATERCOLOR COSMOS"
#
# Clifford attractor rendered as thousands of overlapping translucent
# circles — like wet watercolor pigment pooling on paper.
# Dense regions become rich saturated pools of color.
# Light paper-white background with subtle warm texture.
#
# Data:
# - Attractor params from hash (stars, forks, etc.)
# - contributions_last_year → particle count (density)
# - total_commits → iteration steps (intricacy)
# - Language hues → color palette selection
# - followers → how concentrated/tight the form is
# =========================================================================

def generate_watercolor(metrics: dict) -> str:
    h = _sh(metrics)
    rng = np.random.default_rng(int(h[:8], 16))

    # Attractor params
    a = -2.0 + _hf(h,0,4)*4.0
    b = -2.0 + _hf(h,4,8)*4.0
    c = -2.0 + _hf(h,8,12)*4.0
    d = -2.0 + _hf(h,12,16)*4.0
    use_dejong = int(h[16],16) > 7

    n_iters = max(50000, min(400000, 50000 + metrics.get("total_commits",0)*5))
    concentration = 1.0 + min(1.0, metrics.get("followers",10)/2000) * 0.5

    # Collect primary language hues for coloring
    repos = metrics.get("repos", [])
    hues = [LANG_HUES.get(r.get("language"), 160) for r in repos]
    if not hues: hues = [210, 340, 50]
    # Pick 3-4 dominant hues
    dominant_hues = list(set(hues))[:4]
    if len(dominant_hues) < 2: dominant_hues = [dominant_hues[0], (dominant_hues[0]+120)%360]

    # Run attractor
    x, y = 0.1, 0.1
    points = []
    for i in range(n_iters):
        if use_dejong:
            nx = math.sin(a*y) - math.cos(b*x)
            ny = math.sin(c*x) - math.cos(d*y)
        else:
            nx = math.sin(a*y) + c*math.cos(a*x)
            ny = math.sin(b*x) + d*math.cos(b*y)
        x, y = nx, ny
        if i > 100:  # skip transient
            points.append((x, y))

    if not points:
        points = [(0,0)]

    # Find bounds for mapping to canvas (use percentiles to handle outliers)
    xs = np.array([p[0] for p in points])
    ys = np.array([p[1] for p in points])
    x_min, x_max = float(np.percentile(xs, 2)), float(np.percentile(xs, 98))
    y_min, y_max = float(np.percentile(ys, 2)), float(np.percentile(ys, 98))
    x_range = max(0.01, x_max - x_min)
    y_range = max(0.01, y_max - y_min)
    scale = min((WIDTH-100)/x_range, (HEIGHT-100)/y_range)
    ox = CX - (x_min+x_max)/2 * scale
    oy = CY - (y_min+y_max)/2 * scale

    # Sample points for rendering (can't draw all 400k)
    sample_n = min(len(points), max(3000, min(15000, metrics.get("contributions_last_year",500)*3)))
    indices = rng.choice(len(points), size=sample_n, replace=False)
    indices.sort()

    # Compute density grid for sizing/opacity
    grid_res = 80
    density = np.zeros((grid_res, grid_res))
    for idx in indices:
        px, py = points[idx]
        sx = (px - x_min) / x_range
        sy = (py - y_min) / y_range
        gi = max(0, min(grid_res-1, int(sx * grid_res)))
        gj = max(0, min(grid_res-1, int(sy * grid_res)))
        density[gj, gi] += 1
    max_density = max(1, density.max())

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">
<defs>
  <filter id="paper" x="0%" y="0%" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.4" numOctaves="4" seed="42" result="noise"/>
    <feColorMatrix in="noise" type="matrix" result="warm"
      values="0 0 0 0 0.98  0 0 0 0 0.96  0 0 0 0 0.93  0 0 0 0.06 0"/>
    <feBlend in="SourceGraphic" in2="warm" mode="multiply"/>
  </filter>
  <filter id="watercolor" x="-10%" y="-10%" width="120%" height="120%">
    <feGaussianBlur stdDeviation="0.8"/>
  </filter>
</defs>
<rect width="{WIDTH}" height="{HEIGHT}" fill="#faf8f5"/>
<rect width="{WIDTH}" height="{HEIGHT}" filter="url(#paper)" fill="#faf8f5" opacity="0.5"/>
"""

    # Render as overlapping translucent circles
    svg += '<g filter="url(#watercolor)">\n'

    for idx in indices:
        px, py = points[idx]
        sx = ox + px * scale
        sy = oy + py * scale

        if sx < -10 or sx > WIDTH+10 or sy < -10 or sy > HEIGHT+10:
            continue

        # Grid cell density
        gi = max(0, min(grid_res-1, int((px-x_min)/x_range * grid_res)))
        gj = max(0, min(grid_res-1, int((py-y_min)/y_range * grid_res)))
        d = density[gj, gi] / max_density

        # Color: pick from dominant hues based on position in attractor
        frac = idx / len(points)
        hue_idx = int(frac * len(dominant_hues)) % len(dominant_hues)
        hue = dominant_hues[hue_idx]
        # Shift hue slightly by density (denser = warmer)
        hue = (hue + d * 20) % 360

        # On light bg: rich saturated mid-tones work best
        L = 0.55 + d * 0.15  # lighter in dense areas (watercolor pooling)
        C = 0.12 + d * 0.10  # more saturated in dense areas
        color = oklch(L, C, hue)

        # Size: larger in sparse areas (diffused pigment), smaller in dense (concentrated)
        r = 1.0 + (1-d) * 3.5
        # Opacity: more opaque in dense areas
        op = 0.04 + d * 0.12

        svg += f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{r:.1f}" fill="{color}" opacity="{op:.3f}"/>\n'

    svg += '</g>\n'

    # Subtle border frame
    svg += f'<rect x="20" y="20" width="{WIDTH-40}" height="{HEIGHT-40}" fill="none" stroke="#ddd8d0" stroke-width="0.5" rx="4"/>\n'

    svg += '</svg>\n'
    return svg


# =========================================================================
# 2. "INK GARDEN"
#
# Bold organic branching with thick strokes and vivid color on warm cream.
# Like botanical ink illustration — clear structure, confident marks.
#
# Data:
# - repos → branch clusters (each repo = one plant/organism)
# - language → stroke color
# - stars → flower bloom size at branch tips
# - contributions_monthly → background stipple density by region
# - orgs → number of distinct root systems
# =========================================================================

def generate_ink_garden(metrics: dict) -> str:
    h = _sh(metrics)
    rng = np.random.default_rng(int(h[:8], 16))
    noise = Noise2D(seed=int(h[8:16],16))

    repos = metrics.get("repos", [])
    monthly = metrics.get("contributions_monthly", {})
    orgs = metrics.get("orgs_count", 1)

    # Root positions — each org gets a root cluster
    root_positions = []
    for oi in range(max(1, min(orgs, 5))):
        rx = 100 + (oi / max(1, orgs-1)) * (WIDTH - 200) if orgs > 1 else CX
        rx += rng.uniform(-40, 40)
        ry = HEIGHT - 80 + rng.uniform(-20, 20)
        root_positions.append((rx, ry))

    # Assign repos to roots
    segments = []  # (x1,y1,x2,y2,sw,color,depth)
    bloom_circles = []  # (x,y,r,color) — flowers at tips

    for ri, repo in enumerate(repos):
        root_idx = ri % len(root_positions)
        rx, ry = root_positions[root_idx]
        lang = repo.get("language")
        hue = LANG_HUES.get(lang, 160)
        stars = repo.get("stars", 0)
        age = repo.get("age_months", 6)

        # Base color — vivid on light background
        base_color = oklch(0.45, 0.16, hue)
        light_color = oklch(0.60, 0.18, hue)  # for tips
        bloom_color = oklch(0.65, 0.20, (hue + 30) % 360)  # complementary accent

        # Growth direction: upward with noise
        main_angle = -math.pi/2 + rng.uniform(-0.4, 0.4)
        # Height based on age
        main_length = 80 + min(400, age * 4)

        max_depth = max(2, min(5, 2 + age // 15))

        def grow(x, y, angle, depth, length, sw):
            if depth > max_depth or length < 8 or len(segments) > 3000:
                return
            n_segs = max(2, int(length / 20))
            cx_, cy_ = x, y
            for si in range(n_segs):
                if len(segments) > 3000: break
                nv = noise.fbm(cx_*0.008 + ri*3, cy_*0.008, 2)
                a = angle + nv * 0.5
                sl = length / n_segs * rng.uniform(0.8, 1.2)
                nx_ = cx_ + sl * math.cos(a)
                ny_ = cy_ + sl * math.sin(a)
                # Boundary
                nx_ = max(30, min(WIDTH-30, nx_))
                ny_ = max(30, min(HEIGHT-30, ny_))

                d_frac = depth / max_depth
                c = oklch(0.45 + d_frac*0.15, 0.16 - d_frac*0.04, (hue + d_frac*15)%360)
                segments.append((cx_, cy_, nx_, ny_, sw, c, depth))
                cx_, cy_ = nx_, ny_
                angle = a

                # Branch
                if len(segments) < 3000 and rng.random() < 0.35 * (1-depth/max_depth):
                    fa = rng.uniform(0.4, 1.0) * rng.choice([-1, 1])
                    grow(cx_, cy_, a+fa, depth+1, length*rng.uniform(0.4, 0.7), sw*0.65)

            # Terminal: try to fork
            if depth < max_depth and len(segments) < 3000:
                for _ in range(rng.integers(1, 3)):
                    if len(segments) >= 3000: break
                    fa = rng.uniform(0.3, 0.9) * rng.choice([-1, 1])
                    grow(cx_, cy_, angle+fa, depth+1, length*rng.uniform(0.3, 0.6), sw*0.6)

            # Bloom at tip
            if depth >= max_depth - 1:
                br = 2 + stars * 0.8
                bloom_circles.append((cx_, cy_, min(12, br), bloom_color))

        stem_sw = 2.5 + min(2.0, age * 0.03)
        grow(rx, ry, main_angle, 0, main_length, stem_sw)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">
<defs>
  <filter id="ink" x="-5%" y="-5%" width="110%" height="110%">
    <feTurbulence type="fractalNoise" baseFrequency="0.08" numOctaves="2" seed="7" result="noise"/>
    <feDisplacementMap in="SourceGraphic" in2="noise" scale="1.5" xChannelSelector="R" yChannelSelector="G"/>
  </filter>
</defs>
<rect width="{WIDTH}" height="{HEIGHT}" fill="#faf7f2"/>
"""

    # Background stipple from monthly contributions (subtle texture)
    max_m = max(monthly.values()) if monthly else 100
    months_sorted = sorted(monthly.keys())
    for mi, mkey in enumerate(months_sorted):
        intensity = monthly[mkey] / max(1, max_m)
        region_x = 40 + (mi / max(1, len(months_sorted)-1)) * (WIDTH - 80) if len(months_sorted) > 1 else CX
        n_dots = int(intensity * 40)
        for di in range(n_dots):
            dx = region_x + rng.uniform(-50, 50)
            dy = rng.uniform(30, HEIGHT - 30)
            dr = rng.uniform(0.3, 0.8)
            svg += f'<circle cx="{dx:.0f}" cy="{dy:.0f}" r="{dr:.1f}" fill="#c8c0b5" opacity="{0.15 + intensity*0.15:.2f}"/>\n'

    # Ground line
    svg += f'<line x1="30" y1="{HEIGHT-60}" x2="{WIDTH-30}" y2="{HEIGHT-60}" stroke="#c8bfb0" stroke-width="1" opacity="0.4"/>\n'

    # Branches
    svg += '<g filter="url(#ink)">\n'
    for x1, y1, x2, y2, sw, color, depth in segments:
        mx = (x1+x2)/2 + rng.uniform(-1.5, 1.5)
        my = (y1+y2)/2 + rng.uniform(-1.5, 1.5)
        op = max(0.3, 0.85 - depth * 0.12)
        svg += (f'<path d="M{x1:.1f},{y1:.1f} Q{mx:.1f},{my:.1f} {x2:.1f},{y2:.1f}" '
                f'fill="none" stroke="{color}" stroke-width="{sw:.2f}" '
                f'opacity="{op:.2f}" stroke-linecap="round"/>\n')

    # Blooms
    for bx, by, br, bc in bloom_circles:
        svg += f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="{br:.1f}" fill="{bc}" opacity="0.6"/>\n'
        # Inner dot
        svg += f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="{br*0.35:.1f}" fill="{oklch(0.85,0.06,(LANG_HUES.get(None,160)+60)%360)}" opacity="0.7"/>\n'

    svg += '</g>\n'

    # Root marks at base
    for rx, ry in root_positions:
        svg += f'<circle cx="{rx:.0f}" cy="{ry:.0f}" r="4" fill="#8b7d6b" opacity="0.3"/>\n'

    svg += f'<rect x="20" y="20" width="{WIDTH-40}" height="{HEIGHT-40}" fill="none" stroke="#e0d8cc" stroke-width="0.5" rx="3"/>\n'
    svg += '</svg>\n'
    return svg


# =========================================================================
# 3. "TOPOGRAPHY"
#
# Contribution data as elevation contour map with filled color bands.
# Monthly activity creates peaks; repos create landmark points.
# Clean, map-like aesthetic with bold contour lines and soft fills.
#
# Data:
# - contributions_monthly → elevation at angular positions
# - repos → named landmark peaks
# - total_commits → overall elevation scale
# - followers → number of contour rings
# =========================================================================

def generate_topography(metrics: dict) -> str:
    h = _sh(metrics)
    rng = np.random.default_rng(int(h[:8], 16))
    noise = Noise2D(seed=int(h[8:16],16))

    monthly = metrics.get("contributions_monthly", {})
    repos = metrics.get("repos", [])
    total_commits = metrics.get("total_commits", 500)
    followers = metrics.get("followers", 10)

    # Build elevation field: noise + contribution peaks
    grid = 200
    elevation = np.zeros((grid, grid))

    # Base noise terrain
    for gy in range(grid):
        for gx in range(grid):
            nx = gx / grid * 6
            ny = gy / grid * 6
            elevation[gy, gx] = noise.fbm(nx, ny, 4) * 0.3

    # Contribution peaks at month angles
    max_m = max(monthly.values()) if monthly else 100
    months_sorted = sorted(monthly.keys())
    for mi, mkey in enumerate(months_sorted):
        intensity = monthly[mkey] / max(1, max_m)
        angle = -math.pi/2 + mi * 2 * math.pi / max(1, len(months_sorted))
        # Peak position
        pr = 0.2 + intensity * 0.15
        pcx = 0.5 + pr * math.cos(angle)
        pcy = 0.5 + pr * math.sin(angle)
        # Add gaussian peak
        sigma = 0.06 + intensity * 0.04
        peak_height = intensity * 0.7
        for gy in range(grid):
            for gx in range(grid):
                fx = gx / grid
                fy = gy / grid
                dx = fx - pcx
                dy = fy - pcy
                elevation[gy, gx] += peak_height * math.exp(-(dx*dx+dy*dy)/(2*sigma*sigma))

    # Repo landmark peaks
    for ri, repo in enumerate(repos):
        stars = repo.get("stars", 0)
        age = repo.get("age_months", 6)
        angle = ri * 2.399  # golden angle
        dist = 0.15 + (age / 120) * 0.25
        rcx = 0.5 + dist * math.cos(angle)
        rcy = 0.5 + dist * math.sin(angle)
        sigma = 0.03
        peak_h = 0.2 + stars * 0.03
        for gy in range(max(0,int((rcy-0.15)*grid)), min(grid,int((rcy+0.15)*grid))):
            for gx in range(max(0,int((rcx-0.15)*grid)), min(grid,int((rcx+0.15)*grid))):
                fx = gx/grid; fy = gy/grid
                dx = fx-rcx; dy = fy-rcy
                elevation[gy,gx] += peak_h * math.exp(-(dx*dx+dy*dy)/(2*sigma*sigma))

    # Normalize
    e_min = elevation.min()
    e_max = elevation.max()
    if e_max > e_min:
        elevation = (elevation - e_min) / (e_max - e_min)

    # Contour levels
    n_levels = max(6, min(16, 6 + followers // 20))
    levels = [i / n_levels for i in range(1, n_levels)]

    # Color palette for elevation bands — topographic map colors
    # Low=ocean blue → green → yellow → orange → brown → white (peak)
    topo_colors = [
        (0.0, "#e8f0f8"),   # lowest — pale blue
        (0.1, "#d0e4f0"),
        (0.2, "#b8dcc8"),   # green lowlands
        (0.3, "#a0d4a0"),
        (0.4, "#c8d888"),   # yellow-green
        (0.5, "#e8d870"),   # yellow
        (0.6, "#e8c050"),   # gold
        (0.7, "#d8a040"),   # orange
        (0.8, "#c88030"),   # brown
        (0.9, "#b06828"),
        (1.0, "#f0e8e0"),   # snow peak
    ]

    def topo_color(elev):
        for i in range(len(topo_colors)-1):
            t0, c0 = topo_colors[i]
            t1, c1 = topo_colors[i+1]
            if t0 <= elev <= t1:
                return c0  # use lower color (flat shading)
        return topo_colors[-1][1]

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">
<rect width="{WIDTH}" height="{HEIGHT}" fill="#f5f2ed"/>
"""

    # Fill elevation bands as small rectangles (pixelated topography)
    cell_w = WIDTH / grid
    cell_h = HEIGHT / grid
    # Downsample for fill
    fill_step = 4
    for gy in range(0, grid, fill_step):
        for gx in range(0, grid, fill_step):
            e = elevation[gy, gx]
            c = topo_color(e)
            sx = gx * cell_w
            sy = gy * cell_h
            sw = cell_w * fill_step
            sh = cell_h * fill_step
            svg += f'<rect x="{sx:.1f}" y="{sy:.1f}" width="{sw:.1f}" height="{sh:.1f}" fill="{c}" opacity="0.6"/>\n'

    # Contour lines (marching squares simplified — just draw level crossings)
    for level in levels:
        contour_segs = []
        for gy in range(grid-1):
            for gx in range(grid-1):
                # Check all 4 edges of the cell
                tl = elevation[gy, gx]
                tr = elevation[gy, gx+1]
                bl = elevation[gy+1, gx]
                br = elevation[gy+1, gx+1]

                edges = []
                # Top edge
                if (tl < level) != (tr < level):
                    t = (level - tl) / (tr - tl + 1e-10)
                    edges.append((gx + t, gy))
                # Bottom edge
                if (bl < level) != (br < level):
                    t = (level - bl) / (br - bl + 1e-10)
                    edges.append((gx + t, gy + 1))
                # Left edge
                if (tl < level) != (bl < level):
                    t = (level - tl) / (bl - tl + 1e-10)
                    edges.append((gx, gy + t))
                # Right edge
                if (tr < level) != (br < level):
                    t = (level - tr) / (br - tr + 1e-10)
                    edges.append((gx + 1, gy + t))

                if len(edges) >= 2:
                    x1 = edges[0][0] * cell_w
                    y1 = edges[0][1] * cell_h
                    x2 = edges[1][0] * cell_w
                    y2 = edges[1][1] * cell_h
                    contour_segs.append((x1, y1, x2, y2))

        # Draw contour segments
        is_major = levels.index(level) % 3 == 0
        sw = 0.8 if is_major else 0.3
        op = 0.5 if is_major else 0.25
        # Contour color based on elevation
        ci = int(level * 10)
        c_stroke = "#6b7b6b" if level < 0.5 else "#8b6b4b"

        for x1, y1, x2, y2 in contour_segs:
            svg += f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{c_stroke}" stroke-width="{sw}" opacity="{op:.2f}"/>\n'

    # Repo landmark markers
    for ri, repo in enumerate(repos):
        age = repo.get("age_months", 6)
        stars = repo.get("stars", 0)
        angle = ri * 2.399
        dist = 0.15 + (age / 120) * 0.25
        lx = (0.5 + dist * math.cos(angle)) * WIDTH
        ly = (0.5 + dist * math.sin(angle)) * HEIGHT
        # Triangle marker
        ts = 4 + stars * 0.5
        svg += (f'<polygon points="{lx:.0f},{ly-ts:.0f} {lx-ts*0.6:.0f},{ly+ts*0.3:.0f} {lx+ts*0.6:.0f},{ly+ts*0.3:.0f}" '
                f'fill="#d04030" opacity="0.7" stroke="#fff" stroke-width="0.3"/>\n')

    # Month labels around edge (contribution calendar)
    month_labels = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    for mi, mkey in enumerate(months_sorted):
        angle = -math.pi/2 + mi * 2 * math.pi / max(1, len(months_sorted))
        lx = CX + 370 * math.cos(angle)
        ly = CY + 370 * math.sin(angle)
        month_num = int(mkey) - 1 if mkey.isdigit() else mi
        label = month_labels[month_num % 12] if month_num < 12 else mkey
        intensity = monthly[mkey] / max(1, max_m)
        fc = f"rgba(80,60,40,{0.3+intensity*0.5:.2f})"
        svg += f'<text x="{lx:.0f}" y="{ly:.0f}" text-anchor="middle" dominant-baseline="central" font-family="Georgia,serif" font-size="9" fill="#5a4a3a" opacity="{0.3+intensity*0.4:.2f}">{label}</text>\n'

    svg += f'<rect x="15" y="15" width="{WIDTH-30}" height="{HEIGHT-30}" fill="none" stroke="#c8bfb0" stroke-width="0.8" rx="2"/>\n'
    svg += '</svg>\n'
    return svg


# =========================================================================
# Main
# =========================================================================

ART_TYPES = [
    ("watercolor", "Watercolor Cosmos", generate_watercolor),
    ("inkgarden", "Ink Garden", generate_ink_garden),
    ("topography", "Topography", generate_topography),
]

if __name__ == "__main__":
    out_dir = Path(".github/assets/img")
    out_dir.mkdir(parents=True, exist_ok=True)

    for pname, metrics in PROFILES.items():
        print(f"\n--- {metrics['label']} ---")
        for slug, label, gen_func in ART_TYPES:
            svg = gen_func(metrics)
            out = out_dir / f"proto-v8-{slug}-{pname}.svg"
            out.write_text(svg, encoding="utf-8")
            print(f"  {label}: {len(svg)//1024} KB → {out}")

    print("\nDone! Open proto-v8-* files in browser.")
