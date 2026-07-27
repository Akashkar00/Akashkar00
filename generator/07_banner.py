"""Phase 1: assemble dark.svg / light.svg.

Structure notes that matter if you edit this later:

  * Two portrait layers, not one. The intro reveals ~60 groups scattered across
    the whole portrait; the loop drifts ~94 spatially-coherent bands. Those are
    incompatible groupings of the same dots, so the dot data is emitted twice.
    Merging them into one layer breaks the intro.

  * Drift is a linear function of position, so clustering it directly recreates
    a square grid and the dissolve looks blocky. Per-dot noise is added before
    clustering; STRAIGHT_METRIC below verifies the result is not a grid.

  * Dots are <path> runs with shape-rendering="crispEdges" -- never font
    glyphs, which mush below ~2px.

  * Every info row is locked with textLength + lengthAdjust="spacingAndGlyphs",
    so values stay aligned under whatever monospace the viewer actually has.
    Leaders are drawn as paths, not text, for the same reason.
"""
import numpy as np
from scipy.cluster.vq import kmeans2

W, H = 1180, 610
BX, BY, BW, BH = 32.0, 96.0, 400.0, 453.0     # portrait box, matches 06_logos.py
GRID_W, GRID_H = 300, 340
PITCH = BW / GRID_W
DOT = 0.8                                      # grid units
TRAV_DOT = 2.5                                 # banner units; travellers are thicker

N_INTRO_GROUPS = 60
N_BANDS = 94
DRIFT = 0.42
NOISE_SIGMA = 4.0

INTRO_DUR = 3.2
INTRO_SPREAD = 2.0
LOOP = 14.2
# portrait 3.0 | 1.3 | logo 2.0 | 1.3 | logo 2.0 | 1.3 | logo 2.0 | 1.3  = 14.2
STOPS = [0.0, 3.0, 4.3, 6.3, 7.6, 9.6, 10.9, 12.9, 14.2]
KT = [s / LOOP for s in STOPS]

FONT = ("ui-monospace,'SF Mono',SFMono-Regular,Menlo,Consolas,"
        "'Liberation Mono',monospace")
CW = 0.60          # monospace advance as a fraction of font-size

THEMES = {
    "dark": dict(
        page="#0A101F", win="#0C1322", panel="#0B1120", border="#1E2A44",
        grid="#141E33", text="#C9D4E8", muted="#64748B", chrome="#22D3EE",
        dots="#A78BFA", trav="#22D3EE", accent="#10B981", live="#EF4444",
        pill_fg="#04121A", title="#8195B5",
    ),
    "light": dict(
        page="#F6F7FB", win="#FFFFFF", panel="#FBFCFE", border="#D8DEEA",
        grid="#EDF1F7", text="#1F2937", muted="#6B7280", chrome="#0891B2",
        dots="#7C3AED", trav="#0891B2", accent="#059669", live="#DC2626",
        pill_fg="#FFFFFF", title="#64748B",
    ),
}

ROWS = [
    ("Subject",        "AKASH KAR"),
    ("Role",           "GenAI / Agentic Systems | Data Science | Analytics"),
    ("Origin",         "Rourkela, Odisha, India"),
    ("Education",      "B.Tech Biomedical Engg, NIT Rourkela"),
    ("Status",         "Building + Learning + Shipping"),
    ("ToolChain",      "VS Code | Claude Code | Docker | Git"),
    None,
    ("Core.Lang",      "Python | SQL | TypeScript"),
    ("Core.Agents",    "LangGraph | LangChain | MCP"),
    ("Core.Serving",   "FastAPI | Streamlit | React"),
    ("Core.Vector",    "Qdrant | Chroma | FlashRank"),
    ("Core.Infra",     "GCP Cloud Run | Docker | Terraform"),
    ("Core.Evals",     "RAGAS | LangSmith | Logfire"),
    ("Core.Guard",     "NeMo Guardrails | Portkey | Redis"),
    None,
    ("Grid.Mail",      "karakash828@gmail.com"),
    ("Grid.LinkedIn",  "/in/akash-kar-0a7a7826a"),
    ("Grid.GitHub",    "/Akashkar00"),
    ("Grid.Instagram", "/akashkar00"),
]

HANDLE = "@Akashkar00"
TITLE = "profile.sh --live"


# ---------------------------------------------------------------- utilities
def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def num(v, nd=2):
    """Compact number formatting -- this runs 20k times per layer.

    Drops the leading zero ("0.8" -> ".8"), which SVG accepts. Three characters
    per dot across two layers is roughly 120 KB on this banner.
    """
    r = round(v, nd)
    if r == int(r):
        return str(int(r))
    t = f"{r:.{nd}f}".rstrip("0").rstrip(".")
    if t.startswith("0."):
        return t[1:]
    if t.startswith("-0."):
        return "-" + t[2:]
    return t


def dot_path(cells):
    """Emit dots as one relative path run: cheaper than a rect per dot."""
    out = []
    pr = pc = 0
    first = True
    d = num(DOT)
    for r, c in cells:
        if first:
            out.append(f"M{c} {r}")
            first = False
        else:
            dc, dr = c - pc, r - pr
            sep = "" if dr < 0 else " "
            out.append(f"m{dc}{sep}{dr}")
        out.append(f"h{d}v{d}h-{d}z")
        pr, pc = r, c
    return "".join(out)


def kt_str(vals):
    return ";".join(f"{v:.5f}".rstrip("0").rstrip(".") for v in vals)


# ---------------------------------------------------------------- metrics
def evenness(labels, cells, n_groups, nx=4, ny=4):
    """Total-variation distance of each group's spatial spread from the whole.

    Scattered groups -> near the sampling floor. Groups built by spatial region
    -> large, and the intro reveals patch-by-patch instead of shimmering in.
    """
    rr = np.array([c[0] for c in cells])
    cc = np.array([c[1] for c in cells])
    bx = np.clip((cc / GRID_W * nx).astype(int), 0, nx - 1)
    by = np.clip((rr / GRID_H * ny).astype(int), 0, ny - 1)
    cell = by * nx + bx
    K = nx * ny
    overall = np.bincount(cell, minlength=K) / len(cell)
    tv = []
    for g in range(n_groups):
        m = labels == g
        if m.sum() == 0:
            continue
        p = np.bincount(cell[m], minlength=K) / m.sum()
        tv.append(0.5 * np.abs(p - overall).sum())
    return float(np.mean(tv))


def straightness(labels, cells, min_run=6):
    """Fraction of inter-group boundary edges lying on long axis-aligned runs.

    Quantising a position-linear drift produces literal square tiles; this is
    the metric that catches it. Organic grouping stays near zero.
    """
    lab = -np.ones((GRID_H, GRID_W), int)
    for (r, c), g in zip(cells, labels):
        lab[r, c] = g

    def frac(edges):
        if edges.size == 0:
            return 0.0
        total = int(edges.sum())
        if total == 0:
            return 0.0
        longrun = 0
        for line in edges:
            run = 0
            for v in line:
                if v:
                    run += 1
                else:
                    if run >= min_run:
                        longrun += run
                    run = 0
            if run >= min_run:
                longrun += run
        return longrun / total

    a, b = lab[:, :-1], lab[:, 1:]
    vert = (a != b) & (a >= 0) & (b >= 0)          # boundary between h-neighbours
    a, b = lab[:-1, :], lab[1:, :]
    horz = (a != b) & (a >= 0) & (b >= 0)
    return 0.5 * (frac(vert.T) + frac(horz))


# ---------------------------------------------------------------- grouping
def build_groups(bits, rng):
    ys, xs = np.nonzero(bits)
    cells = list(zip(ys.tolist(), xs.tolist()))
    pos = np.column_stack([xs, ys]).astype(np.float64)
    n = len(cells)

    # intro: pure random interleave, so every group covers the whole portrait
    intro = rng.integers(0, N_INTRO_GROUPS, size=n)

    # loop: drift toward the first logo's centroid, in grid units
    lp = np.load("logo_points.npz", allow_pickle=True)
    cen = lp["centroid"]
    cg = np.array([(cen[0] - BX) / PITCH, (cen[1] - BY) / PITCH])
    drift = DRIFT * (cg[None, :] - pos)

    # noise BEFORE clustering, or the clusters are a square grid
    noisy = drift + rng.normal(0.0, NOISE_SIGMA, drift.shape)
    cent, band = kmeans2(noisy, N_BANDS, minit="++", iter=40,
                         seed=int(rng.integers(1 << 30)))
    band_vec = np.zeros((N_BANDS, 2))
    for g in range(N_BANDS):
        m = band == g
        band_vec[g] = drift[m].mean(axis=0) if m.any() else 0.0

    return cells, intro, band, band_vec, n


# ---------------------------------------------------------------- svg parts
def portrait_layers(cells, intro, band, band_vec, t, rng):
    by_intro = [[] for _ in range(N_INTRO_GROUPS)]
    for cell, g in zip(cells, intro):
        by_intro[g].append(cell)
    by_band = [[] for _ in range(N_BANDS)]
    for cell, g in zip(cells, band):
        by_band[g].append(cell)

    o = []
    o.append(f'<g transform="translate({num(BX)},{num(BY)}) scale({PITCH:.6f})" '
             f'fill="{t["dots"]}" shape-rendering="crispEdges">')

    # --- intro layer: plays once, then hands over to the loop
    o.append('<g opacity="1">')
    o.append(f'<animate attributeName="opacity" from="1" to="0" dur="0.001s" '
             f'begin="{INTRO_DUR}s" fill="freeze"/>')
    order = rng.permutation(N_INTRO_GROUPS)
    for slot, g in enumerate(order):
        grp = sorted(by_intro[g])
        if not grp:
            continue
        b = slot / N_INTRO_GROUPS * INTRO_SPREAD
        o.append(f'<path opacity="0" d="{dot_path(grp)}">'
                 f'<animate attributeName="opacity" from="0" to="1" '
                 f'begin="{b:.3f}s" dur="0.85s" fill="freeze"/></path>')
    o.append('</g>')

    # --- loop layer: drift bands
    o.append('<g opacity="0">')
    o.append(f'<animate attributeName="opacity" from="0" to="1" dur="0.001s" '
             f'begin="{INTRO_DUR}s" fill="freeze"/>')
    okt = kt_str([KT[0], KT[1], KT[2], KT[7], KT[8]])
    for g in range(N_BANDS):
        grp = sorted(by_band[g])
        if not grp:
            continue
        dx, dy = band_vec[g]
        # small per-band stagger so the dissolve is not a single flat fade
        j = float(rng.uniform(-0.018, 0.018))
        k2 = min(max(KT[2] + j, KT[1] + 0.01), KT[7] - 0.01)
        vals = f"0,0;0,0;{num(dx)},{num(dy)};{num(dx)},{num(dy)};0,0"
        o.append(
            f'<g><path d="{dot_path(grp)}"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="{vals}" keyTimes="{okt}" dur="{LOOP}s" '
            f'begin="{INTRO_DUR}s" repeatCount="indefinite" calcMode="spline" '
            f'keySplines=".4 0 .2 1;.4 0 .2 1;.4 0 .2 1;.4 0 .2 1"/>'
            f'<animate attributeName="opacity" values="1;1;0;0;1" '
            f'keyTimes="{kt_str([KT[0], KT[1], k2, KT[7], KT[8]])}" '
            f'dur="{LOOP}s" begin="{INTRO_DUR}s" repeatCount="indefinite"/></g>')
    o.append('</g></g>')
    return "\n".join(o)


def traveller_layer(t):
    lp = np.load("logo_points.npz", allow_pickle=True)
    L1, L2, L3 = lp["L1"], lp["L2"], lp["L3"]
    d2, d3 = L2 - L1, L3 - L1

    pkt = kt_str([KT[0], KT[3], KT[4], KT[5], KT[6], KT[8]])
    okt = kt_str([KT[0], KT[1], KT[2], KT[7], KT[8]])
    s = num(TRAV_DOT)
    half = TRAV_DOT / 2

    o = [f'<g opacity="0" fill="{t["trav"]}" shape-rendering="crispEdges">',
         f'<animate attributeName="opacity" values="0;0;1;1;0" '
         f'keyTimes="{okt}" dur="{LOOP}s" begin="{INTRO_DUR}s" '
         f'repeatCount="indefinite"/>']
    spl = ";".join([".45 0 .15 1"] * 5)
    for i in range(len(L1)):
        x, y = round(L1[i, 0] - half, 1), round(L1[i, 1] - half, 1)
        a = f"{num(d2[i,0],1)},{num(d2[i,1],1)}"
        b = f"{num(d3[i,0],1)},{num(d3[i,1],1)}"
        vals = f"0,0;0,0;{a};{a};{b};{b}"
        o.append(
            f'<path d="M{num(x)} {num(y)}h{s}v{s}h-{s}z">'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="{vals}" keyTimes="{pkt}" dur="{LOOP}s" '
            f'begin="{INTRO_DUR}s" repeatCount="indefinite" calcMode="spline" '
            f'keySplines="{spl}"/></path>')
    o.append('</g>')
    return "\n".join(o)


def info_panel(t):
    x0, x1 = 470.0, 1148.0
    fs, hfs = 14.0, 13.0
    cw = fs * CW
    y = 128.0
    step = 23.0
    o = []

    o.append(f'<text x="{num(x0)}" y="104" font-family="{FONT}" '
             f'font-size="{num(hfs)}" fill="{t["chrome"]}" '
             f'letter-spacing="1.6">SYSTEM.INFO</text>')
    o.append(f'<path d="M{num(x0)} 112h{num(x1-x0)}" stroke="{t["border"]}" '
             f'stroke-width="1" fill="none"/>')

    for row in ROWS:
        if row is None:
            y += 11
            continue
        label, value = row
        lw = len(label) * cw
        vw = len(value) * cw
        vx = x1 - vw
        o.append(f'<text x="{num(x0)}" y="{num(y)}" font-family="{FONT}" '
                 f'font-size="{num(fs)}" fill="{t["muted"]}" '
                 f'textLength="{num(lw)}" lengthAdjust="spacingAndGlyphs">'
                 f'{esc(label)}</text>')
        o.append(f'<text x="{num(vx)}" y="{num(y)}" font-family="{FONT}" '
                 f'font-size="{num(fs)}" fill="{t["text"]}" '
                 f'textLength="{num(vw)}" lengthAdjust="spacingAndGlyphs">'
                 f'{esc(value)}</text>')

        gs, ge = x0 + lw + 9, vx - 9
        if ge > gs:
            n = int((ge - gs) // 5)
            off = (ge - gs - (n - 1) * 5) / 2 if n > 1 else 0
            seg = "".join(
                f'M{num(gs + off + i * 5)} {num(y - 4)}h1.6v1.6h-1.6z'
                for i in range(max(n, 0)))
            if seg:
                o.append(f'<path d="{seg}" fill="{t["border"]}" '
                         f'shape-rendering="crispEdges"/>')
        y += step

    # LIVE badge
    bx, by_ = x1 - 62, 92.0
    o.append(f'<rect x="{num(bx)}" y="{num(by_)}" width="62" height="18" rx="9" '
             f'fill="none" stroke="{t["live"]}" stroke-width="1"/>')
    o.append(f'<circle cx="{num(bx+11)}" cy="{num(by_+9)}" r="3.2" '
             f'fill="{t["live"]}"><animate attributeName="opacity" '
             f'values="1;0.2;1" dur="1.6s" repeatCount="indefinite"/></circle>')
    o.append(f'<text x="{num(bx+21)}" y="{num(by_+13)}" font-family="{FONT}" '
             f'font-size="12" fill="{t["live"]}" letter-spacing="1.1" '
             f'textLength="30" lengthAdjust="spacingAndGlyphs">LIVE</text>')

    # handle pill
    pw = len(HANDLE) * 14 * CW + 26
    px, py = x0, y + 8
    o.append(f'<rect x="{num(px)}" y="{num(py)}" width="{num(pw)}" height="26" '
             f'rx="13" fill="{t["accent"]}"/>')
    o.append(f'<text x="{num(px+13)}" y="{num(py+18)}" font-family="{FONT}" '
             f'font-size="14" fill="{t["pill_fg"]}" font-weight="600" '
             f'textLength="{num(len(HANDLE)*14*CW)}" '
             f'lengthAdjust="spacingAndGlyphs">{esc(HANDLE)}</text>')
    return "\n".join(o), y


def chrome(t):
    o = []
    o.append(f'<rect width="{W}" height="{H}" fill="{t["page"]}"/>')
    o.append(f'<rect x="8.5" y="8.5" width="{W-17}" height="{H-17}" rx="11" '
             f'fill="{t["win"]}" stroke="{t["border"]}" stroke-width="1"/>')
    o.append(f'<path d="M9 42h{W-18}" stroke="{t["border"]}" stroke-width="1"/>')
    for i, c in enumerate(("#FF5F57", "#FEBC2E", "#28C840")):
        o.append(f'<circle cx="{30 + i*19}" cy="25.5" r="5.5" fill="{c}"/>')
    tl = len(TITLE) * 13 * CW
    o.append(f'<text x="{num(W/2 - tl/2)}" y="30" font-family="{FONT}" '
             f'font-size="13" fill="{t["title"]}" textLength="{num(tl)}" '
             f'lengthAdjust="spacingAndGlyphs">{esc(TITLE)}</text>')

    # portrait frame + label
    o.append(f'<rect x="{num(BX-14)}" y="{num(BY-30)}" width="{num(BW+28)}" '
             f'height="{num(BH+44)}" rx="8" fill="{t["panel"]}" '
             f'stroke="{t["border"]}" stroke-width="1"/>')
    o.append(f'<text x="{num(BX)}" y="{num(BY-12)}" font-family="{FONT}" '
             f'font-size="13" fill="{t["chrome"]}" letter-spacing="1.6" '
             f'>VISUAL.MAP</text>')
    return "\n".join(o)


def build(theme_name, bits, rng):
    t = THEMES[theme_name]
    cells, intro, band, band_vec, n = build_groups(bits, rng)

    ev = evenness(intro, cells, N_INTRO_GROUPS)
    st = straightness(band, cells)
    print(f"[{theme_name}] dots={n}  intro-evenness={ev:.3f} "
          f"(lower=scattered)  band-straightness={st:.3f} (lower=organic)")
    if st > 0.10:
        print(f"  WARNING: bands look like a grid (straightness {st:.3f}) -- "
              f"raise NOISE_SIGMA")

    panel, _ = info_panel(t)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img" '
        f'aria-label="Akash Kar - GenAI, agentic systems, data science and analytics">',
        # ligature-capable monospace fonts render "--live" as an em dash
        '<style>text{font-variant-ligatures:none}</style>',
        chrome(t),
        portrait_layers(cells, intro, band, band_vec, t, rng),
        traveller_layer(t),
        panel,
        '</svg>',
    ]
    return "\n".join(parts), dict(dots=n, evenness=ev, straightness=st)


def main():
    d = np.load("bits_v6.npz")
    stats = {}
    for name, key in (("dark", "dark"), ("light", "light")):
        rng = np.random.default_rng(20260727)
        svg, s = build(name, d[key], rng)
        open(f"{name}.svg", "w").write(svg)
        kb = len(svg.encode()) / 1024
        s["kb"] = kb
        stats[name] = s
        print(f"  wrote {name}.svg  {kb:.0f} KB")
    return stats


if __name__ == "__main__":
    main()
