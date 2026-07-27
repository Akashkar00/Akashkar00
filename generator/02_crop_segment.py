"""Phase 1, step 2: crop to head+shoulders, then segment the backdrop.

Two changes from step 1, both driven by what the diagnostic showed:
  - crop before segmenting, so the bright wall panel on the left is out of frame
  - segment in an opponent space (lum / red-green / yellow-blue) against a fitted
    smooth background surface, so shadowed skin still separates from neutral grey
"""
import numpy as np
from PIL import Image
from scipy import ndimage

SRC = "source_portrait.png"
GRID_W, GRID_H = 300, 340
ASPECT = GRID_W / GRID_H

img = Image.open(SRC).convert("RGB")
W, H = img.size

# --- crop box, derived from the step-1 measurements (head top row 114, face centre x~552).
# Head-and-shoulders, not a tight face crop: headroom above, down to mid-chest.
y0, y1 = 55, 900
face_cx = 560
ch = y1 - y0
cw = int(round(ch * ASPECT))
x0 = face_cx - cw // 2
x1 = x0 + cw
assert 0 <= x0 and x1 <= W and y1 <= H, (x0, x1, y1)
print(f"crop box: x[{x0}..{x1}] y[{y0}..{y1}]  ({cw}x{ch}, aspect {cw/ch:.4f})")

crop = img.crop((x0, y0, x1, y1))
crop.save("crop_full.png")
a = np.asarray(crop).astype(np.float32)
ch_, cw_ = a.shape[:2]

# --- opponent channels
R, G, B = a[..., 0], a[..., 1], a[..., 2]
lum = 0.299 * R + 0.587 * G + 0.114 * B
rg = R - G
yb = 0.5 * (R + G) - B
chans = np.stack([lum, rg, yb], axis=-1)

# --- fit a smooth 2nd-order surface to the border strip (all backdrop), with
# iterative outlier rejection so the blurred plant doesn't drag the fit.
yy, xx = np.mgrid[0:ch_, 0:cw_].astype(np.float32)
yn, xn = yy / ch_, xx / cw_
basis = np.stack([np.ones_like(xn), xn, yn, xn * yn, xn ** 2, yn ** 2], axis=-1)

border = np.zeros((ch_, cw_), bool)
s = 40
border[:s, :] = border[:, :s] = border[:, -s:] = True   # top + both sides; NOT bottom (chest)

model = np.zeros_like(chans)
for c in range(3):
    sel = border.copy()
    for _ in range(4):
        A = basis[sel]
        coef, *_ = np.linalg.lstsq(A, chans[..., c][sel], rcond=None)
        fit = basis @ coef
        resid = np.abs(chans[..., c] - fit)
        keep = resid[sel] <= np.percentile(resid[sel], 80)
        idx = np.nonzero(sel)
        sel = np.zeros_like(sel)
        sel[idx[0][keep], idx[1][keep]] = True
    model[..., c] = basis @ coef

# --- weighted distance: chroma counts more than luminance, because a black suit
# and a grey wall differ in luminance while shadowed skin differs mainly in chroma.
w = np.array([1.0, 2.6, 2.0])
dist = np.sqrt((((chans - model) * w) ** 2).sum(axis=-1))

hist, edges = np.histogram(dist, bins=256)
p = hist.astype(np.float64) / hist.sum()
omega, mu = np.cumsum(p), np.cumsum(p * np.arange(256))
denom = omega * (1 - omega); denom[denom == 0] = 1e-9
thr = edges[int(np.argmax((mu[-1] * omega - mu) ** 2 / denom))]
print(f"otsu threshold: {thr:.1f}")

fg = dist > thr * 0.92          # slight loosen: recover dim jacket edges
print(f"raw coverage: {fg.mean()*100:.1f}%")

# --- morphology: close, fill, largest component, light open
fg = ndimage.binary_closing(fg, np.ones((11, 11)))
fg = ndimage.binary_fill_holes(fg)
lab, n = ndimage.label(fg)
if n > 1:
    sizes = ndimage.sum(fg, lab, range(1, n + 1))
    fg = lab == (np.argmax(sizes) + 1)
fg = ndimage.binary_opening(fg, np.ones((5, 5)))
fg = ndimage.binary_fill_holes(fg)
print(f"cleaned coverage: {fg.mean()*100:.1f}%")

ys, xs = np.nonzero(fg)
print(f"subject bbox in crop: x[{xs.min()}..{xs.max()}] y[{ys.min()}..{ys.max()}]")

np.save("mask_crop.npy", fg)
np.save("lum_crop.npy", lum)

diag = a.copy()
diag[~fg] *= 0.22
edge = fg ^ ndimage.binary_erosion(fg, np.ones((3, 3)))
diag[edge] = [255, 0, 128]
Image.fromarray(diag.astype(np.uint8)).resize((cw_ // 2, ch_ // 2)).save("diag_mask2.png")
print("wrote diag_mask2.png")
