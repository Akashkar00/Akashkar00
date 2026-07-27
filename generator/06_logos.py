"""Phase 1: sample the three logo marks into matched point sets.

Traced from real vector paths (simple-icons), not hand-drawn. Each mark is
rasterised, filled by winding rule, then reduced to N evenly-spread points via
Lloyd relaxation so the traveller dots sit on a blue-noise-ish lattice rather
than clumping where the raster happened to be dense.

Consecutive logos are matched with optimal transport (Hungarian on squared
distance) so every traveller takes the shortest path to its next position.
Without it dots cross the frame and the morph reads as noise.
"""
import numpy as np
from matplotlib.path import Path as MplPath
from scipy.cluster.vq import kmeans2
from scipy.optimize import linear_sum_assignment
from svgelements import Path as SvgPath, SVG
import re

# --- banner geometry, shared with the SVG assembler
PORTRAIT_BOX = (32.0, 96.0, 400.0, 453.0)   # x, y, w, h in banner units
N_TRAVELLERS = 900
RASTER = 420
LOGO_FILL = 0.66          # fraction of the portrait box the mark occupies

LOGOS = ["langgraph", "modelcontextprotocol", "googlecloud"]
LABELS = ["LangGraph", "MCP", "Google Cloud"]


def load_path_d(slug):
    src = open(f"logos/{slug}.svg").read()
    ds = re.findall(r'\sd="([^"]+)"', src)
    if not ds:
        raise SystemExit(f"no path data in logos/{slug}.svg")
    return ds


def rasterise(ds, n=RASTER):
    """Fill the mark on an n x n grid using the even-odd rule.

    Even-odd, not nonzero: the Google Cloud mark's inner counter winds the same
    direction as its outer contour, so a nonzero fill floods it and the cloud
    renders as a featureless blob. The other two marks have no nested subpaths
    and are identical under either rule.
    """
    # simple-icons marks live in a 0..24 viewBox
    g = (np.arange(n) + 0.5) / n * 24.0
    gx, gy = np.meshgrid(g, g)
    pts = np.column_stack([gx.ravel(), gy.ravel()])

    acc = np.zeros((n, n), bool)
    for d in ds:
        for sub in SvgPath(d).as_subpaths():
            sp = SvgPath(sub)
            steps = int(np.clip(sp.length(error=1e-4) * 3, 60, 1400))
            xy = [(float(q.x), float(q.y))
                  for q in (sp.point(t / steps) for t in range(steps + 1))]
            if len(xy) < 3:
                continue
            verts = xy + [xy[0]]
            codes = ([MplPath.MOVETO] + [MplPath.LINETO] * (len(xy) - 1)
                     + [MplPath.CLOSEPOLY])
            acc ^= MplPath(np.asarray(verts), codes).contains_points(pts).reshape(n, n)
    return acc


def sample_points(mask, k, seed):
    """Even coverage via Lloyd relaxation over an oversampled candidate set."""
    ys, xs = np.nonzero(mask)
    if len(xs) < k * 4:
        raise SystemExit(f"mark too sparse to carry {k} dots ({len(xs)} cells)")
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(xs), size=min(len(xs), k * 40), replace=False)
    cand = np.column_stack([xs[idx], ys[idx]]).astype(np.float64)
    cand += rng.uniform(-0.5, 0.5, cand.shape)
    centers, _ = kmeans2(cand, k, minit="++", iter=28, seed=int(seed))
    return centers


def to_box(pts, mask_n):
    """Map raster coords into the portrait box, preserving aspect and centring."""
    bx, by, bw, bh = PORTRAIT_BOX
    span = min(bw, bh) * LOGO_FILL
    p = pts / mask_n                      # 0..1
    p = p - 0.5
    out = np.empty_like(p)
    out[:, 0] = bx + bw / 2 + p[:, 0] * span
    out[:, 1] = by + bh / 2 + p[:, 1] * span
    return out


def match(a, b):
    """Hungarian assignment on squared distance -> shortest total travel."""
    cost = ((a[:, None, :] - b[None, :, :]) ** 2).sum(-1)
    r, c = linear_sum_assignment(cost)
    return b[c][np.argsort(r)]


def main():
    sets, inks = [], []
    for i, slug in enumerate(LOGOS):
        mask = rasterise(load_path_d(slug))
        ink = mask.mean()
        inks.append(ink)
        pts = sample_points(mask, N_TRAVELLERS, seed=1000 + i)
        sets.append(to_box(pts, RASTER))
        print(f"{LABELS[i]:<14} ink={ink*100:5.2f}%  cells={mask.sum():6d}  "
              f"pts={len(pts)}")

    # thin marks make a sparse, wiry morph -- worth knowing before we commit
    thin = [LABELS[i] for i, v in enumerate(inks) if v < 0.10]
    if thin:
        print(f"NOTE: thin marks (<10% ink): {', '.join(thin)} "
              f"-- these read as line drawings, not solid shapes")

    # chain the matching: L1 fixed, L2 matched to L1, L3 matched to matched-L2
    L1 = sets[0]
    L2 = match(L1, sets[1])
    L3 = match(L2, sets[2])

    for name, a, b in (("L1->L2", L1, L2), ("L2->L3", L2, L3), ("L3->L1", L3, L1)):
        d = np.linalg.norm(a - b, axis=1)
        print(f"{name}: travel mean={d.mean():6.1f} p95={np.percentile(d,95):6.1f} "
              f"max={d.max():6.1f}")

    np.savez("logo_points.npz", L1=L1, L2=L2, L3=L3,
             centroid=L1.mean(axis=0), labels=np.array(LABELS))
    print(f"\nlogo1 centroid: {L1.mean(axis=0).round(1)}")
    print("wrote logo_points.npz")


if __name__ == "__main__":
    main()
