"""
Generative Art Prototypes v7 — Maximum Data Meaning
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Every GitHub metric is a distinct visual force. Nothing is wasted.

PIECE: "Digital Genesis" — Your entire GitHub life as one living cosmos.

DATA → VISUAL MAPPING (every metric has a specific, creative role):

STRUCTURAL / SPATIAL:
- public_repos → number of celestial bodies (each repo = one orbital body)
- repo language → body color (language hue map, each language a species of light)
- repo stars → body luminosity + corona size (popular = radiant)
- repo age → orbital radius (oldest repos = outermost orbits, newest = innermost)
- repo size → body mass (bigger codebase = larger diameter)

ATMOSPHERIC:
- contributions_monthly → atmospheric density at each month-angle
  (Jan=12 o'clock, clockwise). Dense months = thick luminous fog,
  quiet months = void. Your year's rhythm becomes visible weather.
- contributions_last_year → overall atmospheric brightness
- total_commits → nebula background turbulence complexity (more history = richer texture)

GRAVITATIONAL / SOCIAL:
- followers → gravitational field strength (pulls everything tighter, denser)
- following → escape velocity (higher = more outward tendrils reaching out)
- followers/following ratio → field asymmetry (lopsided = more inward pull on one side)

NETWORK / COMMUNITY:
- stars (total) → number of particle trails orbiting outward (each star = one photon escaping)
- forks → underground mycelium connections between repos (shared DNA spreading)
- watchers → ambient watchfire nodes that pulse at the edges
- network_count → connective tissue density (edges between related bodies)
- open_issues → small red dwarf satellites orbiting their parent bodies

TEMPORAL / ARCHAEOLOGICAL:
- account_age → geological strata rings (each year = one ring, like tree growth)
- star_events timeline → meteor showers (bursts of incoming light at specific months)
- contribution streak patterns → aurora ribbons that trace the streaks

ORGANIZATIONAL:
- orgs_count → number of distinct orbital planes (each org tilts the orbits differently)
  Multiple orgs = complex intersecting orbital mechanics

Everything is animated: bodies orbit, atmospheres breathe, stars pulse, meteors flash.
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
DURATION = 30

LANG_HUES = {
    "Python": 210, "JavaScript": 50, "TypeScript": 215, "Java": 10,
    "C++": 290, "C": 260, "Go": 175, "Rust": 25, "Ruby": 350,
    "Swift": 15, "Kotlin": 280, "Shell": 120, "HTML": 30, "CSS": 200,
    "R": 240, "Jupyter Notebook": 170, "Scala": 340, None: 160,
}

PROFILES = {
    "wyatt": {
        "label": "wyattowalsh", "stars": 42, "forks": 12, "watchers": 8,
        "followers": 85, "following": 60, "public_repos": 35, "orgs_count": 3,
        "contributions_last_year": 1200, "total_commits": 4800,
        "open_issues_count": 5, "network_count": 18, "account_age_years": 8,
        "repos": [
            {"name": "gnn-mol", "language": "Python", "stars": 12, "age_months": 24, "size_kb": 8500},
            {"name": "ball", "language": "Python", "stars": 8, "age_months": 36, "size_kb": 12000},
            {"name": "portfolio", "language": "TypeScript", "stars": 5, "age_months": 18, "size_kb": 4200},
            {"name": "dotfiles", "language": "Shell", "stars": 3, "age_months": 60, "size_kb": 800},
            {"name": "nba-db", "language": "Python", "stars": 6, "age_months": 48, "size_kb": 15000},
            {"name": "wyattowalsh", "language": "Python", "stars": 2, "age_months": 12, "size_kb": 2000},
            {"name": "research", "language": "Jupyter Notebook", "stars": 4, "age_months": 30, "size_kb": 6000},
        ],
        "contributions_monthly": {
            "01": 120, "02": 95, "03": 180, "04": 210, "05": 140, "06": 60,
            "07": 45, "08": 80, "09": 150, "10": 200, "11": 170, "12": 90,
        },
        "star_events": [
            {"month": 1, "count": 3}, {"month": 3, "count": 5}, {"month": 4, "count": 8},
            {"month": 6, "count": 2}, {"month": 9, "count": 7}, {"month": 11, "count": 4},
        ],
    },
    "prolific": {
        "label": "Prolific OSS", "stars": 5200, "forks": 890, "watchers": 340,
        "followers": 12000, "following": 150, "public_repos": 180, "orgs_count": 8,
        "contributions_last_year": 3800, "total_commits": 42000,
        "open_issues_count": 120, "network_count": 2400, "account_age_years": 14,
        "repos": [
            {"name": f"proj-{i}", "language": lang, "stars": s, "age_months": a, "size_kb": sz}
            for i, (lang, s, a, sz) in enumerate([
                ("Python",1200,84,50000),("JavaScript",800,96,35000),("TypeScript",600,48,28000),
                ("Go",400,60,22000),("Rust",350,36,18000),("C++",280,108,45000),
                ("Python",200,72,15000),("Shell",150,120,5000),("Ruby",120,90,12000),
                ("Java",100,60,20000),("Python",80,24,8000),("TypeScript",60,36,6000),
                ("Go",40,18,4000),("Rust",30,12,3000),("Python",20,6,2000),
            ])
        ],
        "contributions_monthly": {
            "01":380,"02":420,"03":350,"04":400,"05":310,"06":280,
            "07":290,"08":320,"09":360,"10":400,"11":380,"12":310,
        },
        "star_events": [
            {"month":m,"count":c} for m,c in
            [(1,45),(2,38),(3,52),(4,60),(5,42),(6,35),(7,30),(8,38),(9,55),(10,65),(11,48),(12,40)]
        ],
    },
    "newcomer": {
        "label": "New Developer", "stars": 3, "forks": 1, "watchers": 2,
        "followers": 8, "following": 45, "public_repos": 6, "orgs_count": 1,
        "contributions_last_year": 180, "total_commits": 320,
        "open_issues_count": 2, "network_count": 3, "account_age_years": 1,
        "repos": [
            {"name": "hello-world", "language": "Python", "stars": 1, "age_months": 8, "size_kb": 500},
            {"name": "todo-app", "language": "JavaScript", "stars": 2, "age_months": 5, "size_kb": 1200},
            {"name": "portfolio", "language": "HTML", "stars": 0, "age_months": 3, "size_kb": 300},
        ],
        "contributions_monthly": {
            "07":10,"08":25,"09":30,"10":40,"11":35,"12":40,
        },
        "star_events": [{"month":10,"count":2},{"month":12,"count":1}],
    },
}


def _sh(m):
    s = "-".join(str(m.get(k,0)) for k in sorted(m.keys()) if k not in ("label","repos","contributions_monthly","star_events"))
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
        angles=rng.uniform(0,2*np.pi,256);self.grads=np.column_stack([np.cos(angles),np.sin(angles)])
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


def generate_digital_genesis(metrics: dict, dark_mode: bool = True) -> str:
    h = _sh(metrics)
    rng = np.random.default_rng(int(h[:8], 16))
    noise = Noise2D(seed=int(h[8:16], 16))

    repos = metrics.get("repos", [])
    monthly = metrics.get("contributions_monthly", {})
    star_events = metrics.get("star_events", [])
    max_monthly = max(monthly.values()) if monthly else 100
    followers = metrics.get("followers", 10)
    following = metrics.get("following", 10)
    total_stars = metrics.get("stars", 5)
    total_forks = metrics.get("forks", 2)
    watchers = metrics.get("watchers", 2)
    total_commits = metrics.get("total_commits", 500)
    open_issues = metrics.get("open_issues_count", 0)
    network = metrics.get("network_count", 5)
    orgs = metrics.get("orgs_count", 1)
    age = metrics.get("account_age_years", 1)

    # --- GRAVITY from followers ---
    gravity = min(0.8, followers / 8000)
    max_orbit = 350 * (1 - gravity * 0.3)

    # --- ESCAPE VELOCITY from following (outward reaching tendrils) ---
    escape = min(1.0, following / 200)

    # --- FIELD ASYMMETRY from follower/following ratio ---
    if following > 0:
        asym = min(2.0, followers / following)
    else:
        asym = 2.0

    # --- NEBULA COMPLEXITY from total_commits ---
    nebula_octaves = max(3, min(7, 3 + total_commits // 5000))
    nebula_seed = int(h[16:20], 16) % 999

    # --- ORBITAL PLANES from orgs ---
    orbital_tilts = []
    for oi in range(orgs):
        tilt = (oi * 137.508 + _hf(h, 20+oi, 22+oi) * 60) % 360  # golden angle
        orbital_tilts.append(tilt)

    # --- REPO → CELESTIAL BODY ---
    bodies = []
    max_age = max((r.get("age_months", 1) for r in repos), default=1)
    max_size = max((r.get("size_kb", 1) for r in repos), default=1)
    max_repo_stars = max((r.get("stars", 0) for r in repos), default=1) or 1

    for ri, repo in enumerate(repos):
        lang = repo.get("language")
        hue = LANG_HUES.get(lang, 160)
        stars_r = repo.get("stars", 0)
        age_m = repo.get("age_months", 6)
        size_kb = repo.get("size_kb", 1000)

        # Orbital radius: older repos = farther out (geological layering)
        orbit_r = 40 + (age_m / max(1, max_age)) * (max_orbit - 40)
        # Assign to an orbital plane
        plane_idx = ri % max(1, orgs)
        tilt = orbital_tilts[plane_idx] if orbital_tilts else 0
        # Angular position: spread evenly + golden-angle offset
        angle = ri * 2.399 + tilt * math.pi / 180  # golden angle

        # Gravitational compression (followers pull inward)
        orbit_r *= (1 - gravity * 0.3)

        x = CX + orbit_r * math.cos(angle)
        y = CY + orbit_r * math.sin(angle) * (0.7 + 0.3 * math.cos(tilt * math.pi / 180))  # elliptical

        # Body radius from codebase size
        body_r = 2 + (size_kb / max(1, max_size)) * 8
        # Luminosity from stars
        luminosity = 0.25 + (stars_r / max(1, max_repo_stars)) * 0.65
        # Corona from star count
        corona_r = body_r * (1 + stars_r * 0.3)

        bodies.append({
            "x": x, "y": y, "r": body_r, "hue": hue, "lum": luminosity,
            "corona_r": min(30, corona_r), "orbit_r": orbit_r, "angle": angle,
            "stars": stars_r, "issues": min(3, max(0, int(open_issues * ri / max(1, len(repos))))),
            "name": repo.get("name", ""), "tilt": tilt,
        })

    # --- ATMOSPHERIC DENSITY from monthly contributions ---
    # At each month-angle, contribution count determines fog density
    atm_segments = []
    months_sorted = sorted(monthly.keys())
    for mi, mkey in enumerate(months_sorted):
        count = monthly[mkey]
        intensity = count / max(1, max_monthly)
        angle = -math.pi/2 + mi * 2 * math.pi / max(1, len(months_sorted))
        atm_segments.append((angle, intensity))

    # --- STAR PHOTON TRAILS (total stars → escaping light particles) ---
    n_photons = max(5, min(80, total_stars))
    photon_trails = []
    for pi in range(n_photons):
        # Start near a random body
        if bodies:
            b = bodies[pi % len(bodies)]
            px, py = b["x"] + rng.uniform(-5, 5), b["y"] + rng.uniform(-5, 5)
        else:
            px = CX + rng.uniform(-100, 100)
            py = CY + rng.uniform(-100, 100)

        # Fly outward with curl noise
        pts = [(px, py)]
        for ps in range(40):
            dx = px - CX; dy = py - CY
            dist = math.sqrt(dx*dx + dy*dy) + 1e-10
            # Outward bias + noise
            nv = noise.fbm(px * 0.005, py * 0.005, 3)
            vx = dx / dist * 2 + nv * 3
            vy = dy / dist * 2 + noise.fbm(px * 0.005 + 100, py * 0.005, 3) * 3
            px += vx; py += vy
            if px < -10 or px > WIDTH+10 or py < -10 or py > HEIGHT+10:
                break
            pts.append((px, py))
        if len(pts) > 5:
            hue = bodies[pi % len(bodies)]["hue"] if bodies else 200
            photon_trails.append((pts, hue))

    # --- FORK MYCELIUM (underground connections between same-language repos) ---
    mycelium_paths = []
    lang_groups = {}
    for bi, b in enumerate(bodies):
        lg = b.get("hue", 0)
        if lg not in lang_groups: lang_groups[lg] = []
        lang_groups[lg].append(bi)

    n_myc = min(total_forks, 60)
    myc_count = 0
    for hue, indices in lang_groups.items():
        if len(indices) < 2: continue
        for i in range(len(indices)):
            for j in range(i+1, len(indices)):
                if myc_count >= n_myc: break
                b1 = bodies[indices[i]]; b2 = bodies[indices[j]]
                # Organic curved path between them
                pts = []
                for t in range(20):
                    frac = t / 19
                    x = b1["x"] + (b2["x"] - b1["x"]) * frac
                    y = b1["y"] + (b2["y"] - b1["y"]) * frac
                    # Noise displacement
                    x += noise.fbm(x*0.01 + myc_count, y*0.01, 2) * 25
                    y += noise.fbm(x*0.01, y*0.01 + myc_count, 2) * 25
                    pts.append((x, y))
                mycelium_paths.append((pts, hue))
                myc_count += 1

    # --- WATCHER WATCHFIRES (ambient pulsing nodes at edges) ---
    watchfires = []
    for wi in range(min(watchers, 30)):
        angle = wi * 2.399  # golden angle
        wr = rng.uniform(330, 380)
        wx = CX + wr * math.cos(angle)
        wy = CY + wr * math.sin(angle)
        watchfires.append((wx, wy))

    # --- METEOR SHOWERS from star_events ---
    meteors = []
    for se in star_events:
        m = se["month"] - 1
        angle = -math.pi/2 + m * 2 * math.pi / 12
        for mi in range(se["count"]):
            start_r = rng.uniform(350, 420)
            end_r = rng.uniform(100, 250)
            a_var = rng.uniform(-0.15, 0.15)
            sx = CX + start_r * math.cos(angle + a_var)
            sy = CY + start_r * math.sin(angle + a_var)
            ex = CX + end_r * math.cos(angle + a_var + rng.uniform(-0.1, 0.1))
            ey = CY + end_r * math.sin(angle + a_var + rng.uniform(-0.1, 0.1))
            meteors.append((sx, sy, ex, ey))

    # --- AURORA RIBBONS from contribution streaks ---
    # Find consecutive months with above-average contributions
    avg_monthly = sum(monthly.values()) / max(1, len(monthly)) if monthly else 0
    aurora_arcs = []
    streak_months = []
    for mi, mkey in enumerate(months_sorted):
        if monthly[mkey] > avg_monthly * 0.8:
            streak_months.append(mi)
        else:
            if len(streak_months) >= 2:
                aurora_arcs.append(streak_months[:])
            streak_months = []
    if len(streak_months) >= 2:
        aurora_arcs.append(streak_months[:])

    # ======================== BUILD SVG ========================
    bg1 = "#030310" if dark_mode else "#f5f5ff"
    bg2 = "#010108" if dark_mode else "#eeeef5"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">
<defs>
  <filter id="bloom" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="b1"/>
    <feGaussianBlur in="SourceGraphic" stdDeviation="7" result="b2"/>
    <feGaussianBlur in="SourceGraphic" stdDeviation="16" result="b3"/>
    <feColorMatrix in="b3" type="matrix" result="bright"
      values="1.8 0 0 0 0.12  0 1.8 0 0 0.12  0 0 1.8 0 0.12  0 0 0 0.5 0"/>
    <feMerge><feMergeNode in="bright"/><feMergeNode in="b2"/>
      <feMergeNode in="b1"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="glow" x="-100%" y="-100%" width="300%" height="300%">
    <feGaussianBlur stdDeviation="6"/>
    <feColorMatrix type="matrix" values="1.4 0 0 0 0.08  0 1.4 0 0 0.08  0 0 1.4 0 0.08  0 0 0 0.5 0"/>
  </filter>
  <filter id="nebula" x="0%" y="0%" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.003 0.004" numOctaves="{nebula_octaves}" seed="{nebula_seed}" result="t"/>
    <feColorMatrix in="t" type="matrix" result="tint"
      values="0.06 0 0 0 0.01  0 0.03 0 0 0.01  0 0 0.12 0 0.04  0 0 0 0.30 0"/>
  </filter>
  <radialGradient id="bg" cx="50%" cy="50%" r="60%">
    <stop offset="0%" stop-color="{bg1}"/><stop offset="100%" stop-color="{bg2}"/>
  </radialGradient>
  <radialGradient id="vig" cx="50%" cy="50%" r="55%">
    <stop offset="35%" stop-color="black" stop-opacity="0"/>
    <stop offset="100%" stop-color="black" stop-opacity="0.6"/>
  </radialGradient>
</defs>
<style>
  @keyframes orbit {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
  @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: var(--op); }} }}
  @keyframes pulse {{ 0%,100% {{ opacity: var(--op); r: var(--r); }} 50% {{ opacity: calc(var(--op)*1.4); r: calc(var(--r)*1.2); }} }}
  @keyframes meteor {{ 0% {{ opacity:0.8; stroke-dashoffset: var(--len); }} 100% {{ opacity:0; stroke-dashoffset:0; }} }}
  @keyframes photon {{ from {{ stroke-dashoffset: var(--len); opacity:0; }} to {{ stroke-dashoffset:0; opacity: var(--op); }} }}
  @keyframes watchfire {{ 0%,100% {{ opacity:0.15; }} 50% {{ opacity:0.4; }} }}
  @keyframes auroraShimmer {{ 0%,100% {{ opacity: var(--op); }} 50% {{ opacity: calc(var(--op)*1.5); }} }}
  .body {{ animation: fadeIn 1s ease-out forwards; opacity:0; }}
  .corona {{ animation: pulse 5s ease-in-out infinite; }}
  .photon {{ stroke-dasharray: var(--len); stroke-dashoffset: var(--len); animation: photon var(--dur) ease-out forwards; }}
  .meteor-path {{ stroke-dasharray: var(--len); stroke-dashoffset: var(--len); animation: meteor 2s ease-out infinite; }}
  .watchfire {{ animation: watchfire 4s ease-in-out infinite; }}
  .aurora {{ animation: auroraShimmer 8s ease-in-out infinite; }}
  .myc {{ animation: fadeIn 2s ease-out forwards; opacity:0; }}
  .issue {{ animation: orbit var(--dur) linear infinite; transform-origin: var(--ox) var(--oy); }}
</style>
"""
    svg += f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#bg)"/>\n'

    # L1: Nebula background (total_commits → complexity)
    svg += f'<rect width="{WIDTH}" height="{HEIGHT}" filter="url(#nebula)" opacity="0.5"/>\n'

    # L2: Tree rings / geological strata (account_age)
    for yr in range(age):
        r = 30 + yr * (360 / max(1, age))
        c = oklch(0.15 + yr * 0.02, 0.04, 220 + yr * 8)
        svg += f'<circle cx="{CX}" cy="{CY}" r="{r:.0f}" fill="none" stroke="{c}" stroke-width="0.4" opacity="0.06"/>\n'

    # L3: Atmospheric density (contributions_monthly)
    for angle, intensity in atm_segments:
        if intensity < 0.05: continue
        # Wedge-shaped atmospheric glow
        r1 = 50; r2 = 50 + intensity * 300
        arc_w = 2 * math.pi / max(1, len(atm_segments)) * 0.9
        # Simple circle approximation at the angular position
        ax = CX + (r1 + r2) / 2 * math.cos(angle)
        ay = CY + (r1 + r2) / 2 * math.sin(angle)
        ar = 20 + intensity * 60
        c = oklch(0.15 + intensity * 0.15, 0.08 + intensity * 0.06, 200 + intensity * 60)
        svg += f'<circle cx="{ax:.0f}" cy="{ay:.0f}" r="{ar:.0f}" fill="{c}" opacity="{intensity * 0.10:.3f}"/>\n'

    # L4: Mycelium connections (forks → underground shared-language links)
    svg += '<g filter="url(#bloom)" opacity="0.6">\n'
    for mi, (pts, hue) in enumerate(mycelium_paths):
        c = oklch(0.25, 0.08, hue)
        delay = mi / max(1, len(mycelium_paths)) * DURATION * 0.5
        pd = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
        for j in range(1, len(pts)-1, 2):
            if j+1<len(pts): pd += f" Q{pts[j][0]:.1f},{pts[j][1]:.1f} {pts[j+1][0]:.1f},{pts[j+1][1]:.1f}"
        svg += f'<path d="{pd}" fill="none" stroke="{c}" stroke-width="0.4" stroke-dasharray="3,4" class="myc" style="animation-delay:{delay:.1f}s;--op:0.15"/>\n'
    svg += '</g>\n'

    # L5: Orbital tracks (faint ellipses for each body)
    for b in bodies:
        c = oklch(0.15, 0.03, b["hue"])
        # Ellipse approximation
        ry = b["orbit_r"] * (0.7 + 0.3 * math.cos(b["tilt"] * math.pi / 180))
        svg += f'<ellipse cx="{CX}" cy="{CY}" rx="{b["orbit_r"]:.0f}" ry="{ry:.0f}" fill="none" stroke="{c}" stroke-width="0.3" opacity="0.04" transform="rotate({b['tilt']:.0f},{CX},{CY})"/>\n'

    # L6: Photon trails (stars → escaping light)
    svg += '<g filter="url(#bloom)">\n'
    for pi, (pts, hue) in enumerate(photon_trails):
        c = oklch(0.5, 0.12, hue)
        pd = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
        pl = 0
        for j in range(1, len(pts)-1, 2):
            if j+1<len(pts):
                pd += f" Q{pts[j][0]:.1f},{pts[j][1]:.1f} {pts[j+1][0]:.1f},{pts[j+1][1]:.1f}"
                pl += math.sqrt((pts[j+1][0]-pts[max(0,j-1)][0])**2+(pts[j+1][1]-pts[max(0,j-1)][1])**2)
        delay = pi / n_photons * DURATION * 0.7
        svg += f'<path d="{pd}" fill="none" stroke="{c}" stroke-width="0.5" stroke-linecap="round" class="photon" style="--len:{max(1,pl):.0f};--op:0.20;--dur:{2+rng.uniform(0,3):.1f}s;animation-delay:{delay:.1f}s"/>\n'
    svg += '</g>\n'

    # L7: Celestial bodies (repos)
    svg += '<g filter="url(#bloom)">\n'
    for bi, b in enumerate(bodies):
        delay = bi / max(1, len(bodies)) * DURATION * 0.5
        c_body = oklch(0.3 + b["lum"] * 0.4, 0.14 + b["lum"] * 0.06, b["hue"])
        c_corona = oklch(0.4 + b["lum"] * 0.3, 0.10, b["hue"])

        # Corona (star glow)
        if b["stars"] > 0:
            svg += (f'<circle cx="{b["x"]:.1f}" cy="{b["y"]:.1f}" r="{b["corona_r"]:.1f}" '
                    f'fill="{c_corona}" class="corona" filter="url(#glow)" '
                    f'style="--op:{b["lum"]*0.15:.3f};--r:{b["corona_r"]:.0f};'
                    f'animation-delay:{delay:.1f}s"/>\n')

        # Body
        svg += (f'<circle cx="{b["x"]:.1f}" cy="{b["y"]:.1f}" r="{b["r"]:.1f}" '
                f'fill="{c_body}" class="body" '
                f'style="animation-delay:{delay:.2f}s;--op:{0.5+b["lum"]*0.4:.3f}"/>\n')

        # Issues as red dwarf satellites
        for ii in range(b["issues"]):
            issue_angle = ii * 2 * math.pi / max(1, b["issues"])
            issue_r = b["r"] + 5 + ii * 3
            ix = b["x"] + issue_r * math.cos(issue_angle)
            iy = b["y"] + issue_r * math.sin(issue_angle)
            ic = oklch(0.4, 0.18, 15)  # red
            dur = 6 + ii * 2
            svg += (f'<circle cx="{ix:.1f}" cy="{iy:.1f}" r="1.2" fill="{ic}" opacity="0.5" '
                    f'class="issue" style="--dur:{dur}s;--ox:{b["x"]:.0f}px;--oy:{b["y"]:.0f}px"/>\n')

    svg += '</g>\n'

    # L8: Watchfires (watchers → edge sentinels)
    for wi, (wx, wy) in enumerate(watchfires):
        c = oklch(0.4, 0.10, 50)
        delay = rng.uniform(0, 5)
        svg += (f'<circle cx="{wx:.0f}" cy="{wy:.0f}" r="1.5" fill="{c}" '
                f'class="watchfire" style="animation-delay:{delay:.1f}s;--op:0.15"/>\n')

    # L9: Meteor showers (star events → incoming light)
    if meteors:
        svg += '<g filter="url(#bloom)">\n'
        for mi, (sx, sy, ex, ey) in enumerate(meteors):
            seg_len = math.sqrt((ex-sx)**2 + (ey-sy)**2)
            c = oklch(0.85, 0.06, 55)
            delay = rng.uniform(0, DURATION * 0.9)
            dur = 1.5 + rng.uniform(0, 2)
            svg += (f'<line x1="{sx:.0f}" y1="{sy:.0f}" x2="{ex:.0f}" y2="{ey:.0f}" '
                    f'stroke="{c}" stroke-width="0.8" stroke-linecap="round" '
                    f'class="meteor-path" style="--len:{seg_len:.0f};animation-delay:{delay:.1f}s;animation-duration:{dur:.1f}s"/>\n')
        svg += '</g>\n'

    # L10: Aurora ribbons (contribution streaks)
    if aurora_arcs:
        svg += '<g filter="url(#bloom)">\n'
        for ai, arc_months in enumerate(aurora_arcs):
            arc_pts = []
            for ami in arc_months:
                angle = -math.pi/2 + ami * 2 * math.pi / max(1, len(months_sorted))
                r = 180 + rng.uniform(-20, 20)
                x = CX + r * math.cos(angle)
                y = CY + r * math.sin(angle)
                arc_pts.append((x, y))
            if len(arc_pts) < 2: continue
            pd = f"M{arc_pts[0][0]:.1f},{arc_pts[0][1]:.1f}"
            for j in range(1, len(arc_pts)):
                pd += f" L{arc_pts[j][0]:.1f},{arc_pts[j][1]:.1f}"

            aurora_hue = 160 + ai * 40
            c = oklch(0.45, 0.14, aurora_hue)
            delay = rng.uniform(0, 3)
            svg += (f'<path d="{pd}" fill="none" stroke="{c}" stroke-width="3" '
                    f'stroke-linecap="round" opacity="0.08" class="aurora" '
                    f'style="--op:0.08;animation-delay:{delay:.1f}s"/>\n')
        svg += '</g>\n'

    # L11: Outward tendrils (following → escape velocity / reaching out)
    n_tendrils = max(3, min(15, int(following * 0.1)))
    svg += '<g filter="url(#bloom)" opacity="0.4">\n'
    for ti in range(n_tendrils):
        angle = ti * 2.399 + rng.uniform(-0.3, 0.3)
        # Start from mid-radius, extend outward
        pts = []
        x = CX + 150 * math.cos(angle)
        y = CY + 150 * math.sin(angle)
        for ts in range(30):
            dx = x - CX; dy = y - CY
            dist = math.sqrt(dx*dx + dy*dy) + 1e-10
            nv = noise.fbm(x * 0.005 + ti, y * 0.005, 3)
            vx = dx / dist * 2.5 + nv * 2
            vy = dy / dist * 2.5 + noise.fbm(x * 0.005 + 50, y * 0.005 + ti, 3) * 2
            x += vx; y += vy
            if x < -10 or x > WIDTH+10 or y < -10 or y > HEIGHT+10: break
            pts.append((x, y))
        if len(pts) > 5:
            c = oklch(0.35, 0.08, 180 + ti * 20)
            pd = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
            for j in range(1, len(pts)-1, 2):
                if j+1<len(pts): pd += f" Q{pts[j][0]:.1f},{pts[j][1]:.1f} {pts[j+1][0]:.1f},{pts[j+1][1]:.1f}"
            pl = sum(math.sqrt((pts[j][0]-pts[j-1][0])**2+(pts[j][1]-pts[j-1][1])**2) for j in range(1,len(pts)))
            delay = ti / n_tendrils * DURATION * 0.4
            svg += f'<path d="{pd}" fill="none" stroke="{c}" stroke-width="0.5" stroke-linecap="round" class="photon" style="--len:{max(1,pl):.0f};--op:0.12;--dur:4s;animation-delay:{delay:.1f}s"/>\n'
    svg += '</g>\n'

    if dark_mode:
        svg += f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#vig)"/>\n'

    svg += '</svg>\n'
    return svg


if __name__ == "__main__":
    out_dir = Path(".github/assets/img")
    for pname, metrics in PROFILES.items():
        svg = generate_digital_genesis(metrics, dark_mode=True)
        out = out_dir / f"proto-v7-genesis-{pname}-dark.svg"
        out.write_text(svg, encoding="utf-8")
        print(f"{metrics['label']}: {len(svg)//1024} KB → {out}")
    print("\nDone!")
