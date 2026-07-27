"""Phase 1, step 1: verify the source photo segments cleanly before we commit to a pipeline.

Outputs a diagnostic PNG (mask + luminance histogram by region) and prints metrics.
Nothing here writes to the final SVG -- this is the go/no-go check.
"""
import numpy as np
from PIL import Image
from scipy import ndimage

SRC = "source_portrait.png"

img = Image.open(SRC).convert("RGB")
W, H = img.size
a = np.asarray(img).astype(np.float32)
print(f"source: {W}x{H}")

# --- background estimate: sample the four corners, which on a studio-ish shot
# are all backdrop. Median over the patches resists the plant in the SE corner.
patch = 90
corners = [
    a[:patch, :patch], a[:patch, -patch:],
    a[-patch:, :patch], a[-patch:, -patch:],
]
for name, c in zip(["NW", "NE", "SW", "SE"], corners):
    print(f"  corner {name}: mean RGB {c.reshape(-1,3).mean(axis=0).round(1)}")

# SE holds the plant -> drop it from the background estimate.
bg_ref = np.median(np.concatenate([c.reshape(-1, 3) for c in corners[:3]]), axis=0)
print(f"background reference RGB: {bg_ref.round(1)}")

# --- colour distance from background
dist = np.linalg.norm(a - bg_ref[None, None, :], axis=2)
print(f"distance percentiles: "
      f"p10={np.percentile(dist,10):.1f} p50={np.percentile(dist,50):.1f} "
      f"p90={np.percentile(dist,90):.1f}")

# Otsu on the distance map to pick the threshold rather than hardcoding one.
hist, edges = np.histogram(dist, bins=256)
p = hist.astype(np.float64) / hist.sum()
omega = np.cumsum(p)
mu = np.cumsum(p * np.arange(256))
mu_t = mu[-1]
denom = omega * (1 - omega)
denom[denom == 0] = 1e-9
sigma_b = (mu_t * omega - mu) ** 2 / denom
k = int(np.argmax(sigma_b))
thr = edges[k]
print(f"otsu threshold on colour distance: {thr:.1f}")

fg = dist > thr
print(f"raw foreground coverage: {fg.mean()*100:.1f}%")

# --- clean up: close gaps, fill holes, keep the largest blob
fg = ndimage.binary_closing(fg, structure=np.ones((9, 9)))
fg = ndimage.binary_fill_holes(fg)
lab, n = ndimage.label(fg)
if n > 1:
    sizes = ndimage.sum(fg, lab, range(1, n + 1))
    print(f"components: {n}, largest {sizes.max()/fg.size*100:.1f}% "
          f"| 2nd {sorted(sizes)[-2]/fg.size*100:.2f}%")
    fg = lab == (np.argmax(sizes) + 1)
fg = ndimage.binary_opening(fg, structure=np.ones((5, 5)))
print(f"cleaned foreground coverage: {fg.mean()*100:.1f}%")

# --- where is the subject? drives the crop.
ys, xs = np.nonzero(fg)
print(f"subject bbox: x[{xs.min()}..{xs.max()}] y[{ys.min()}..{ys.max()}]")
# top of head = first row with meaningful foreground
rowsum = fg.sum(axis=1)
head_top = int(np.argmax(rowsum > 12))
print(f"head top row: {head_top}")
colsum = fg.sum(axis=0)
print(f"subject horizontal centre: {int((xs.min()+xs.max())/2)} (image centre {W//2})")

# --- luminance separation check: can we tell suit from background?
lum = a @ np.array([0.299, 0.587, 0.114])
print(f"\nluminance: background={lum[~fg].mean():.1f}  subject={lum[fg].mean():.1f}")
# sample the jacket: lower third of the subject, excluding the bright shirt
lower = fg.copy()
lower[: int(H * 0.62), :] = False
jl = lum[lower]
print(f"lower-body luminance: p10={np.percentile(jl,10):.1f} "
      f"p50={np.percentile(jl,50):.1f} p90={np.percentile(jl,90):.1f}")
dark_frac = (jl < 60).mean()
print(f"lower body below lum 60 (would vanish in dark mode): {dark_frac*100:.1f}%")

np.save("fg_mask_full.npy", fg)

# --- diagnostic image
diag = a.copy()
diag[~fg] = diag[~fg] * 0.25          # dim the background
edge = fg ^ ndimage.binary_erosion(fg, np.ones((3, 3)))
diag[edge] = [255, 0, 128]            # mark the mask boundary
Image.fromarray(diag.astype(np.uint8)).resize((W // 2, H // 2)).save("diag_mask.png")
print("\nwrote diag_mask.png, fg_mask_full.npy")
