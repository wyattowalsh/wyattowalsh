"""
Generative Art Prototypes v9 — Ink Garden & Topography Evolved
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Pushing both concepts way further:

INK GARDEN v2:
- Radial growth from center (not just upward) — more dynamic composition
- Multi-pass rendering: skeleton → bark texture → leaves → flowers → pollen
- Thicker, more confident marks with real stroke variation
- Elaborate flower heads (petal paths, not just circles)
- Leaves along branches — small curved strokes angled outward
- Cross-hatching shadow areas for depth on light bg
- Better color: richer, more saturated, wider range

TOPOGRAPHY v2:
- Smooth contour chains (connect marching-squares segments into paths)
- Richer color bands with smooth gradient transitions
- Hatching between contours for texture
- Water features: low-elevation areas as lakes with wave pattern
- Cartographic frame with scale bar, north arrow, legend
- Label placement for repo landmarks
- Ridge emphasis lines (thicker contours at peaks)
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
    "Shell": 118, "HTML": 28, "CSS": 198, "Jupyter Notebook": 168, None: 155,
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
# INK GARDEN v2 — Radial botanical with multi-layer detail
# =========================================================================

def generate_ink_garden_v2(metrics: dict) -> str:
    h = _sh(metrics)
    rng = np.random.default_rng(int(h[:8], 16))
    noise = Noise2D(seed=int(h[8:16],16))

    repos = metrics.get("repos", [])
    monthly = metrics.get("contributions_monthly", {})
    orgs = metrics.get("orgs_count", 1)
    followers = metrics.get("followers", 10)
    total_commits = metrics.get("total_commits", 500)

    MAX_SEGS = 5000

    # All branch segments: (x1,y1,x2,y2,sw,hue,depth,is_main)
    all_segs = []
    # Leaf positions: (x,y,angle,size,hue)
    leaves = []
    # Bloom positions: (x,y,size,hue,petal_count)
    blooms = []

    for ri, repo in enumerate(repos):
        lang = repo.get("language")
        hue = LANG_HUES.get(lang, 160)
        stars = repo.get("stars", 0)
        age = repo.get("age_months", 6)

        # Radial growth direction from center
        base_angle = ri * 2.399 + _hf(h, (ri*2)%60, (ri*2+2)%60+2) * 0.6 - 0.3
        # Length from age
        main_length = 60 + min(300, age * 3.5)
        # Start slightly off-center
        start_r = 15 + rng.uniform(0, 20)
        sx = CX + start_r * math.cos(base_angle)
        sy = CY + start_r * math.sin(base_angle)

        max_depth = max(2, min(5, 2 + age // 14))
        stem_sw = 3.0 + min(2.5, age * 0.04)

        def grow(x, y, angle, depth, length, sw):
            if depth > max_depth or length < 6 or len(all_segs) >= MAX_SEGS:
                return
            n_segs = max(2, int(length / 15))
            cx_, cy_ = x, y

            for si in range(n_segs):
                if len(all_segs) >= MAX_SEGS: break
                nv = noise.fbm(cx_*0.006 + ri*5, cy_*0.006, 3)
                a = angle + nv * 0.4 * (1 + depth * 0.3)
                sl = length / n_segs * rng.uniform(0.8, 1.2)
                nx_ = cx_ + sl * math.cos(a)
                ny_ = cy_ + sl * math.sin(a)
                # Keep in bounds
                dist = math.sqrt((nx_-CX)**2 + (ny_-CY)**2)
                if dist > 380:
                    a += (math.atan2(CY-ny_, CX-nx_) - a) * 0.3
                    nx_ = cx_ + sl * math.cos(a)
                    ny_ = cy_ + sl * math.sin(a)

                is_main = depth == 0
                all_segs.append((cx_, cy_, nx_, ny_, sw, hue, depth, is_main))

                # Add leaves along branches (not on main stem)
                if depth >= 1 and si % 2 == 0 and rng.random() < 0.6:
                    leaf_angle = a + rng.choice([-1, 1]) * (0.6 + rng.uniform(0, 0.5))
                    leaf_size = 4 + rng.uniform(0, 4) * (1 - depth/max_depth)
                    leaves.append((nx_, ny_, leaf_angle, leaf_size, (hue+30)%360))

                cx_, cy_ = nx_, ny_
                angle = a

                # Branch
                if len(all_segs) < MAX_SEGS and rng.random() < 0.4 * (1 - depth/max_depth):
                    fa = rng.uniform(0.3, 1.0) * rng.choice([-1, 1])
                    grow(cx_, cy_, a+fa, depth+1, length*rng.uniform(0.4, 0.7), sw*0.6)

            # Terminal fork
            if depth < max_depth and len(all_segs) < MAX_SEGS:
                n_forks = rng.integers(1, 3)
                for _ in range(n_forks):
                    if len(all_segs) >= MAX_SEGS: break
                    fa = rng.uniform(0.3, 0.9) * rng.choice([-1, 1])
                    grow(cx_, cy_, angle+fa, depth+1, length*rng.uniform(0.3, 0.6), sw*0.55)

            # Bloom at tips
            if depth >= max_depth - 1:
                n_petals = max(3, min(8, 3 + stars // 2))
                bloom_size = 4 + stars * 0.6
                blooms.append((cx_, cy_, min(15, bloom_size), hue, n_petals))

        grow(sx, sy, base_angle, 0, main_length, stem_sw)

    # --- BUILD SVG ---
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">
<defs>
  <filter id="ink" x="-3%" y="-3%" width="106%" height="106%">
    <feTurbulence type="fractalNoise" baseFrequency="0.06" numOctaves="3" seed="12" result="n"/>
    <feDisplacementMap in="SourceGraphic" in2="n" scale="1.2" xChannelSelector="R" yChannelSelector="G"/>
  </filter>
</defs>
<rect width="{WIDTH}" height="{HEIGHT}" fill="#faf6f0"/>
"""

    # Subtle background stipple from monthly activity
    max_m = max(monthly.values()) if monthly else 100
    for mkey, count in monthly.items():
        intensity = count / max(1, max_m)
        mi = int(mkey) - 1 if mkey.isdigit() else 0
        angle = mi * 2 * math.pi / 12
        cx_m = CX + 250 * math.cos(angle)
        cy_m = CY + 250 * math.sin(angle)
        n_dots = int(intensity * 30)
        for _ in range(n_dots):
            dx = cx_m + rng.normal(0, 60)
            dy = cy_m + rng.normal(0, 60)
            dr = rng.uniform(0.2, 0.6)
            svg += f'<circle cx="{dx:.0f}" cy="{dy:.0f}" r="{dr:.1f}" fill="#d0c8b8" opacity="{0.1+intensity*0.2:.2f}"/>\n'

    # Cross-hatching shadows in dense branch areas
    # (approximate: draw thin diagonal lines behind branches)
    branch_density = defaultdict(int)
    for x1,y1,x2,y2,sw,hue,depth,is_main in all_segs:
        gx = int((x1+x2)/2 / 40)
        gy = int((y1+y2)/2 / 40)
        branch_density[(gx,gy)] += 1

    max_bd = max(branch_density.values()) if branch_density else 1
    for (gx,gy), count in branch_density.items():
        if count < 3: continue
        density_frac = count / max_bd
        cx_h = gx * 40 + 20
        cy_h = gy * 40 + 20
        n_hatch = int(density_frac * 6)
        for hi in range(n_hatch):
            hx1 = cx_h - 15 + hi * 5
            hy1 = cy_h - 15
            hx2 = hx1 + 20
            hy2 = cy_h + 15
            svg += f'<line x1="{hx1:.0f}" y1="{hy1:.0f}" x2="{hx2:.0f}" y2="{hy2:.0f}" stroke="#c8bfb0" stroke-width="0.3" opacity="{density_frac*0.2:.3f}"/>\n'

    svg += '<g filter="url(#ink)">\n'

    # Pass 1: Main stems (thick, dark)
    for x1,y1,x2,y2,sw,hue,depth,is_main in all_segs:
        if not is_main: continue
        color = oklch(0.30, 0.08, hue)
        mx = (x1+x2)/2 + rng.uniform(-1, 1)
        my = (y1+y2)/2 + rng.uniform(-1, 1)
        svg += (f'<path d="M{x1:.1f},{y1:.1f} Q{mx:.1f},{my:.1f} {x2:.1f},{y2:.1f}" '
                f'fill="none" stroke="{color}" stroke-width="{sw:.1f}" '
                f'opacity="0.85" stroke-linecap="round"/>\n')

    # Pass 2: Secondary branches
    for x1,y1,x2,y2,sw,hue,depth,is_main in all_segs:
        if is_main: continue
        d_frac = depth / 5
        color = oklch(0.35 + d_frac*0.15, 0.12 + d_frac*0.04, hue)
        op = max(0.35, 0.80 - depth * 0.10)
        mx = (x1+x2)/2 + rng.uniform(-1.5, 1.5)
        my = (y1+y2)/2 + rng.uniform(-1.5, 1.5)
        svg += (f'<path d="M{x1:.1f},{y1:.1f} Q{mx:.1f},{my:.1f} {x2:.1f},{y2:.1f}" '
                f'fill="none" stroke="{color}" stroke-width="{sw:.1f}" '
                f'opacity="{op:.2f}" stroke-linecap="round"/>\n')

    # Pass 3: Leaves
    for lx, ly, la, ls, lh in leaves:
        # Leaf: a curved teardrop path
        tip_x = lx + ls * math.cos(la)
        tip_y = ly + ls * math.sin(la)
        # Control point perpendicular to leaf direction
        perp = la + math.pi/2
        cp1x = (lx + tip_x)/2 + ls*0.3 * math.cos(perp)
        cp1y = (ly + tip_y)/2 + ls*0.3 * math.sin(perp)
        cp2x = (lx + tip_x)/2 - ls*0.3 * math.cos(perp)
        cp2y = (ly + tip_y)/2 - ls*0.3 * math.sin(perp)

        leaf_c = oklch(0.48, 0.14, lh)
        svg += (f'<path d="M{lx:.1f},{ly:.1f} Q{cp1x:.1f},{cp1y:.1f} {tip_x:.1f},{tip_y:.1f} '
                f'Q{cp2x:.1f},{cp2y:.1f} {lx:.1f},{ly:.1f}" '
                f'fill="{leaf_c}" opacity="0.45" stroke="{oklch(0.38,0.10,lh)}" stroke-width="0.3"/>\n')

    # Pass 4: Blooms (petal flowers, not just circles)
    for bx, by, bs, bh, n_petals in blooms:
        petal_c = oklch(0.60, 0.20, bh)
        petal_dark = oklch(0.50, 0.16, bh)
        center_c = oklch(0.75, 0.12, (bh + 60) % 360)

        for pi in range(n_petals):
            pa = pi * 2 * math.pi / n_petals + rng.uniform(-0.1, 0.1)
            # Petal as an elliptical arc
            pr = bs * 0.7
            tip_x = bx + pr * math.cos(pa)
            tip_y = by + pr * math.sin(pa)
            # Side control points
            side_a = pa + 0.4
            side_b = pa - 0.4
            cp_r = pr * 0.6
            cp1x = bx + cp_r * math.cos(side_a)
            cp1y = by + cp_r * math.sin(side_a)
            cp2x = bx + cp_r * math.cos(side_b)
            cp2y = by + cp_r * math.sin(side_b)

            svg += (f'<path d="M{bx:.1f},{by:.1f} Q{cp1x:.1f},{cp1y:.1f} {tip_x:.1f},{tip_y:.1f} '
                    f'Q{cp2x:.1f},{cp2y:.1f} {bx:.1f},{by:.1f}" '
                    f'fill="{petal_c}" opacity="0.55" stroke="{petal_dark}" stroke-width="0.3"/>\n')

        # Center
        svg += f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="{bs*0.2:.1f}" fill="{center_c}" opacity="0.8"/>\n'

    svg += '</g>\n'

    # Center mark
    svg += f'<circle cx="{CX}" cy="{CY}" r="5" fill="none" stroke="#b0a898" stroke-width="1" opacity="0.3"/>\n'
    svg += f'<circle cx="{CX}" cy="{CY}" r="1.5" fill="#8a7a6a" opacity="0.4"/>\n'

    # Frame
    svg += f'<rect x="18" y="18" width="{WIDTH-36}" height="{HEIGHT-36}" fill="none" stroke="#d8d0c4" stroke-width="0.6" rx="3"/>\n'

    svg += '</svg>\n'
    return svg


# =========================================================================
# TOPOGRAPHY v2 — Smooth contours, hatching, water, cartographic details
# =========================================================================

def generate_topography_v2(metrics: dict) -> str:
    h = _sh(metrics)
    rng = np.random.default_rng(int(h[:8], 16))
    noise = Noise2D(seed=int(h[8:16],16))

    monthly = metrics.get("contributions_monthly", {})
    repos = metrics.get("repos", [])
    total_commits = metrics.get("total_commits", 500)
    followers = metrics.get("followers", 10)
    contributions = metrics.get("contributions_last_year", 200)

    grid = 150
    elevation = np.zeros((grid, grid))

    # Base terrain noise
    terrain_octaves = max(3, min(6, 3 + total_commits // 8000))
    for gy in range(grid):
        for gx in range(grid):
            nx = gx / grid * 5
            ny = gy / grid * 5
            elevation[gy, gx] = noise.fbm(nx, ny, terrain_octaves) * 0.25

    # Contribution peaks
    max_m = max(monthly.values()) if monthly else 100
    months_sorted = sorted(monthly.keys())
    for mi, mkey in enumerate(months_sorted):
        intensity = monthly[mkey] / max(1, max_m)
        angle = -math.pi/2 + mi * 2 * math.pi / max(1, len(months_sorted))
        pr = 0.18 + intensity * 0.12
        pcx = 0.5 + pr * math.cos(angle)
        pcy = 0.5 + pr * math.sin(angle)
        sigma = 0.05 + intensity * 0.04
        peak_h = intensity * 0.6
        # Optimized: only compute near peak
        y_lo = max(0, int((pcy-3*sigma)*grid))
        y_hi = min(grid, int((pcy+3*sigma)*grid)+1)
        x_lo = max(0, int((pcx-3*sigma)*grid))
        x_hi = min(grid, int((pcx+3*sigma)*grid)+1)
        for gy in range(y_lo, y_hi):
            for gx in range(x_lo, x_hi):
                fx = gx/grid; fy = gy/grid
                dx = fx-pcx; dy = fy-pcy
                elevation[gy,gx] += peak_h * math.exp(-(dx*dx+dy*dy)/(2*sigma*sigma))

    # Repo landmark peaks
    repo_positions = []
    for ri, repo in enumerate(repos):
        stars = repo.get("stars", 0)
        age = repo.get("age_months", 6)
        angle = ri * 2.399
        dist = 0.12 + min(0.3, age / 120 * 0.3)
        rcx = 0.5 + dist * math.cos(angle)
        rcy = 0.5 + dist * math.sin(angle)
        sigma = 0.025
        peak_h = 0.15 + min(0.4, stars * 0.02)
        y_lo = max(0, int((rcy-3*sigma)*grid))
        y_hi = min(grid, int((rcy+3*sigma)*grid)+1)
        x_lo = max(0, int((rcx-3*sigma)*grid))
        x_hi = min(grid, int((rcx+3*sigma)*grid)+1)
        for gy in range(y_lo, y_hi):
            for gx in range(x_lo, x_hi):
                fx = gx/grid; fy = gy/grid
                dx = fx-rcx; dy = fy-rcy
                elevation[gy,gx] += peak_h * math.exp(-(dx*dx+dy*dy)/(2*sigma*sigma))
        repo_positions.append((rcx, rcy, repo))

    # Central peak (your profile)
    for gy in range(grid):
        for gx in range(grid):
            fx = gx/grid; fy = gy/grid
            dx = fx-0.5; dy = fy-0.5
            elevation[gy,gx] += 0.3 * math.exp(-(dx*dx+dy*dy)/(2*0.08*0.08))

    # Normalize
    e_min = elevation.min(); e_max = elevation.max()
    if e_max > e_min:
        elevation = (elevation - e_min) / (e_max - e_min)

    # Color palette — rich topo colors
    def topo_hex(e):
        # Water < 0.15, land above
        if e < 0.12: return "#dce8f0"  # deep water
        if e < 0.18: return "#e0ecf2"  # shallow water
        if e < 0.25: return "#d4e4ca"  # coastal lowland
        if e < 0.35: return "#c0d8a0"  # lowland green
        if e < 0.45: return "#a8cc80"  # green
        if e < 0.55: return "#d0cc70"  # yellow-green
        if e < 0.65: return "#e0b858"  # gold
        if e < 0.75: return "#d09840"  # orange
        if e < 0.85: return "#c07838"  # brown
        if e < 0.92: return "#a86030"  # dark brown
        return "#efe8e0"  # snow

    # Contour levels
    n_levels = max(8, min(20, 8 + followers // 15))
    levels = [i / n_levels for i in range(1, n_levels)]

    # Marching squares → chained contour paths
    cell_w = WIDTH / grid
    cell_h = HEIGHT / grid

    def extract_contours(level):
        """Extract contour segments and chain them into paths."""
        seg_list = []
        for gy in range(grid-1):
            for gx in range(grid-1):
                tl=elevation[gy,gx];tr=elevation[gy,gx+1]
                bl=elevation[gy+1,gx];br=elevation[gy+1,gx+1]
                edges=[]
                if (tl<level)!=(tr<level):
                    t=(level-tl)/(tr-tl+1e-10)
                    edges.append(((gx+t)*cell_w, gy*cell_h))
                if (bl<level)!=(br<level):
                    t=(level-bl)/(br-bl+1e-10)
                    edges.append(((gx+t)*cell_w, (gy+1)*cell_h))
                if (tl<level)!=(bl<level):
                    t=(level-tl)/(bl-tl+1e-10)
                    edges.append((gx*cell_w, (gy+t)*cell_h))
                if (tr<level)!=(br<level):
                    t=(level-tr)/(br-tr+1e-10)
                    edges.append(((gx+1)*cell_w, (gy+t)*cell_h))
                if len(edges)>=2:
                    seg_list.append((edges[0], edges[1]))

        # Chain segments into paths (greedy nearest-neighbor)
        if not seg_list:
            return []
        used = [False]*len(seg_list)
        chains = []

        for start_i in range(len(seg_list)):
            if used[start_i]: continue
            used[start_i] = True
            chain = [seg_list[start_i][0], seg_list[start_i][1]]
            # Extend forward
            changed = True
            while changed:
                changed = False
                last = chain[-1]
                best_d = 8.0  # max connection distance
                best_j = -1
                best_end = 0
                for j in range(len(seg_list)):
                    if used[j]: continue
                    for end_idx in [0, 1]:
                        pt = seg_list[j][end_idx]
                        d = math.sqrt((pt[0]-last[0])**2 + (pt[1]-last[1])**2)
                        if d < best_d:
                            best_d = d; best_j = j; best_end = end_idx
                if best_j >= 0:
                    used[best_j] = True
                    if best_end == 0:
                        chain.append(seg_list[best_j][1])
                    else:
                        chain.append(seg_list[best_j][0])
                    changed = True
            if len(chain) >= 3:
                chains.append(chain)
        return chains

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">
<rect width="{WIDTH}" height="{HEIGHT}" fill="#f8f4ee"/>
"""

    # Fill color bands
    fill_step = 3
    for gy in range(0, grid, fill_step):
        for gx in range(0, grid, fill_step):
            e = elevation[gy, gx]
            c = topo_hex(e)
            sx = gx * cell_w; sy = gy * cell_h
            sw = cell_w * fill_step + 0.5; sh = cell_h * fill_step + 0.5
            svg += f'<rect x="{sx:.1f}" y="{sy:.1f}" width="{sw:.1f}" height="{sh:.1f}" fill="{c}" opacity="0.7"/>\n'

    # Water wave pattern for low-elevation areas
    for gy in range(0, grid, 8):
        for gx in range(0, grid, 2):
            e = elevation[min(gy, grid-1), min(gx, grid-1)]
            if e < 0.15:
                wx = gx * cell_w
                wy = gy * cell_h + math.sin(gx * 0.3) * 2
                wx2 = (gx+2) * cell_w
                wy2 = gy * cell_h + math.sin((gx+2) * 0.3) * 2
                svg += f'<line x1="{wx:.1f}" y1="{wy:.1f}" x2="{wx2:.1f}" y2="{wy2:.1f}" stroke="#b8d0e0" stroke-width="0.3" opacity="0.3"/>\n'

    # Contour lines — smooth chains
    for li, level in enumerate(levels):
        chains = extract_contours(level)
        is_major = li % 4 == 0
        sw = 0.9 if is_major else 0.35
        stroke_color = "#5a6858" if level < 0.5 else "#7a5a3a"
        op = 0.55 if is_major else 0.25

        for chain in chains:
            if len(chain) < 2: continue
            pd = f"M{chain[0][0]:.1f},{chain[0][1]:.1f}"
            # Smooth with quadratic beziers
            for j in range(1, len(chain)-1, 2):
                if j+1 < len(chain):
                    pd += f" Q{chain[j][0]:.1f},{chain[j][1]:.1f} {chain[j+1][0]:.1f},{chain[j+1][1]:.1f}"
                else:
                    pd += f" L{chain[j][0]:.1f},{chain[j][1]:.1f}"
            svg += f'<path d="{pd}" fill="none" stroke="{stroke_color}" stroke-width="{sw}" opacity="{op:.2f}" stroke-linecap="round" stroke-linejoin="round"/>\n'

        # Elevation label on major contours
        if is_major and chains:
            longest = max(chains, key=len)
            mid = longest[len(longest)//2]
            elev_label = f"{int(level * 1000)}m"
            svg += f'<text x="{mid[0]:.0f}" y="{mid[1]:.0f}" font-family="Georgia,serif" font-size="7" fill="{stroke_color}" opacity="0.5" text-anchor="middle">{elev_label}</text>\n'

    # Hatching between specific contour bands for texture
    for gy in range(0, grid, 6):
        for gx in range(0, grid, 6):
            e = elevation[min(gy,grid-1), min(gx,grid-1)]
            if 0.6 < e < 0.85:  # Mountain zone hatching
                hx = gx * cell_w; hy = gy * cell_h
                hatch_len = 8
                svg += f'<line x1="{hx:.0f}" y1="{hy:.0f}" x2="{hx+hatch_len:.0f}" y2="{hy+hatch_len*0.7:.0f}" stroke="#a08060" stroke-width="0.2" opacity="0.15"/>\n'

    # Repo landmarks with labels
    for rcx, rcy, repo in repo_positions:
        lx = rcx * WIDTH; ly = rcy * HEIGHT
        stars = repo.get("stars", 0)
        name = repo.get("name", "")
        lang = repo.get("language")
        hue = LANG_HUES.get(lang, 160)
        marker_c = oklch(0.45, 0.18, hue)

        # Filled circle marker
        mr = 3 + min(5, stars * 0.4)
        svg += f'<circle cx="{lx:.0f}" cy="{ly:.0f}" r="{mr:.1f}" fill="{marker_c}" opacity="0.75" stroke="#fff" stroke-width="0.6"/>\n'

        # Label
        svg += f'<text x="{lx+mr+3:.0f}" y="{ly+3:.0f}" font-family="Georgia,serif" font-size="7" fill="#4a3a2a" opacity="0.6">{name}</text>\n'

    # Center marker: your profile
    svg += f'<circle cx="{CX}" cy="{CY}" r="4" fill="#d04030" opacity="0.7" stroke="#fff" stroke-width="0.8"/>\n'
    svg += f'<text x="{CX+8}" y="{CY+3}" font-family="Georgia,serif" font-size="8" fill="#4a3a2a" font-weight="bold" opacity="0.7">{metrics.get("label","")}</text>\n'

    # Month markers around edge
    month_labels = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    for mi, mkey in enumerate(months_sorted):
        angle = -math.pi/2 + mi * 2 * math.pi / max(1, len(months_sorted))
        lx = CX + 375 * math.cos(angle)
        ly = CY + 375 * math.sin(angle)
        month_num = int(mkey) - 1 if mkey.isdigit() else mi
        label = month_labels[month_num % 12]
        intensity = monthly[mkey] / max(1, max_m)
        svg += f'<text x="{lx:.0f}" y="{ly:.0f}" text-anchor="middle" dominant-baseline="central" font-family="Georgia,serif" font-size="8" fill="#5a4a3a" opacity="{0.3+intensity*0.5:.2f}">{label}</text>\n'
        # Tick
        tx1 = CX + 362 * math.cos(angle); ty1 = CY + 362 * math.sin(angle)
        tx2 = CX + 368 * math.cos(angle); ty2 = CY + 368 * math.sin(angle)
        svg += f'<line x1="{tx1:.0f}" y1="{ty1:.0f}" x2="{tx2:.0f}" y2="{ty2:.0f}" stroke="#8a7a6a" stroke-width="0.5" opacity="0.4"/>\n'

    # Cartographic frame
    svg += f'<rect x="12" y="12" width="{WIDTH-24}" height="{HEIGHT-24}" fill="none" stroke="#a09080" stroke-width="1" rx="2"/>\n'
    svg += f'<rect x="15" y="15" width="{WIDTH-30}" height="{HEIGHT-30}" fill="none" stroke="#c8bfb0" stroke-width="0.3" rx="1"/>\n'

    # Scale bar
    svg += f'<line x1="30" y1="{HEIGHT-30}" x2="130" y2="{HEIGHT-30}" stroke="#5a4a3a" stroke-width="1.2"/>\n'
    svg += f'<line x1="30" y1="{HEIGHT-33}" x2="30" y2="{HEIGHT-27}" stroke="#5a4a3a" stroke-width="0.8"/>\n'
    svg += f'<line x1="130" y1="{HEIGHT-33}" x2="130" y2="{HEIGHT-27}" stroke="#5a4a3a" stroke-width="0.8"/>\n'
    svg += f'<text x="80" y="{HEIGHT-35}" text-anchor="middle" font-family="Georgia,serif" font-size="7" fill="#5a4a3a" opacity="0.6">{contributions} contributions</text>\n'

    # North arrow
    svg += f'<polygon points="{WIDTH-35},{35} {WIDTH-40},{55} {WIDTH-35},{50} {WIDTH-30},{55}" fill="#5a4a3a" opacity="0.4"/>\n'
    svg += f'<text x="{WIDTH-35}" y="{30}" text-anchor="middle" font-family="Georgia,serif" font-size="8" fill="#5a4a3a" opacity="0.5">N</text>\n'

    svg += '</svg>\n'
    return svg


# =========================================================================
# Main
# =========================================================================

if __name__ == "__main__":
    out_dir = Path(".github/assets/img")
    out_dir.mkdir(parents=True, exist_ok=True)

    for pname, metrics in PROFILES.items():
        print(f"\n--- {metrics['label']} ---")
        for slug, gen in [("inkgarden2", generate_ink_garden_v2), ("topo2", generate_topography_v2)]:
            svg = gen(metrics)
            out = out_dir / f"proto-v9-{slug}-{pname}.svg"
            out.write_text(svg, encoding="utf-8")
            print(f"  {slug}: {len(svg)//1024} KB → {out}")

    print("\nDone!")
