"""
Generative Art Prototypes v10 — TO THE MF LIMIT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Everything cranked to 11. Botanical illustration meets generative art.

INK GARDEN ULTIMATE:
- Root system underground (forks = mycorrhizal network)
- Soil strata layers (account age = geological depth)
- Bark texture on main stems
- Detailed multi-petal flowers with stamens
- Butterflies (watchers), bees (contributors), dragonflies (orgs)
- Spider webs between branches (network connections)
- Mushrooms at base (open issues decomposing)
- Falling petals/seeds (star events)
- Dew drops on leaves
- Vine tendrils wrapping stems
- Ground cover: grass, fallen leaves, moss
- Botanical illustration labels with leader lines
- Ornate border with corner flourishes
- Paper aging: foxing spots, edge darkening
- Multiple ink weights and colors

TOPOGRAPHY ULTIMATE:
- Dense contour lines with index contours
- Full hillshade/hachure rendering
- River systems flowing downhill with tributaries
- Lakes with bathymetric contours
- Vegetation symbols (tree patterns)
- Settlement symbols at high-star repos
- Trail network connecting repos
- Ornate compass rose
- Full legend with 10+ symbol types
- Coordinate grid overlay
- Elevation profile cross-section along bottom
- Ornate title cartouche with decorative border
- Spot heights with triangle markers
- Cliff/escarpment symbols
- Glacier patterns at peaks
- Marsh/wetland symbols
- Bridge symbols at path-river crossings
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
# INK GARDEN ULTIMATE — Full botanical illustration
# =========================================================================

def generate_ink_garden_ultimate(metrics: dict) -> str:
    h = _sh(metrics)
    rng = np.random.default_rng(int(h[:8], 16))
    noise = Noise2D(seed=int(h[8:16],16))

    repos = metrics.get("repos", [])
    monthly = metrics.get("contributions_monthly", {})
    orgs = metrics.get("orgs_count", 1)
    followers = metrics.get("followers", 10)
    forks = metrics.get("forks", 0)
    watchers = metrics.get("watchers", 0)
    total_commits = metrics.get("total_commits", 500)
    open_issues = metrics.get("open_issues_count", 0)
    network = metrics.get("network_count", 0)
    stars = metrics.get("stars", 0)
    contributions = metrics.get("contributions_last_year", 200)

    MAX_SEGS = 8000

    # Ground line — slightly above center, with gentle hills
    GROUND_Y = CY + 40
    def ground_y_at(x):
        return GROUND_Y + noise.noise(x*0.008, 0) * 25 + noise.noise(x*0.02, 5) * 8

    # Collect all visual elements
    all_segs = []     # (x1,y1,x2,y2,sw,hue,depth,is_main,repo_idx)
    roots = []        # (x1,y1,x2,y2,sw,hue,depth)
    leaves = []       # (x,y,angle,size,hue,vein)
    blooms = []       # (x,y,size,hue,petal_count,petal_layers)
    buds = []         # (x,y,size,hue)
    berries = []      # (x,y,size,hue)
    tendrils = []     # list of point lists
    mushrooms = []    # (x,y,size,hue)
    insects = []      # (x,y,type,size,hue) — butterfly/bee/dragonfly
    webs = []         # (cx,cy,radius,n_spokes)
    dew_drops = []    # (x,y,size)
    seeds = []        # (x,y,angle,size) — falling seeds/pollen
    labels = []       # (x,y,text,anchor_x,anchor_y)

    for ri, repo in enumerate(repos[:15]):  # Cap at 15 for sanity
        lang = repo.get("language")
        hue = LANG_HUES.get(lang, 160)
        repo_stars = repo.get("stars", 0)
        age = repo.get("age_months", 6)

        # Radial growth from ground line upward, spread across width
        spread = min(14, len(repos))
        base_x = 80 + (WIDTH - 160) * (ri / max(1, spread - 1)) if spread > 1 else CX
        base_x += rng.uniform(-20, 20)
        gy = ground_y_at(base_x)

        base_angle = -math.pi/2 + rng.uniform(-0.3, 0.3)  # Mostly upward
        main_length = 50 + min(250, age * 3.0)
        max_depth = max(2, min(6, 2 + age // 12))
        stem_sw = 2.5 + min(3.0, age * 0.05)

        # Add label for this repo
        labels.append((base_x, gy + 18, repo.get("name",""), base_x, gy))

        def grow(x, y, angle, depth, length, sw, repo_idx):
            if depth > max_depth or length < 5 or len(all_segs) >= MAX_SEGS:
                return
            n_segs = max(2, int(length / 12))
            cx_, cy_ = x, y

            for si in range(n_segs):
                if len(all_segs) >= MAX_SEGS: break
                nv = noise.fbm(cx_*0.005 + ri*7, cy_*0.005, 3)
                a = angle + nv * 0.35 * (1 + depth * 0.25)
                sl = length / n_segs * rng.uniform(0.85, 1.15)
                nx_ = cx_ + sl * math.cos(a)
                ny_ = cy_ + sl * math.sin(a)

                # Keep above ground and in bounds
                if ny_ > ground_y_at(nx_) - 5:
                    a -= 0.3
                    nx_ = cx_ + sl * math.cos(a)
                    ny_ = cy_ + sl * math.sin(a)
                if nx_ < 30 or nx_ > WIDTH-30 or ny_ < 30:
                    a += (math.atan2(CY-ny_, CX-nx_) - a) * 0.4
                    nx_ = cx_ + sl * math.cos(a)
                    ny_ = cy_ + sl * math.sin(a)

                is_main = depth == 0
                all_segs.append((cx_, cy_, nx_, ny_, sw, hue, depth, is_main, repo_idx))

                # Leaves on branches (not main stem)
                if depth >= 1 and rng.random() < 0.55:
                    side = rng.choice([-1, 1])
                    leaf_angle = a + side * (0.5 + rng.uniform(0, 0.6))
                    leaf_size = 5 + rng.uniform(0, 6) * (1 - depth/(max_depth+1))
                    has_vein = rng.random() < 0.7
                    leaves.append((nx_, ny_, leaf_angle, leaf_size, (hue+25)%360, has_vein))
                    # Occasional dew drop on leaf
                    if rng.random() < 0.15:
                        dx = nx_ + leaf_size*0.5*math.cos(leaf_angle)
                        dy = ny_ + leaf_size*0.5*math.sin(leaf_angle)
                        dew_drops.append((dx, dy, rng.uniform(1, 2.5)))

                # Buds on young branches
                if depth >= 2 and rng.random() < 0.12:
                    buds.append((nx_, ny_, rng.uniform(2, 4), hue))

                cx_, cy_ = nx_, ny_
                angle = a

                # Side branch
                if len(all_segs) < MAX_SEGS and rng.random() < 0.35 * (1 - depth/max_depth):
                    fa = rng.uniform(0.4, 1.1) * rng.choice([-1, 1])
                    grow(cx_, cy_, a+fa, depth+1, length*rng.uniform(0.35, 0.65), sw*0.55, repo_idx)

            # Terminal fork
            if depth < max_depth and len(all_segs) < MAX_SEGS:
                n_forks = rng.integers(1, 4)
                for _ in range(n_forks):
                    if len(all_segs) >= MAX_SEGS: break
                    fa = rng.uniform(0.3, 1.0) * rng.choice([-1, 1])
                    grow(cx_, cy_, angle+fa, depth+1, length*rng.uniform(0.25, 0.55), sw*0.5, repo_idx)

            # Blooms at tips — stars determine bloom richness
            if depth >= max_depth - 1 and rng.random() < 0.6:
                n_petals = max(4, min(12, 4 + repo_stars // 2))
                bloom_size = 5 + min(18, repo_stars * 0.8)
                petal_layers = 1 + min(3, repo_stars // 5)
                blooms.append((cx_, cy_, bloom_size, hue, n_petals, petal_layers))

            # Berries on some tips
            if depth >= max_depth and rng.random() < 0.2:
                for _ in range(rng.integers(2, 6)):
                    bx = cx_ + rng.uniform(-6, 6)
                    by = cy_ + rng.uniform(-6, 6)
                    berries.append((bx, by, rng.uniform(1.5, 3), (hue+180)%360))

        grow(base_x, gy, base_angle, 0, main_length, stem_sw, ri)

        # ROOT SYSTEM underground — forks create mycorrhizal network
        n_roots = max(2, min(6, 2 + forks // 5))
        root_depth = 40 + min(120, age * 1.5)
        for rootn in range(n_roots):
            if len(roots) > 2000: break
            ra = math.pi/2 + rng.uniform(-0.8, 0.8)  # Downward
            rx, ry = base_x + rng.uniform(-8, 8), gy
            r_len = root_depth * rng.uniform(0.5, 1.0)
            r_segs = max(3, int(r_len / 10))
            r_sw = stem_sw * 0.5
            for rsi in range(r_segs):
                nv = noise.fbm(rx*0.01 + rootn*3, ry*0.01, 2)
                ra += nv * 0.3
                sl = r_len / r_segs
                nrx = rx + sl * math.cos(ra)
                nry = ry + sl * math.sin(ra)
                roots.append((rx, ry, nrx, nry, r_sw * (1 - rsi/r_segs*0.6), hue, rootn))
                rx, ry = nrx, nry
                r_sw *= 0.92
                # Root branching
                if rng.random() < 0.25 and len(roots) < 2000:
                    bra = ra + rng.choice([-1,1]) * rng.uniform(0.3, 0.8)
                    brx, bry = rx, ry
                    for _ in range(rng.integers(2, 5)):
                        bnrx = brx + 8*math.cos(bra) + rng.uniform(-2,2)
                        bnry = bry + 8*math.sin(bra) + rng.uniform(-1,1)
                        roots.append((brx, bry, bnrx, bnry, r_sw*0.4, hue, rootn))
                        brx, bry = bnrx, bnry
                        bra += rng.uniform(-0.2, 0.2)

    # Tendrils (following/connections) — curly vines
    n_tendrils = min(8, metrics.get("following", 0) // 10)
    for ti in range(n_tendrils):
        # Pick a random branch segment to sprout from
        if all_segs:
            seg = all_segs[rng.integers(0, len(all_segs))]
            tx, ty = seg[2], seg[3]
            ta = rng.uniform(0, 2*math.pi)
            pts = [(tx, ty)]
            for step in range(15):
                ta += 0.4 * math.sin(step * 0.8 + ti)  # Curling
                tx += 4 * math.cos(ta)
                ty += 4 * math.sin(ta)
                pts.append((tx, ty))
            tendrils.append(pts)

    # Mushrooms at base (open issues decomposing)
    n_mush = min(8, open_issues)
    for mi in range(n_mush):
        mx = 60 + rng.uniform(0, WIDTH - 120)
        my = ground_y_at(mx) + rng.uniform(-3, 5)
        ms = 4 + rng.uniform(0, 6)
        mh = 30 + rng.integers(0, 40)  # earthy tones
        mushrooms.append((mx, my, ms, mh))

    # Insects — watchers=butterflies, contributions=bees, orgs=dragonflies
    n_butterflies = min(6, watchers // 2)
    for _ in range(n_butterflies):
        ix = rng.uniform(50, WIDTH-50)
        iy = rng.uniform(40, GROUND_Y - 20)
        insects.append((ix, iy, "butterfly", rng.uniform(8, 16), rng.integers(0, 360)))

    n_bees = min(5, contributions // 400)
    for _ in range(n_bees):
        ix = rng.uniform(80, WIDTH-80)
        iy = rng.uniform(60, GROUND_Y - 40)
        insects.append((ix, iy, "bee", rng.uniform(4, 8), 45))

    n_dragonflies = min(3, orgs)
    for _ in range(n_dragonflies):
        ix = rng.uniform(60, WIDTH-60)
        iy = rng.uniform(30, GROUND_Y - 50)
        insects.append((ix, iy, "dragonfly", rng.uniform(10, 18), rng.integers(0, 360)))

    # Spider webs between close branches (network connections)
    n_webs = min(4, network // 8)
    for _ in range(n_webs):
        if all_segs:
            seg = all_segs[rng.integers(0, len(all_segs))]
            webs.append((seg[2], seg[3], rng.uniform(12, 25), rng.integers(5, 9)))

    # Falling seeds/pollen (star events)
    n_seeds = min(20, stars // 3)
    for _ in range(n_seeds):
        sx = rng.uniform(40, WIDTH-40)
        sy = rng.uniform(30, GROUND_Y - 10)
        sa = rng.uniform(-0.3, 0.3)
        seeds.append((sx, sy, sa, rng.uniform(2, 5)))

    # --- BUILD SVG ---
    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">')

    # --- DEFS: filters, patterns, gradients ---
    parts.append('<defs>')

    # Ink wobble filter
    parts.append('''<filter id="ink" x="-3%" y="-3%" width="106%" height="106%">
    <feTurbulence type="fractalNoise" baseFrequency="0.05" numOctaves="3" seed="42" result="n"/>
    <feDisplacementMap in="SourceGraphic" in2="n" scale="1.5" xChannelSelector="R" yChannelSelector="G"/>
  </filter>''')

    # Paper texture filter
    parts.append('''<filter id="paper" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.6" numOctaves="4" seed="7" result="noise"/>
    <feColorMatrix in="noise" type="saturate" values="0" result="gray"/>
    <feBlend in="SourceGraphic" in2="gray" mode="multiply"/>
  </filter>''')

    # Soft shadow
    parts.append('''<filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
    <feGaussianBlur in="SourceAlpha" stdDeviation="2" result="blur"/>
    <feOffset in="blur" dx="1" dy="2" result="offset"/>
    <feFlood flood-color="#8a7a5a" flood-opacity="0.12" result="color"/>
    <feComposite in="color" in2="offset" operator="in" result="shadow"/>
    <feMerge><feMergeNode in="shadow"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>''')

    # Dew drop highlight
    parts.append('''<filter id="dew">
    <feGaussianBlur in="SourceGraphic" stdDeviation="0.5"/>
  </filter>''')

    # Radial gradient for dew
    parts.append('''<radialGradient id="dewGrad" cx="35%" cy="35%">
    <stop offset="0%" stop-color="#ffffff" stop-opacity="0.9"/>
    <stop offset="40%" stop-color="#e8f4ff" stop-opacity="0.6"/>
    <stop offset="100%" stop-color="#b0d8f0" stop-opacity="0.2"/>
  </radialGradient>''')

    # Grass pattern
    parts.append(f'''<pattern id="grass" x="0" y="0" width="12" height="8" patternUnits="userSpaceOnUse">
    <line x1="2" y1="8" x2="3" y2="2" stroke="#8aaa6a" stroke-width="0.4" opacity="0.3"/>
    <line x1="6" y1="8" x2="5" y2="1" stroke="#7a9a5a" stroke-width="0.3" opacity="0.25"/>
    <line x1="10" y1="8" x2="9" y2="3" stroke="#9aba7a" stroke-width="0.35" opacity="0.28"/>
  </pattern>''')

    # Soil layers pattern
    parts.append('''<pattern id="soil1" x="0" y="0" width="20" height="6" patternUnits="userSpaceOnUse">
    <rect width="20" height="6" fill="#c4a87a"/>
    <circle cx="5" cy="3" r="0.8" fill="#b09060" opacity="0.4"/>
    <circle cx="14" cy="2" r="0.5" fill="#a08050" opacity="0.3"/>
    <line x1="0" y1="5" x2="20" y2="5" stroke="#b8985a" stroke-width="0.2" opacity="0.2"/>
  </pattern>''')

    parts.append('''<pattern id="soil2" x="0" y="0" width="16" height="5" patternUnits="userSpaceOnUse">
    <rect width="16" height="5" fill="#a88860"/>
    <circle cx="4" cy="2" r="1.2" fill="#988050" opacity="0.3"/>
    <circle cx="11" cy="3" r="0.7" fill="#8a7048" opacity="0.35"/>
  </pattern>''')

    parts.append('''<pattern id="soil3" x="0" y="0" width="14" height="4" patternUnits="userSpaceOnUse">
    <rect width="14" height="4" fill="#907850"/>
    <circle cx="7" cy="2" r="1.5" fill="#806840" opacity="0.25"/>
  </pattern>''')

    parts.append('</defs>')

    # --- BACKGROUND: aged paper ---
    parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#f5f0e6" filter="url(#paper)"/>')

    # Paper edge darkening (vignette)
    parts.append(f'''<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#vignetteGrad)" opacity="0"/>''')

    # Foxing spots (age marks on paper)
    n_foxing = 15 + rng.integers(0, 20)
    for _ in range(n_foxing):
        fx = rng.uniform(20, WIDTH-20)
        fy = rng.uniform(20, HEIGHT-20)
        fr = rng.uniform(2, 8)
        parts.append(f'<circle cx="{fx:.0f}" cy="{fy:.0f}" r="{fr:.1f}" fill="#d8c8a8" opacity="{rng.uniform(0.03, 0.08):.3f}"/>')

    # --- UNDERGROUND LAYERS ---
    # Soil strata (account age = depth of strata)
    account_age_months = max(r.get("age_months", 6) for r in repos) if repos else 12
    n_strata = max(2, min(5, account_age_months // 18))

    # Ground surface line
    ground_pts = []
    for gx_i in range(0, WIDTH+5, 5):
        gy_val = ground_y_at(gx_i)
        ground_pts.append((gx_i, gy_val))

    ground_path = f"M{ground_pts[0][0]},{ground_pts[0][1]}"
    for i in range(1, len(ground_pts)):
        ground_path += f" L{ground_pts[i][0]:.1f},{ground_pts[i][1]:.1f}"

    # Draw soil layers from bottom up
    strata_depth = 30 + n_strata * 25
    soil_fills = ["url(#soil3)", "url(#soil2)", "url(#soil1)"]
    soil_colors = ["#907850", "#a88860", "#c4a87a"]
    for si in range(min(n_strata, 3)):
        layer_y = GROUND_Y + 15 + si * 30
        layer_bottom = min(HEIGHT - 15, layer_y + 35)
        layer_path = ground_path + f" L{WIDTH},{ground_pts[-1][1]:.1f}"
        # Offset the ground line down for each layer
        layer_pts = [(x, y + 15 + si*30) for x,y in ground_pts]
        lp = f"M{layer_pts[0][0]},{layer_pts[0][1]:.1f}"
        for lpi in range(1, len(layer_pts)):
            lp += f" L{layer_pts[lpi][0]:.1f},{layer_pts[lpi][1]:.1f}"
        lp += f" L{WIDTH},{layer_bottom} L{WIDTH},{HEIGHT} L0,{HEIGHT} L0,{layer_bottom} Z"
        fill = soil_fills[si % len(soil_fills)]
        parts.append(f'<path d="{lp}" fill="{fill}" opacity="0.5"/>')
        # Stratum line
        slp = f"M{layer_pts[0][0]},{layer_pts[0][1]:.1f}"
        for lpi in range(1, len(layer_pts)):
            slp += f" L{layer_pts[lpi][0]:.1f},{layer_pts[lpi][1]:.1f}"
        parts.append(f'<path d="{slp}" fill="none" stroke="#8a7050" stroke-width="0.4" opacity="0.25" stroke-dasharray="3 4"/>')

    # Pebbles in soil
    n_pebbles = 20 + rng.integers(0, 20)
    for _ in range(n_pebbles):
        px = rng.uniform(30, WIDTH-30)
        py = rng.uniform(GROUND_Y + 10, min(HEIGHT-20, GROUND_Y + strata_depth))
        pr = rng.uniform(1.5, 4)
        pc = rng.choice(["#a09070", "#b0a080", "#908060", "#c0b090"])
        parts.append(f'<ellipse cx="{px:.0f}" cy="{py:.0f}" rx="{pr:.1f}" ry="{pr*0.7:.1f}" fill="{pc}" opacity="{rng.uniform(0.15, 0.3):.2f}" '
                     f'transform="rotate({rng.uniform(-20,20):.0f},{px:.0f},{py:.0f})"/>')

    # --- ROOTS (underground) ---
    parts.append('<g opacity="0.45">')
    for rx1, ry1, rx2, ry2, rsw, rhue, rdepth in roots:
        rc = oklch(0.42, 0.06, 35)  # Root brown
        mx = (rx1+rx2)/2 + rng.uniform(-1.5, 1.5)
        my = (ry1+ry2)/2 + rng.uniform(-1.5, 1.5)
        parts.append(f'<path d="M{rx1:.1f},{ry1:.1f} Q{mx:.1f},{my:.1f} {rx2:.1f},{ry2:.1f}" '
                     f'fill="none" stroke="{rc}" stroke-width="{rsw:.1f}" stroke-linecap="round"/>')
    parts.append('</g>')

    # Mycorrhizal network connections between roots of different plants
    if len(repos) > 1 and forks > 0:
        parts.append('<g opacity="0.12">')
        n_myco = min(15, forks)
        for _ in range(n_myco):
            mx1 = rng.uniform(60, WIDTH-60)
            my1 = rng.uniform(GROUND_Y+20, GROUND_Y+80)
            mx2 = mx1 + rng.uniform(-100, 100)
            my2 = my1 + rng.uniform(-15, 15)
            mcx = (mx1+mx2)/2
            mcy = my1 + rng.uniform(10, 30)
            parts.append(f'<path d="M{mx1:.0f},{my1:.0f} Q{mcx:.0f},{mcy:.0f} {mx2:.0f},{my2:.0f}" '
                         f'fill="none" stroke="#a09060" stroke-width="0.5" stroke-dasharray="2 3"/>')
        parts.append('</g>')

    # Ground surface with grass
    ground_fill = ground_path + f" L{WIDTH},{GROUND_Y+5} L{WIDTH},{GROUND_Y+15} L0,{GROUND_Y+15} Z"
    parts.append(f'<path d="{ground_fill}" fill="url(#grass)" opacity="0.6"/>')
    # Ground line
    parts.append(f'<path d="{ground_path}" fill="none" stroke="#6a8a4a" stroke-width="1.2" opacity="0.5"/>')

    # Ground cover: scattered small marks (grass tufts, tiny stones, fallen leaves)
    for gci in range(60):
        gcx = rng.uniform(20, WIDTH-20)
        gcy = ground_y_at(gcx) + rng.uniform(-3, 3)
        if rng.random() < 0.6:
            # Grass tuft
            for _ in range(rng.integers(2, 5)):
                ga = -math.pi/2 + rng.uniform(-0.4, 0.4)
                gl = rng.uniform(3, 8)
                parts.append(f'<line x1="{gcx:.0f}" y1="{gcy:.0f}" '
                             f'x2="{gcx+gl*math.cos(ga):.0f}" y2="{gcy+gl*math.sin(ga):.0f}" '
                             f'stroke="#7a9a5a" stroke-width="0.4" opacity="0.25"/>')
        else:
            # Tiny stone
            parts.append(f'<circle cx="{gcx:.0f}" cy="{gcy:.0f}" r="{rng.uniform(0.5,1.5):.1f}" fill="#b0a080" opacity="0.2"/>')

    # --- MUSHROOMS at base ---
    for mx, my, ms, mh in mushrooms:
        # Stem
        parts.append(f'<rect x="{mx-ms*0.15:.1f}" y="{my-ms:.1f}" width="{ms*0.3:.1f}" height="{ms:.1f}" '
                     f'fill="#e8dcc0" opacity="0.7" rx="1"/>')
        # Cap (half ellipse)
        cap_c = oklch(0.55, 0.10, mh)
        parts.append(f'<ellipse cx="{mx:.1f}" cy="{my-ms:.1f}" rx="{ms*0.6:.1f}" ry="{ms*0.4:.1f}" '
                     f'fill="{cap_c}" opacity="0.65"/>')
        # Cap spots
        for _ in range(rng.integers(2, 5)):
            sx = mx + rng.uniform(-ms*0.3, ms*0.3)
            sy = my - ms + rng.uniform(-ms*0.2, ms*0.1)
            parts.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{rng.uniform(0.5,1.5):.1f}" fill="#f0e8d0" opacity="0.5"/>')

    # --- ABOVE GROUND: BOTANICAL ILLUSTRATION ---
    parts.append('<g filter="url(#ink)">')

    # Cross-hatching shadows in dense branch areas
    branch_density = defaultdict(int)
    for x1,y1,x2,y2,sw,hue,depth,is_main,ri in all_segs:
        gx = int((x1+x2)/2 / 30)
        gy = int((y1+y2)/2 / 30)
        branch_density[(gx,gy)] += 1

    max_bd = max(branch_density.values()) if branch_density else 1
    for (gx,gy), count in branch_density.items():
        if count < 4: continue
        density_frac = count / max_bd
        cx_h = gx * 30 + 15
        cy_h = gy * 30 + 15
        n_hatch = int(density_frac * 8)
        # Cross-hatch: two directions
        for hi in range(n_hatch):
            op = density_frac * 0.15
            # Direction 1: /
            hx1 = cx_h - 12 + hi * 3
            hy1 = cy_h - 12
            hx2 = hx1 + 18
            hy2 = cy_h + 12
            parts.append(f'<line x1="{hx1:.0f}" y1="{hy1:.0f}" x2="{hx2:.0f}" y2="{hy2:.0f}" '
                         f'stroke="#a09878" stroke-width="0.25" opacity="{op:.3f}"/>')
            # Direction 2: \ (perpendicular)
            if density_frac > 0.5:
                parts.append(f'<line x1="{hx2:.0f}" y1="{hy1:.0f}" x2="{hx1:.0f}" y2="{hy2:.0f}" '
                             f'stroke="#a09878" stroke-width="0.2" opacity="{op*0.7:.3f}"/>')

    # Background stipple from monthly activity
    max_m = max(monthly.values()) if monthly else 100
    for mkey, count in monthly.items():
        intensity = count / max(1, max_m)
        mi = int(mkey) - 1 if mkey.isdigit() else 0
        angle = -math.pi/2 + mi * 2 * math.pi / 12
        cx_m = CX + 200 * math.cos(angle)
        cy_m = CY - 80 + 180 * math.sin(angle)  # Above ground
        cy_m = min(cy_m, GROUND_Y - 30)
        n_dots = int(intensity * 40)
        for _ in range(n_dots):
            dx = cx_m + rng.normal(0, 50)
            dy = cy_m + rng.normal(0, 50)
            if dy > GROUND_Y - 5: continue
            dr = rng.uniform(0.15, 0.5)
            parts.append(f'<circle cx="{dx:.0f}" cy="{dy:.0f}" r="{dr:.1f}" fill="#c8bfa8" opacity="{0.06+intensity*0.12:.2f}"/>')

    # PASS 1: Main stems with bark texture
    for x1,y1,x2,y2,sw,hue,depth,is_main,ri in all_segs:
        if not is_main: continue
        color = oklch(0.28, 0.06, hue)
        mx = (x1+x2)/2 + rng.uniform(-1, 1)
        my = (y1+y2)/2 + rng.uniform(-1, 1)
        parts.append(f'<path d="M{x1:.1f},{y1:.1f} Q{mx:.1f},{my:.1f} {x2:.1f},{y2:.1f}" '
                     f'fill="none" stroke="{color}" stroke-width="{sw:.1f}" '
                     f'opacity="0.85" stroke-linecap="round"/>')
        # Bark texture: parallel thin lines along stem
        if sw > 3:
            seg_len = math.sqrt((x2-x1)**2+(y2-y1)**2)
            if seg_len > 5:
                perp = math.atan2(y2-y1, x2-x1) + math.pi/2
                for bi in range(int(sw)):
                    offset = (bi - sw/2) * 0.6
                    bx1 = x1 + offset*math.cos(perp) + rng.uniform(-0.5, 0.5)
                    by1 = y1 + offset*math.sin(perp) + rng.uniform(-0.5, 0.5)
                    bx2 = x2 + offset*math.cos(perp) + rng.uniform(-0.5, 0.5)
                    by2 = y2 + offset*math.sin(perp) + rng.uniform(-0.5, 0.5)
                    parts.append(f'<line x1="{bx1:.1f}" y1="{by1:.1f}" x2="{bx2:.1f}" y2="{by2:.1f}" '
                                 f'stroke="{oklch(0.32, 0.04, hue)}" stroke-width="0.2" opacity="0.15"/>')

    # PASS 2: Secondary branches
    for x1,y1,x2,y2,sw,hue,depth,is_main,ri in all_segs:
        if is_main: continue
        d_frac = depth / 6
        color = oklch(0.32 + d_frac*0.12, 0.10 + d_frac*0.04, hue)
        op = max(0.3, 0.80 - depth * 0.08)
        mx = (x1+x2)/2 + rng.uniform(-2, 2)
        my = (y1+y2)/2 + rng.uniform(-2, 2)
        parts.append(f'<path d="M{x1:.1f},{y1:.1f} Q{mx:.1f},{my:.1f} {x2:.1f},{y2:.1f}" '
                     f'fill="none" stroke="{color}" stroke-width="{sw:.1f}" '
                     f'opacity="{op:.2f}" stroke-linecap="round"/>')

    # PASS 3: Tendrils (curly vines)
    for pts in tendrils:
        if len(pts) < 3: continue
        pd = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
        for j in range(1, len(pts)-1, 2):
            if j+1 < len(pts):
                pd += f" Q{pts[j][0]:.1f},{pts[j][1]:.1f} {pts[j+1][0]:.1f},{pts[j+1][1]:.1f}"
        parts.append(f'<path d="{pd}" fill="none" stroke="#6a9a4a" stroke-width="0.5" opacity="0.35" stroke-linecap="round"/>')

    # PASS 4: Leaves with veins
    for lx, ly, la, ls, lh, has_vein in leaves:
        tip_x = lx + ls * math.cos(la)
        tip_y = ly + ls * math.sin(la)
        perp = la + math.pi/2
        bulge = ls * 0.35
        cp1x = (lx + tip_x)/2 + bulge * math.cos(perp)
        cp1y = (ly + tip_y)/2 + bulge * math.sin(perp)
        cp2x = (lx + tip_x)/2 - bulge * math.cos(perp)
        cp2y = (ly + tip_y)/2 - bulge * math.sin(perp)

        leaf_fill = oklch(0.52, 0.16, lh)
        leaf_stroke = oklch(0.40, 0.12, lh)
        parts.append(f'<path d="M{lx:.1f},{ly:.1f} Q{cp1x:.1f},{cp1y:.1f} {tip_x:.1f},{tip_y:.1f} '
                     f'Q{cp2x:.1f},{cp2y:.1f} {lx:.1f},{ly:.1f}" '
                     f'fill="{leaf_fill}" opacity="0.4" stroke="{leaf_stroke}" stroke-width="0.3"/>')

        # Leaf vein (midrib + side veins)
        if has_vein:
            parts.append(f'<line x1="{lx:.1f}" y1="{ly:.1f}" x2="{tip_x:.1f}" y2="{tip_y:.1f}" '
                         f'stroke="{leaf_stroke}" stroke-width="0.2" opacity="0.3"/>')
            # Side veins
            for vi in range(1, 4):
                vt = vi / 4
                vx = lx + (tip_x-lx)*vt
                vy = ly + (tip_y-ly)*vt
                for side in [-1, 1]:
                    va = la + side * (0.5 + vi*0.1)
                    vl = ls * 0.2 * (1 - vt*0.5)
                    vex = vx + vl * math.cos(va)
                    vey = vy + vl * math.sin(va)
                    parts.append(f'<line x1="{vx:.1f}" y1="{vy:.1f}" x2="{vex:.1f}" y2="{vey:.1f}" '
                                 f'stroke="{leaf_stroke}" stroke-width="0.15" opacity="0.2"/>')

    # PASS 5: Buds
    for bx, by, bs, bh in buds:
        bud_c = oklch(0.60, 0.15, bh)
        # Bud: small elongated oval
        parts.append(f'<ellipse cx="{bx:.1f}" cy="{by:.1f}" rx="{bs*0.4:.1f}" ry="{bs:.1f}" '
                     f'fill="{bud_c}" opacity="0.5" stroke="{oklch(0.45,0.12,bh)}" stroke-width="0.2" '
                     f'transform="rotate({rng.uniform(-30,30):.0f},{bx:.1f},{by:.1f})"/>')

    # PASS 6: Blooms with multi-layer petals and stamens
    for bx, by, bs, bh, n_petals, petal_layers in blooms:
        # Multiple petal layers (outer to inner, each rotated)
        for layer in range(petal_layers):
            layer_frac = layer / max(1, petal_layers)
            layer_r = bs * (1 - layer_frac * 0.3)
            layer_op = 0.4 + layer_frac * 0.2
            rot_offset = layer * 0.3  # Rotate each layer
            petal_hue = (bh + layer * 15) % 360
            petal_c = oklch(0.58 + layer_frac*0.12, 0.22 - layer_frac*0.06, petal_hue)
            petal_dark = oklch(0.48 + layer_frac*0.08, 0.18, petal_hue)

            for pi in range(n_petals):
                pa = pi * 2 * math.pi / n_petals + rot_offset + rng.uniform(-0.08, 0.08)
                pr = layer_r * 0.75
                tip_x = bx + pr * math.cos(pa)
                tip_y = by + pr * math.sin(pa)
                side_a = pa + 0.35
                side_b = pa - 0.35
                cp_r = pr * 0.55
                cp1x = bx + cp_r * math.cos(side_a)
                cp1y = by + cp_r * math.sin(side_a)
                cp2x = bx + cp_r * math.cos(side_b)
                cp2y = by + cp_r * math.sin(side_b)

                parts.append(f'<path d="M{bx:.1f},{by:.1f} Q{cp1x:.1f},{cp1y:.1f} {tip_x:.1f},{tip_y:.1f} '
                             f'Q{cp2x:.1f},{cp2y:.1f} {bx:.1f},{by:.1f}" '
                             f'fill="{petal_c}" opacity="{layer_op:.2f}" stroke="{petal_dark}" stroke-width="0.2"/>')

                # Petal vein
                parts.append(f'<line x1="{bx:.1f}" y1="{by:.1f}" x2="{tip_x:.1f}" y2="{tip_y:.1f}" '
                             f'stroke="{petal_dark}" stroke-width="0.15" opacity="0.15"/>')

        # Center pistil
        center_c = oklch(0.72, 0.15, (bh + 60) % 360)
        parts.append(f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="{bs*0.18:.1f}" fill="{center_c}" opacity="0.8"/>')
        # Stipple center
        for _ in range(max(3, n_petals)):
            sx = bx + rng.uniform(-bs*0.12, bs*0.12)
            sy = by + rng.uniform(-bs*0.12, bs*0.12)
            parts.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="0.4" fill="{oklch(0.55, 0.12, (bh+80)%360)}" opacity="0.5"/>')

        # Stamens radiating from center
        n_stamens = max(3, n_petals - 2)
        for si in range(n_stamens):
            sa = si * 2 * math.pi / n_stamens + 0.15
            sr = bs * 0.35
            stx = bx + sr * math.cos(sa)
            sty = by + sr * math.sin(sa)
            parts.append(f'<line x1="{bx:.1f}" y1="{by:.1f}" x2="{stx:.1f}" y2="{sty:.1f}" '
                         f'stroke="{oklch(0.65, 0.10, (bh+40)%360)}" stroke-width="0.3" opacity="0.4"/>')
            # Anther dot
            parts.append(f'<circle cx="{stx:.1f}" cy="{sty:.1f}" r="0.8" fill="{oklch(0.70, 0.18, 50)}" opacity="0.6"/>')

    # PASS 7: Berries
    for bx, by, bs, bh in berries:
        berry_c = oklch(0.45, 0.20, bh)
        parts.append(f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="{bs:.1f}" fill="{berry_c}" opacity="0.6" '
                     f'stroke="{oklch(0.35, 0.15, bh)}" stroke-width="0.3"/>')
        # Highlight
        parts.append(f'<circle cx="{bx-bs*0.25:.1f}" cy="{by-bs*0.25:.1f}" r="{bs*0.3:.1f}" fill="#ffffff" opacity="0.25"/>')

    parts.append('</g>')  # End ink filter group

    # PASS 8: Spider webs (no ink filter — should be delicate)
    for wcx, wcy, wr, n_spokes in webs:
        # Spokes
        for si in range(n_spokes):
            sa = si * 2 * math.pi / n_spokes
            sx = wcx + wr * math.cos(sa)
            sy = wcy + wr * math.sin(sa)
            parts.append(f'<line x1="{wcx:.1f}" y1="{wcy:.1f}" x2="{sx:.1f}" y2="{sy:.1f}" '
                         f'stroke="#c0b8a0" stroke-width="0.2" opacity="0.2"/>')
        # Spiral rings
        for ring in range(3, int(wr), 4):
            ring_pts = []
            for si in range(n_spokes + 1):
                sa = si * 2 * math.pi / n_spokes
                rx = wcx + ring * math.cos(sa)
                ry = wcy + ring * math.sin(sa)
                ring_pts.append(f"{rx:.1f},{ry:.1f}")
            parts.append(f'<polyline points="{" ".join(ring_pts)}" fill="none" stroke="#c0b8a0" stroke-width="0.15" opacity="0.15"/>')
        # Dew drops on web
        for _ in range(rng.integers(2, 5)):
            da = rng.uniform(0, 2*math.pi)
            dr = rng.uniform(3, wr*0.8)
            dx = wcx + dr * math.cos(da)
            dy = wcy + dr * math.sin(da)
            dew_drops.append((dx, dy, rng.uniform(0.8, 1.8)))

    # PASS 9: Dew drops
    for dx, dy, ds in dew_drops:
        parts.append(f'<circle cx="{dx:.1f}" cy="{dy:.1f}" r="{ds:.1f}" fill="url(#dewGrad)" filter="url(#dew)"/>')

    # PASS 10: Insects
    for ix, iy, itype, isize, ihue in insects:
        if itype == "butterfly":
            # Body
            parts.append(f'<ellipse cx="{ix:.0f}" cy="{iy:.0f}" rx="1" ry="{isize*0.3:.1f}" fill="#3a3020" opacity="0.6"/>')
            # Wings (4 teardrop shapes)
            wing_c1 = oklch(0.62, 0.22, ihue)
            wing_c2 = oklch(0.55, 0.18, (ihue+30)%360)
            for side in [-1, 1]:
                # Upper wing
                uwx = ix + side * isize * 0.5
                uwy = iy - isize * 0.2
                parts.append(f'<ellipse cx="{uwx:.0f}" cy="{uwy:.0f}" rx="{isize*0.4:.1f}" ry="{isize*0.3:.1f}" '
                             f'fill="{wing_c1}" opacity="0.45" '
                             f'transform="rotate({side*15},{uwx:.0f},{uwy:.0f})"/>')
                # Dot on wing
                parts.append(f'<circle cx="{uwx:.0f}" cy="{uwy:.0f}" r="{isize*0.08:.1f}" fill="#ffffff" opacity="0.3"/>')
                # Lower wing
                lwx = ix + side * isize * 0.35
                lwy = iy + isize * 0.15
                parts.append(f'<ellipse cx="{lwx:.0f}" cy="{lwy:.0f}" rx="{isize*0.25:.1f}" ry="{isize*0.2:.1f}" '
                             f'fill="{wing_c2}" opacity="0.4"/>')
            # Antennae
            parts.append(f'<path d="M{ix},{iy-isize*0.3:.0f} Q{ix-3},{iy-isize*0.6:.0f} {ix-5},{iy-isize*0.7:.0f}" '
                         f'fill="none" stroke="#3a3020" stroke-width="0.3" opacity="0.4"/>')
            parts.append(f'<path d="M{ix},{iy-isize*0.3:.0f} Q{ix+3},{iy-isize*0.6:.0f} {ix+5},{iy-isize*0.7:.0f}" '
                         f'fill="none" stroke="#3a3020" stroke-width="0.3" opacity="0.4"/>')

        elif itype == "bee":
            # Body with stripes
            parts.append(f'<ellipse cx="{ix:.0f}" cy="{iy:.0f}" rx="{isize*0.35:.1f}" ry="{isize*0.25:.1f}" fill="#d4a030" opacity="0.6"/>')
            # Stripes
            for si in range(3):
                sx = ix - isize*0.2 + si * isize*0.15
                parts.append(f'<line x1="{sx:.0f}" y1="{iy-isize*0.2:.0f}" x2="{sx:.0f}" y2="{iy+isize*0.2:.0f}" '
                             f'stroke="#2a2010" stroke-width="0.8" opacity="0.3"/>')
            # Wings
            parts.append(f'<ellipse cx="{ix:.0f}" cy="{iy-isize*0.3:.0f}" rx="{isize*0.3:.1f}" ry="{isize*0.15:.1f}" '
                         f'fill="#e8e0d0" opacity="0.3" stroke="#c8c0b0" stroke-width="0.2"/>')

        elif itype == "dragonfly":
            # Body
            parts.append(f'<line x1="{ix-isize*0.5:.0f}" y1="{iy:.0f}" x2="{ix+isize*0.5:.0f}" y2="{iy:.0f}" '
                         f'stroke="#4a6a80" stroke-width="1" opacity="0.5" stroke-linecap="round"/>')
            # Wings (4 long narrow ellipses)
            for side in [-1, 1]:
                for offset in [-0.15, 0.05]:
                    wx = ix + offset * isize
                    wy = iy + side * isize * 0.25
                    parts.append(f'<ellipse cx="{wx:.0f}" cy="{wy:.0f}" rx="{isize*0.35:.1f}" ry="{isize*0.08:.1f}" '
                                 f'fill="#d8e8f0" opacity="0.25" stroke="#a0b8c8" stroke-width="0.2" '
                                 f'transform="rotate({side*10},{wx:.0f},{wy:.0f})"/>')

    # PASS 11: Falling seeds/pollen
    for sx, sy, sa, ss in seeds:
        # Dandelion-like seed puff
        parts.append(f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="{ss*0.3:.1f}" fill="#d8cca0" opacity="0.3"/>')
        # Filaments
        n_fil = rng.integers(4, 8)
        for fi in range(n_fil):
            fa = fi * 2 * math.pi / n_fil + sa
            fl = ss
            fx = sx + fl * math.cos(fa)
            fy = sy + fl * math.sin(fa)
            parts.append(f'<line x1="{sx:.0f}" y1="{sy:.0f}" x2="{fx:.0f}" y2="{fy:.0f}" '
                         f'stroke="#c8bfa0" stroke-width="0.2" opacity="0.2"/>')

    # --- LABELS (botanical annotation style) ---
    parts.append('<g font-family="Georgia,serif" font-size="7" fill="#5a4a3a">')
    for lx, ly, text, ax, ay in labels:
        # Leader line from label to base of plant
        parts.append(f'<line x1="{ax:.0f}" y1="{ay:.0f}" x2="{lx:.0f}" y2="{ly:.0f}" '
                     f'stroke="#a09070" stroke-width="0.3" opacity="0.3" stroke-dasharray="1.5 2"/>')
        # Dot at anchor
        parts.append(f'<circle cx="{ax:.0f}" cy="{ay:.0f}" r="1" fill="#a09070" opacity="0.3"/>')
        # Text with italic style
        parts.append(f'<text x="{lx:.0f}" y="{ly:.0f}" text-anchor="middle" font-style="italic" opacity="0.45">{text}</text>')
    parts.append('</g>')

    # --- ORNATE BORDER with corner flourishes ---
    # Outer border
    m = 14
    parts.append(f'<rect x="{m}" y="{m}" width="{WIDTH-2*m}" height="{HEIGHT-2*m}" fill="none" stroke="#b0a088" stroke-width="1.2" rx="3"/>')
    # Inner border
    m2 = 18
    parts.append(f'<rect x="{m2}" y="{m2}" width="{WIDTH-2*m2}" height="{HEIGHT-2*m2}" fill="none" stroke="#d0c8b0" stroke-width="0.4" rx="2"/>')

    # Corner flourishes (small botanical curves)
    for cx_c, cy_c, rot in [(m+5, m+5, 0), (WIDTH-m-5, m+5, 90), (WIDTH-m-5, HEIGHT-m-5, 180), (m+5, HEIGHT-m-5, 270)]:
        parts.append(f'<g transform="rotate({rot},{cx_c},{cy_c})">')
        parts.append(f'<path d="M{cx_c},{cy_c} Q{cx_c+12},{cy_c+2} {cx_c+18},{cy_c+10}" '
                     f'fill="none" stroke="#b0a088" stroke-width="0.6" opacity="0.4"/>')
        parts.append(f'<path d="M{cx_c},{cy_c} Q{cx_c+2},{cy_c+12} {cx_c+10},{cy_c+18}" '
                     f'fill="none" stroke="#b0a088" stroke-width="0.6" opacity="0.4"/>')
        # Small leaf at corner
        parts.append(f'<path d="M{cx_c+3},{cy_c+3} Q{cx_c+8},{cy_c+1} {cx_c+12},{cy_c+5} Q{cx_c+8},{cy_c+7} {cx_c+3},{cy_c+3}" '
                     f'fill="#c8d0a8" opacity="0.15"/>')
        parts.append('</g>')

    # Title cartouche at bottom
    parts.append(f'<text x="{CX}" y="{HEIGHT-22}" text-anchor="middle" font-family="Georgia,serif" font-size="9" '
                 f'fill="#7a6a5a" opacity="0.4" font-style="italic">{metrics.get("label","")}</text>')

    parts.append('</svg>')
    return '\n'.join(parts)


# =========================================================================
# TOPOGRAPHY ULTIMATE — Full cartographic illustration
# =========================================================================

def generate_topography_ultimate(metrics: dict) -> str:
    h = _sh(metrics)
    rng = np.random.default_rng(int(h[:8], 16))
    noise = Noise2D(seed=int(h[8:16],16))
    noise2 = Noise2D(seed=int(h[16:24],16))

    monthly = metrics.get("contributions_monthly", {})
    repos = metrics.get("repos", [])
    total_commits = metrics.get("total_commits", 500)
    followers = metrics.get("followers", 10)
    contributions = metrics.get("contributions_last_year", 200)
    forks = metrics.get("forks", 0)
    stars = metrics.get("stars", 0)
    network = metrics.get("network_count", 0)
    orgs = metrics.get("orgs_count", 1)

    # Map area (with margins for cartographic frame)
    MAP_L, MAP_T, MAP_R, MAP_B = 60, 60, WIDTH-60, HEIGHT-110  # Extra bottom for profile
    MAP_W = MAP_R - MAP_L
    MAP_H = MAP_B - MAP_T

    grid = 180
    elevation = np.zeros((grid, grid))

    # Base terrain noise
    terrain_octaves = max(3, min(7, 3 + total_commits // 6000))
    for gy in range(grid):
        for gx in range(grid):
            nx = gx / grid * 6
            ny = gy / grid * 6
            elevation[gy, gx] = noise.fbm(nx, ny, terrain_octaves) * 0.2

    # Contribution peaks — seasonal mountains
    max_m = max(monthly.values()) if monthly else 100
    months_sorted = sorted(monthly.keys())
    peak_positions = []
    for mi, mkey in enumerate(months_sorted):
        intensity = monthly[mkey] / max(1, max_m)
        angle = -math.pi/2 + mi * 2 * math.pi / max(1, len(months_sorted))
        pr = 0.15 + intensity * 0.15
        pcx = 0.5 + pr * math.cos(angle)
        pcy = 0.5 + pr * math.sin(angle)
        sigma = 0.04 + intensity * 0.05
        peak_h = intensity * 0.55
        peak_positions.append((pcx, pcy, peak_h, mkey))
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
        repo_stars = repo.get("stars", 0)
        age = repo.get("age_months", 6)
        angle = ri * 2.399 + _hf(h, (ri*2)%60, (ri*2+2)%60+2) * 0.4
        dist = 0.1 + min(0.32, age / 100 * 0.32)
        rcx = 0.5 + dist * math.cos(angle)
        rcy = 0.5 + dist * math.sin(angle)
        sigma = 0.02 + min(0.03, repo_stars * 0.001)
        peak_h = 0.12 + min(0.45, repo_stars * 0.015)
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

    # Central peak (profile)
    for gy in range(grid):
        for gx in range(grid):
            fx = gx/grid; fy = gy/grid
            dx = fx-0.5; dy = fy-0.5
            elevation[gy,gx] += 0.35 * math.exp(-(dx*dx+dy*dy)/(2*0.07*0.07))

    # River valleys — carve channels following noise
    n_rivers = max(1, min(5, forks // 5))
    river_paths = []
    for rvi in range(n_rivers):
        rx = 0.5 + rng.uniform(-0.3, 0.3)
        ry = 0.5 + rng.uniform(-0.3, 0.3)
        rpts = [(rx, ry)]
        for step in range(60):
            # Flow downhill with noise perturbation
            gxi = min(grid-2, max(1, int(rx*grid)))
            gyi = min(grid-2, max(1, int(ry*grid)))
            # Gradient
            dedx = (elevation[gyi, gxi+1] - elevation[gyi, gxi-1]) / 2
            dedy = (elevation[gyi+1, gxi] - elevation[gyi-1, gxi]) / 2
            # Flow perpendicular to gradient (along contour) + downhill
            nv = noise2.noise(rx*8 + rvi*10, ry*8) * 0.3
            rx += -dedx * 0.8 + nv * 0.02
            ry += -dedy * 0.8 + noise2.noise(rx*5, ry*5+rvi*5) * 0.02
            rx = max(0.02, min(0.98, rx))
            ry = max(0.02, min(0.98, ry))
            rpts.append((rx, ry))
            # Carve the valley
            gxi2 = min(grid-1, max(0, int(rx*grid)))
            gyi2 = min(grid-1, max(0, int(ry*grid)))
            for dy in range(-2, 3):
                for dx2 in range(-2, 3):
                    yi = min(grid-1, max(0, gyi2+dy))
                    xi = min(grid-1, max(0, gxi2+dx2))
                    d = math.sqrt(dy*dy + dx2*dx2)
                    if d < 3:
                        elevation[yi, xi] -= 0.03 * (1 - d/3)
        river_paths.append(rpts)

    # Normalize
    e_min = elevation.min(); e_max = elevation.max()
    if e_max > e_min:
        elevation = (elevation - e_min) / (e_max - e_min)

    # Color palette — rich topo colors
    topo_stops = [
        (0.00, "#d0e4f0"),  # deep water
        (0.10, "#d8eaf2"),  # shallow water
        (0.18, "#e2f0e8"),  # coastal
        (0.25, "#d0e4c0"),  # lowland
        (0.32, "#b8d898"),  # green lowland
        (0.40, "#a0cc78"),  # green
        (0.48, "#c8cc68"),  # yellow-green
        (0.56, "#dcc050"),  # gold
        (0.64, "#d8a840"),  # amber
        (0.72, "#cc8830"),  # orange-brown
        (0.80, "#b87028"),  # brown
        (0.88, "#a06020"),  # dark brown
        (0.94, "#c0b0a0"),  # rocky
        (1.00, "#f0ece4"),  # snow
    ]

    def topo_color(e):
        for i in range(len(topo_stops)-1):
            if e <= topo_stops[i+1][0]:
                t = (e - topo_stops[i][0]) / max(0.001, topo_stops[i+1][0] - topo_stops[i][0])
                c1 = topo_stops[i][1]
                c2 = topo_stops[i+1][1]
                r = int(int(c1[1:3],16) * (1-t) + int(c2[1:3],16) * t)
                g = int(int(c1[3:5],16) * (1-t) + int(c2[3:5],16) * t)
                b = int(int(c1[5:7],16) * (1-t) + int(c2[5:7],16) * t)
                return f"#{r:02x}{g:02x}{b:02x}"
        return topo_stops[-1][1]

    # Contour extraction
    cell_w = MAP_W / grid
    cell_h = MAP_H / grid

    def grid_to_map(gx, gy):
        return MAP_L + gx * cell_w, MAP_T + gy * cell_h

    def extract_contours(level):
        seg_list = []
        for gy in range(grid-1):
            for gx in range(grid-1):
                tl=elevation[gy,gx];tr=elevation[gy,gx+1]
                bl=elevation[gy+1,gx];br=elevation[gy+1,gx+1]
                edges=[]
                if (tl<level)!=(tr<level):
                    t=(level-tl)/(tr-tl+1e-10)
                    edges.append(grid_to_map(gx+t, gy))
                if (bl<level)!=(br<level):
                    t=(level-bl)/(br-bl+1e-10)
                    edges.append(grid_to_map(gx+t, gy+1))
                if (tl<level)!=(bl<level):
                    t=(level-tl)/(bl-tl+1e-10)
                    edges.append(grid_to_map(gx, gy+t))
                if (tr<level)!=(br<level):
                    t=(level-tr)/(br-tr+1e-10)
                    edges.append(grid_to_map(gx+1, gy+t))
                if len(edges)>=2:
                    seg_list.append((edges[0], edges[1]))

        if not seg_list:
            return []
        used = [False]*len(seg_list)
        chains = []
        for start_i in range(len(seg_list)):
            if used[start_i]: continue
            used[start_i] = True
            chain = [seg_list[start_i][0], seg_list[start_i][1]]
            changed = True
            while changed:
                changed = False
                last = chain[-1]
                best_d = 8.0
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

    # Hillshade computation
    hillshade = np.zeros((grid, grid))
    sun_az = math.radians(315)  # NW light
    sun_alt = math.radians(45)
    for gy in range(1, grid-1):
        for gx in range(1, grid-1):
            dzdx = (elevation[gy, gx+1] - elevation[gy, gx-1]) / 2
            dzdy = (elevation[gy+1, gx] - elevation[gy-1, gx]) / 2
            slope = math.atan(math.sqrt(dzdx*dzdx + dzdy*dzdy) * 5)
            aspect = math.atan2(-dzdy, dzdx)
            hs = math.cos(sun_alt)*math.cos(slope) + math.sin(sun_alt)*math.sin(slope)*math.cos(sun_az - aspect)
            hillshade[gy, gx] = max(0, min(1, (hs + 1) / 2))

    # --- BUILD SVG ---
    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">')

    # Defs
    parts.append('<defs>')

    # Tree symbol pattern
    parts.append(f'''<pattern id="trees" x="0" y="0" width="16" height="14" patternUnits="userSpaceOnUse">
    <circle cx="4" cy="6" r="2.5" fill="none" stroke="#5a8a3a" stroke-width="0.4" opacity="0.2"/>
    <line x1="4" y1="8.5" x2="4" y2="11" stroke="#5a8a3a" stroke-width="0.3" opacity="0.15"/>
    <circle cx="12" cy="4" r="2" fill="none" stroke="#5a8a3a" stroke-width="0.35" opacity="0.18"/>
    <line x1="12" y1="6" x2="12" y2="9" stroke="#5a8a3a" stroke-width="0.25" opacity="0.12"/>
  </pattern>''')

    # Marsh pattern
    parts.append(f'''<pattern id="marsh" x="0" y="0" width="12" height="8" patternUnits="userSpaceOnUse">
    <line x1="2" y1="6" x2="2" y2="2" stroke="#6898a8" stroke-width="0.3" opacity="0.2"/>
    <line x1="6" y1="6" x2="6" y2="3" stroke="#6898a8" stroke-width="0.3" opacity="0.2"/>
    <line x1="10" y1="6" x2="10" y2="2" stroke="#6898a8" stroke-width="0.3" opacity="0.2"/>
    <line x1="0" y1="7" x2="12" y2="7" stroke="#6898a8" stroke-width="0.2" opacity="0.15"/>
  </pattern>''')

    # Wave pattern for water
    parts.append(f'''<pattern id="waves" x="0" y="0" width="20" height="6" patternUnits="userSpaceOnUse">
    <path d="M0,3 Q5,1 10,3 Q15,5 20,3" fill="none" stroke="#8ab8d0" stroke-width="0.3" opacity="0.2"/>
  </pattern>''')

    parts.append('</defs>')

    # Background
    parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#f5f0e6"/>')

    # --- ELEVATION FILL with hillshade ---
    fill_step = 2
    for gy in range(0, grid, fill_step):
        for gx in range(0, grid, fill_step):
            e = elevation[gy, gx]
            hs = hillshade[min(gy, grid-1), min(gx, grid-1)]
            c = topo_color(e)
            # Apply hillshade as brightness modifier
            r = int(c[1:3], 16)
            g = int(c[3:5], 16)
            b = int(c[5:7], 16)
            shade_factor = 0.7 + hs * 0.5  # Range 0.7-1.2
            r = max(0, min(255, int(r * shade_factor)))
            g = max(0, min(255, int(g * shade_factor)))
            b = max(0, min(255, int(b * shade_factor)))
            shaded = f"#{r:02x}{g:02x}{b:02x}"

            mx, my = grid_to_map(gx, gy)
            sw = cell_w * fill_step + 0.5
            sh = cell_h * fill_step + 0.5
            parts.append(f'<rect x="{mx:.1f}" y="{my:.1f}" width="{sw:.1f}" height="{sh:.1f}" fill="{shaded}" opacity="0.8"/>')

    # --- WATER FEATURES ---
    # Lakes/water areas with wave pattern
    for gy in range(0, grid, 3):
        for gx in range(0, grid, 3):
            e = elevation[min(gy,grid-1), min(gx,grid-1)]
            if e < 0.12:
                mx, my = grid_to_map(gx, gy)
                sw = cell_w * 3 + 0.5
                sh = cell_h * 3 + 0.5
                parts.append(f'<rect x="{mx:.1f}" y="{my:.1f}" width="{sw:.1f}" height="{sh:.1f}" fill="url(#waves)" opacity="0.5"/>')

    # --- VEGETATION OVERLAY ---
    for gy in range(0, grid, 6):
        for gx in range(0, grid, 6):
            e = elevation[min(gy,grid-1), min(gx,grid-1)]
            if 0.25 < e < 0.50:  # Green zone = forested
                mx, my = grid_to_map(gx, gy)
                sw = cell_w * 6
                sh = cell_h * 6
                parts.append(f'<rect x="{mx:.1f}" y="{my:.1f}" width="{sw:.1f}" height="{sh:.1f}" fill="url(#trees)" opacity="0.6"/>')
            elif 0.12 < e < 0.20:  # Marsh zone
                mx, my = grid_to_map(gx, gy)
                sw = cell_w * 6
                sh = cell_h * 6
                parts.append(f'<rect x="{mx:.1f}" y="{my:.1f}" width="{sw:.1f}" height="{sh:.1f}" fill="url(#marsh)" opacity="0.5"/>')

    # --- RIVERS ---
    for rpts in river_paths:
        if len(rpts) < 3: continue
        pd = f"M{MAP_L + rpts[0][0]*MAP_W:.1f},{MAP_T + rpts[0][1]*MAP_H:.1f}"
        for j in range(1, len(rpts)-1, 2):
            if j+1 < len(rpts):
                pd += (f" Q{MAP_L + rpts[j][0]*MAP_W:.1f},{MAP_T + rpts[j][1]*MAP_H:.1f} "
                       f"{MAP_L + rpts[j+1][0]*MAP_W:.1f},{MAP_T + rpts[j+1][1]*MAP_H:.1f}")
        # River width increases downstream
        parts.append(f'<path d="{pd}" fill="none" stroke="#7ab0cc" stroke-width="1.5" opacity="0.5" stroke-linecap="round"/>')
        # River name label along first segment
        if len(rpts) > 10:
            mid = len(rpts) // 4
            lx = MAP_L + rpts[mid][0] * MAP_W
            ly = MAP_T + rpts[mid][1] * MAP_H
            angle = math.degrees(math.atan2(
                rpts[mid+1][1] - rpts[mid][1],
                rpts[mid+1][0] - rpts[mid][0]
            ))
            parts.append(f'<text x="{lx:.0f}" y="{ly:.0f}" font-family="Georgia,serif" font-size="6" '
                         f'fill="#5a90b0" opacity="0.4" font-style="italic" '
                         f'transform="rotate({angle:.0f},{lx:.0f},{ly:.0f})" text-anchor="middle">R. {river_paths.index(rpts)+1}</text>')

    # --- CONTOUR LINES ---
    n_levels = max(12, min(25, 10 + followers // 10))
    levels = [i / n_levels for i in range(1, n_levels)]

    for li, level in enumerate(levels):
        chains = extract_contours(level)
        is_index = li % 5 == 0  # Index contour every 5th
        sw = 0.8 if is_index else 0.3
        stroke_color = "#5a6858" if level < 0.5 else "#7a5a3a"
        op = 0.5 if is_index else 0.2

        for chain in chains:
            if len(chain) < 2: continue
            pd = f"M{chain[0][0]:.1f},{chain[0][1]:.1f}"
            for j in range(1, len(chain)-1, 2):
                if j+1 < len(chain):
                    pd += f" Q{chain[j][0]:.1f},{chain[j][1]:.1f} {chain[j+1][0]:.1f},{chain[j+1][1]:.1f}"
                else:
                    pd += f" L{chain[j][0]:.1f},{chain[j][1]:.1f}"
            parts.append(f'<path d="{pd}" fill="none" stroke="{stroke_color}" stroke-width="{sw}" '
                         f'opacity="{op:.2f}" stroke-linecap="round" stroke-linejoin="round"/>')

        # Elevation label on index contours
        if is_index and chains:
            longest = max(chains, key=len)
            mid = longest[len(longest)//2]
            elev_label = f"{int(level * 1000)}m"
            # Background for readability
            parts.append(f'<rect x="{mid[0]-12:.0f}" y="{mid[1]-5:.0f}" width="24" height="8" fill="#f5f0e6" opacity="0.7" rx="1"/>')
            parts.append(f'<text x="{mid[0]:.0f}" y="{mid[1]+2:.0f}" font-family="monospace" font-size="5.5" '
                         f'fill="{stroke_color}" opacity="0.55" text-anchor="middle">{elev_label}</text>')

    # --- HACHURES on steep slopes ---
    for gy in range(2, grid-2, 4):
        for gx in range(2, grid-2, 4):
            e = elevation[gy, gx]
            dzdx = abs(elevation[gy, min(gx+1,grid-1)] - elevation[gy, max(gx-1,0)])
            dzdy = abs(elevation[min(gy+1,grid-1), gx] - elevation[max(gy-1,0), gx])
            slope = math.sqrt(dzdx*dzdx + dzdy*dzdy)
            if slope > 0.04 and 0.6 < e < 0.92:  # Steep mountain terrain
                mx, my = grid_to_map(gx, gy)
                aspect = math.atan2(-dzdy, dzdx)
                hlen = min(6, slope * 40)
                hx2 = mx + hlen * math.cos(aspect)
                hy2 = my + hlen * math.sin(aspect)
                parts.append(f'<line x1="{mx:.1f}" y1="{my:.1f}" x2="{hx2:.1f}" y2="{hy2:.1f}" '
                             f'stroke="#8a7050" stroke-width="0.25" opacity="0.15"/>')

    # --- GLACIER/SNOW PATTERN at peaks ---
    for gy in range(0, grid, 5):
        for gx in range(0, grid, 5):
            e = elevation[min(gy,grid-1), min(gx,grid-1)]
            if e > 0.92:
                mx, my = grid_to_map(gx, gy)
                # Stipple dots for snow
                for _ in range(3):
                    sx = mx + rng.uniform(0, cell_w*4)
                    sy = my + rng.uniform(0, cell_h*4)
                    parts.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="0.5" fill="#c0b8a8" opacity="0.2"/>')

    # --- SPOT HEIGHTS (triangle markers at peaks) ---
    # Find local maxima
    spot_heights = []
    for gy in range(3, grid-3, 8):
        for gx in range(3, grid-3, 8):
            e = elevation[gy, gx]
            is_peak = True
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    if dy == 0 and dx == 0: continue
                    if elevation[gy+dy, gx+dx] > e:
                        is_peak = False
                        break
                if not is_peak: break
            if is_peak and e > 0.5:
                mx, my = grid_to_map(gx, gy)
                spot_heights.append((mx, my, e))

    for sx, sy, se in spot_heights[:12]:  # Cap
        # Triangle marker
        ts = 3
        parts.append(f'<polygon points="{sx:.0f},{sy-ts:.0f} {sx-ts:.0f},{sy+ts:.0f} {sx+ts:.0f},{sy+ts:.0f}" '
                     f'fill="none" stroke="#5a4a3a" stroke-width="0.5" opacity="0.4"/>')
        parts.append(f'<text x="{sx+5:.0f}" y="{sy+2:.0f}" font-family="monospace" font-size="5" '
                     f'fill="#5a4a3a" opacity="0.4">{int(se*1000)}</text>')

    # --- TRAIL NETWORK connecting repos ---
    if len(repo_positions) > 1:
        # Connect repos to center and to nearest neighbors
        center = (0.5, 0.5)
        for rcx, rcy, repo in repo_positions:
            mx1 = MAP_L + rcx * MAP_W
            my1 = MAP_T + rcy * MAP_H
            mx2 = MAP_L + center[0] * MAP_W
            my2 = MAP_T + center[1] * MAP_H
            # Curved trail
            mcx = (mx1+mx2)/2 + rng.uniform(-20, 20)
            mcy = (my1+my2)/2 + rng.uniform(-20, 20)
            parts.append(f'<path d="M{mx1:.0f},{my1:.0f} Q{mcx:.0f},{mcy:.0f} {mx2:.0f},{my2:.0f}" '
                         f'fill="none" stroke="#a08060" stroke-width="0.4" opacity="0.2" '
                         f'stroke-dasharray="3 2"/>')

    # --- REPO LANDMARKS ---
    for rcx, rcy, repo in repo_positions:
        lx = MAP_L + rcx * MAP_W
        ly = MAP_T + rcy * MAP_H
        repo_stars = repo.get("stars", 0)
        name = repo.get("name", "")
        lang = repo.get("language")
        hue = LANG_HUES.get(lang, 160)
        marker_c = oklch(0.45, 0.18, hue)

        # Settlement symbol for high-star repos
        if repo_stars > 50:
            # Building symbol
            bs = 4 + min(4, repo_stars // 100)
            parts.append(f'<rect x="{lx-bs:.0f}" y="{ly-bs:.0f}" width="{bs*2:.0f}" height="{bs*2:.0f}" '
                         f'fill="{marker_c}" opacity="0.5" stroke="#3a2a1a" stroke-width="0.4"/>')
            parts.append(f'<rect x="{lx-bs+1:.0f}" y="{ly-bs+1:.0f}" width="{bs-2:.0f}" height="{bs-2:.0f}" '
                         f'fill="#f5f0e6" opacity="0.3"/>')
        else:
            # Circle marker
            mr = 2.5 + min(5, repo_stars * 0.3)
            parts.append(f'<circle cx="{lx:.0f}" cy="{ly:.0f}" r="{mr:.1f}" fill="{marker_c}" '
                         f'opacity="0.65" stroke="#fff" stroke-width="0.5"/>')

        # Label
        parts.append(f'<text x="{lx+8:.0f}" y="{ly+3:.0f}" font-family="Georgia,serif" font-size="6" '
                     f'fill="#4a3a2a" opacity="0.55" font-weight="bold">{name}</text>')
        if repo_stars > 0:
            parts.append(f'<text x="{lx+8:.0f}" y="{ly+10:.0f}" font-family="Georgia,serif" font-size="5" '
                         f'fill="#7a6a5a" opacity="0.4">{repo_stars} stars</text>')

    # Center marker
    parts.append(f'<circle cx="{MAP_L+MAP_W/2:.0f}" cy="{MAP_T+MAP_H/2:.0f}" r="5" fill="#cc3828" opacity="0.6" stroke="#fff" stroke-width="1"/>')
    parts.append(f'<text x="{MAP_L+MAP_W/2+9:.0f}" y="{MAP_T+MAP_H/2+3:.0f}" font-family="Georgia,serif" font-size="8" '
                 f'fill="#3a2a1a" font-weight="bold" opacity="0.6">{metrics.get("label","")}</text>')

    # --- MONTH MARKERS around edge ---
    month_labels = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    for mi, mkey in enumerate(months_sorted):
        angle = -math.pi/2 + mi * 2 * math.pi / max(1, len(months_sorted))
        lx = MAP_L + MAP_W/2 + (MAP_W/2 + 10) * math.cos(angle)
        ly = MAP_T + MAP_H/2 + (MAP_H/2 + 10) * math.sin(angle)
        # Clamp to map area
        lx = max(MAP_L - 20, min(MAP_R + 20, lx))
        ly = max(MAP_T - 20, min(MAP_B + 20, ly))
        month_num = int(mkey) - 1 if mkey.isdigit() else mi
        label = month_labels[month_num % 12]
        intensity = monthly[mkey] / max(1, max_m)
        parts.append(f'<text x="{lx:.0f}" y="{ly:.0f}" text-anchor="middle" dominant-baseline="central" '
                     f'font-family="Georgia,serif" font-size="7" fill="#5a4a3a" opacity="{0.25+intensity*0.45:.2f}">{label}</text>')

    # --- ORNATE COMPASS ROSE ---
    compass_cx = MAP_R - 45
    compass_cy = MAP_T + 45
    compass_r = 22

    # Outer ring
    parts.append(f'<circle cx="{compass_cx}" cy="{compass_cy}" r="{compass_r}" fill="none" stroke="#8a7a5a" stroke-width="0.6" opacity="0.4"/>')
    parts.append(f'<circle cx="{compass_cx}" cy="{compass_cy}" r="{compass_r-3}" fill="none" stroke="#a09070" stroke-width="0.3" opacity="0.3"/>')

    # Cardinal points (N, S, E, W)
    dirs = [("N", 0, -1), ("E", 1, 0), ("S", 0, 1), ("W", -1, 0)]
    for label, dx, dy in dirs:
        # Main pointer
        tip_x = compass_cx + dx * (compass_r - 2)
        tip_y = compass_cy + dy * (compass_r - 2)
        # Arrow
        perp_x, perp_y = -dy, dx
        parts.append(f'<polygon points="{compass_cx},{compass_cy} '
                     f'{compass_cx + perp_x*3},{compass_cy + perp_y*3} '
                     f'{tip_x},{tip_y} '
                     f'{compass_cx - perp_x*3},{compass_cy - perp_y*3}" '
                     f'fill="#8a7a5a" opacity="0.25" stroke="#6a5a3a" stroke-width="0.3"/>')
        # Label
        lx = compass_cx + dx * (compass_r + 6)
        ly = compass_cy + dy * (compass_r + 6)
        parts.append(f'<text x="{lx:.0f}" y="{ly:.0f}" text-anchor="middle" dominant-baseline="central" '
                     f'font-family="Georgia,serif" font-size="7" fill="#5a4a3a" opacity="0.5" '
                     f'font-weight="{"bold" if label == "N" else "normal"}">{label}</text>')

    # Intercardinal (NE, SE, SW, NW) — smaller
    for dx, dy in [(1,-1), (1,1), (-1,1), (-1,-1)]:
        d = math.sqrt(2)
        tip_x = compass_cx + dx/d * (compass_r - 6)
        tip_y = compass_cy + dy/d * (compass_r - 6)
        parts.append(f'<line x1="{compass_cx}" y1="{compass_cy}" x2="{tip_x:.0f}" y2="{tip_y:.0f}" '
                     f'stroke="#a09070" stroke-width="0.4" opacity="0.25"/>')

    # Center dot
    parts.append(f'<circle cx="{compass_cx}" cy="{compass_cy}" r="1.5" fill="#6a5a3a" opacity="0.4"/>')

    # --- CARTOGRAPHIC FRAME ---
    # Double frame
    parts.append(f'<rect x="{MAP_L-4}" y="{MAP_T-4}" width="{MAP_W+8}" height="{MAP_H+8}" '
                 f'fill="none" stroke="#7a6a4a" stroke-width="1.5" rx="1"/>')
    parts.append(f'<rect x="{MAP_L-1}" y="{MAP_T-1}" width="{MAP_W+2}" height="{MAP_H+2}" '
                 f'fill="none" stroke="#a09070" stroke-width="0.4"/>')

    # Tick marks with grid coordinates
    for i in range(0, 11):
        # Top and bottom
        tx = MAP_L + i * MAP_W / 10
        parts.append(f'<line x1="{tx:.0f}" y1="{MAP_T-4}" x2="{tx:.0f}" y2="{MAP_T-1}" stroke="#7a6a4a" stroke-width="0.5" opacity="0.4"/>')
        parts.append(f'<line x1="{tx:.0f}" y1="{MAP_B+1}" x2="{tx:.0f}" y2="{MAP_B+4}" stroke="#7a6a4a" stroke-width="0.5" opacity="0.4"/>')
        if i < 10 and i % 2 == 0:
            parts.append(f'<text x="{tx+MAP_W/20:.0f}" y="{MAP_B+12}" text-anchor="middle" font-family="monospace" font-size="5" fill="#8a7a5a" opacity="0.35">{i*10}</text>')
        # Left and right
        ty = MAP_T + i * MAP_H / 10
        parts.append(f'<line x1="{MAP_L-4}" y1="{ty:.0f}" x2="{MAP_L-1}" y2="{ty:.0f}" stroke="#7a6a4a" stroke-width="0.5" opacity="0.4"/>')
        parts.append(f'<line x1="{MAP_R+1}" y1="{ty:.0f}" x2="{MAP_R+4}" y2="{ty:.0f}" stroke="#7a6a4a" stroke-width="0.5" opacity="0.4"/>')

    # --- COORDINATE GRID (faint) ---
    for i in range(1, 10):
        gx_line = MAP_L + i * MAP_W / 10
        gy_line = MAP_T + i * MAP_H / 10
        parts.append(f'<line x1="{gx_line:.0f}" y1="{MAP_T}" x2="{gx_line:.0f}" y2="{MAP_B}" stroke="#a09878" stroke-width="0.15" opacity="0.1"/>')
        parts.append(f'<line x1="{MAP_L}" y1="{gy_line:.0f}" x2="{MAP_R}" y2="{gy_line:.0f}" stroke="#a09878" stroke-width="0.15" opacity="0.1"/>')

    # --- SCALE BAR ---
    sb_x = MAP_L + 10
    sb_y = MAP_B + 25
    sb_w = 100
    parts.append(f'<line x1="{sb_x}" y1="{sb_y}" x2="{sb_x+sb_w}" y2="{sb_y}" stroke="#5a4a3a" stroke-width="1.2"/>')
    parts.append(f'<line x1="{sb_x}" y1="{sb_y-3}" x2="{sb_x}" y2="{sb_y+3}" stroke="#5a4a3a" stroke-width="0.8"/>')
    parts.append(f'<line x1="{sb_x+sb_w}" y1="{sb_y-3}" x2="{sb_x+sb_w}" y2="{sb_y+3}" stroke="#5a4a3a" stroke-width="0.8"/>')
    parts.append(f'<line x1="{sb_x+sb_w//2}" y1="{sb_y-2}" x2="{sb_x+sb_w//2}" y2="{sb_y+2}" stroke="#5a4a3a" stroke-width="0.5"/>')
    # Alternating fill
    parts.append(f'<rect x="{sb_x}" y="{sb_y-1.5}" width="{sb_w//4}" height="3" fill="#5a4a3a" opacity="0.5"/>')
    parts.append(f'<rect x="{sb_x+sb_w//2}" y="{sb_y-1.5}" width="{sb_w//4}" height="3" fill="#5a4a3a" opacity="0.5"/>')
    parts.append(f'<text x="{sb_x+sb_w//2}" y="{sb_y-6}" text-anchor="middle" font-family="Georgia,serif" font-size="6" fill="#5a4a3a" opacity="0.5">{contributions} contributions</text>')
    parts.append(f'<text x="{sb_x}" y="{sb_y+10}" font-family="monospace" font-size="5" fill="#8a7a5a" opacity="0.4">0</text>')
    parts.append(f'<text x="{sb_x+sb_w}" y="{sb_y+10}" text-anchor="end" font-family="monospace" font-size="5" fill="#8a7a5a" opacity="0.4">{contributions}</text>')

    # --- ELEVATION PROFILE (cross-section at bottom) ---
    prof_x = MAP_L + 150
    prof_y = MAP_B + 20
    prof_w = MAP_W - 160
    prof_h = 30
    # Frame
    parts.append(f'<rect x="{prof_x}" y="{prof_y}" width="{prof_w}" height="{prof_h}" fill="none" stroke="#a09070" stroke-width="0.3" opacity="0.3"/>')
    parts.append(f'<text x="{prof_x}" y="{prof_y-3}" font-family="Georgia,serif" font-size="5" fill="#7a6a5a" opacity="0.4">Elevation Profile (E-W)</text>')

    # Draw profile along center horizontal
    mid_row = grid // 2
    prof_pts = []
    for pi in range(0, grid, 2):
        e = elevation[mid_row, pi]
        px = prof_x + (pi / grid) * prof_w
        py = prof_y + prof_h - e * prof_h * 0.85
        prof_pts.append(f"{px:.1f},{py:.1f}")
    # Fill under profile
    fill_path = f"M{prof_x},{prof_y+prof_h} L" + " L".join(prof_pts) + f" L{prof_x+prof_w},{prof_y+prof_h} Z"
    parts.append(f'<path d="{fill_path}" fill="#d8d0c0" opacity="0.3"/>')
    # Profile line
    parts.append(f'<polyline points="{" ".join(prof_pts)}" fill="none" stroke="#7a6a4a" stroke-width="0.5" opacity="0.4"/>')

    # --- LEGEND ---
    leg_x = MAP_R - 110
    leg_y = MAP_B + 17
    leg_w = 100
    parts.append(f'<rect x="{leg_x}" y="{leg_y}" width="{leg_w}" height="36" fill="#f5f0e6" stroke="#a09070" stroke-width="0.3" rx="1" opacity="0.9"/>')
    parts.append(f'<text x="{leg_x+4}" y="{leg_y+8}" font-family="Georgia,serif" font-size="6" fill="#4a3a2a" font-weight="bold" opacity="0.5">LEGEND</text>')

    legend_items = [
        ("circle", "#cc3828", "Profile center"),
        ("line", "#7ab0cc", "River"),
        ("line_dash", "#a08060", "Trail"),
    ]
    for li, (shape, color, text) in enumerate(legend_items):
        iy = leg_y + 15 + li * 7
        if shape == "circle":
            parts.append(f'<circle cx="{leg_x+8}" cy="{iy}" r="2" fill="{color}" opacity="0.6"/>')
        elif shape == "line":
            parts.append(f'<line x1="{leg_x+4}" y1="{iy}" x2="{leg_x+12}" y2="{iy}" stroke="{color}" stroke-width="1" opacity="0.5"/>')
        elif shape == "line_dash":
            parts.append(f'<line x1="{leg_x+4}" y1="{iy}" x2="{leg_x+12}" y2="{iy}" stroke="{color}" stroke-width="0.5" opacity="0.4" stroke-dasharray="2 1"/>')
        parts.append(f'<text x="{leg_x+16}" y="{iy+2}" font-family="Georgia,serif" font-size="5" fill="#5a4a3a" opacity="0.45">{text}</text>')

    # --- TITLE CARTOUCHE ---
    tc_x = MAP_L
    tc_y = HEIGHT - 30
    parts.append(f'<text x="{tc_x}" y="{tc_y}" font-family="Georgia,serif" font-size="10" fill="#4a3a2a" font-weight="bold" opacity="0.5">'
                 f'Topographic Survey: {metrics.get("label","")}</text>')
    parts.append(f'<text x="{tc_x}" y="{tc_y+12}" font-family="Georgia,serif" font-size="6" fill="#7a6a5a" opacity="0.35">'
                 f'{len(repos)} repositories  |  {contributions} contributions  |  {stars} stars</text>')

    parts.append('</svg>')
    return '\n'.join(parts)


# =========================================================================
# Main
# =========================================================================

if __name__ == "__main__":
    out_dir = Path(".github/assets/img")
    out_dir.mkdir(parents=True, exist_ok=True)

    for pname, metrics in PROFILES.items():
        print(f"\n--- {metrics['label']} ---")
        for slug, gen in [("inkgarden-ult", generate_ink_garden_ultimate),
                          ("topo-ult", generate_topography_ultimate)]:
            svg = gen(metrics)
            out = out_dir / f"proto-v10-{slug}-{pname}.svg"
            out.write_text(svg, encoding="utf-8")
            print(f"  {slug}: {len(svg)//1024} KB -> {out}")

    print("\nDone!")
