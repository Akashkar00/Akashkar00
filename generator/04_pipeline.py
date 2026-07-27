"""Phase 1: crop -> segment -> tone -> 1-bit serpentine Floyd-Steinberg -> preview.

Single tunable pipeline so we can iterate on look without re-running four scripts.
Fixes over 03_dither.py:
  - tone statistics computed over subject pixels only (the grey backdrop was
    skewing autocontrast and washing the face out)
  - soft-knee highlight rolloff, so the blown white shirt keeps fold detail
    instead of saturating to a solid slab
  - shadow lift, so the black jacket holds a ghosted shoulder line
  - tighter crop and a stricter mask, killing the bottom-left leakage
"""
import argparse
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

GRID_W, GRID_H = 300, 340
ASPECT = GRID_W / GRID_H
PANEL_BG = (0x0A, 0x10, 0x1F)
DOT_DARK = (0xA7, 0x8B, 0xFA)
DOT_LIGHT = (0x7C, 0x3A, 0xED)
PAPER = (0xF6, 0xF7, 0xFB)


def build_crop(src, y0, y1, face_cx):
    img = Image.open(src).convert("RGB")
    W, H = img.size
    ch = y1 - y0
    cw = int(round(ch * ASPECT))
    x0 = max(0, face_cx - cw // 2)
    x1 = min(W, x0 + cw)
    x0 = x1 - cw
    assert x0 >= 0 and y1 <= H, (x0, x1, y1, W, H)
    return img.crop((x0, y0, x1, y1)), (x0, y0, x1, y1)


def segment(a, thr_scale, border_px=40):
    """Opponent-space distance from a fitted smooth backdrop surface."""
    h, w = a.shape[:2]
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    lum = 0.299 * R + 0.587 * G + 0.114 * B
    chans = np.stack([lum, R - G, 0.5 * (R + G) - B], axis=-1)

    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    yn, xn = yy / h, xx / w
    basis = np.stack([np.ones_like(xn), xn, yn, xn * yn, xn ** 2, yn ** 2], -1)

    border = np.zeros((h, w), bool)
    border[:border_px, :] = border[:, :border_px] = border[:, -border_px:] = True

    model = np.zeros_like(chans)
    for c in range(3):
        sel = border.copy()
        for _ in range(4):
            coef, *_ = np.linalg.lstsq(basis[sel], chans[..., c][sel], rcond=None)
            resid = np.abs(chans[..., c] - basis @ coef)
            keep = resid[sel] <= np.percentile(resid[sel], 80)
            iy, ix = np.nonzero(sel)
            sel = np.zeros_like(sel)
            sel[iy[keep], ix[keep]] = True
        model[..., c] = basis @ coef

    w_ = np.array([1.0, 2.6, 2.0])
    dist = np.sqrt((((chans - model) * w_) ** 2).sum(-1))

    hist, edges = np.histogram(dist, bins=256)
    p = hist.astype(np.float64) / hist.sum()
    om, mu = np.cumsum(p), np.cumsum(p * np.arange(256))
    den = om * (1 - om); den[den == 0] = 1e-9
    thr = edges[int(np.argmax((mu[-1] * om - mu) ** 2 / den))]

    fg = dist > thr * thr_scale
    fg = ndimage.binary_closing(fg, np.ones((11, 11)))
    fg = ndimage.binary_fill_holes(fg)
    lab, n = ndimage.label(fg)
    if n > 1:
        sizes = ndimage.sum(fg, lab, range(1, n + 1))
        fg = lab == (np.argmax(sizes) + 1)
    fg = ndimage.binary_opening(fg, np.ones((7, 7)))
    fg = ndimage.binary_fill_holes(fg)
    return fg, lum, thr


def tone(L, mask, lo_p, hi_p, knee, lift_face, lift_body, ramp, gain):
    """Map luminance to dot probability using subject-only statistics.

    lo_p/hi_p   percentile black/white points measured inside the mask
    knee        highlight rolloff start; above this the curve compresses so the
                shirt lands short of solid and keeps its folds
    lift_face   shadow floor over the face -- kept small, or facial modelling
                flattens into a uniform silhouette
    lift_body   shadow floor over the jacket, which is otherwise near-zero
                density and dissolves into the panel
    ramp        (top, bottom) fractions between which the lift blends
    gain        midtone contrast, applied about 0.5 where the face lives
    """
    sub = L[mask] if mask is not None else L.ravel()
    lo, hi = np.percentile(sub, lo_p), np.percentile(sub, hi_p)
    x = np.clip((L - lo) / max(hi - lo, 1e-6), 0.0, 1.0)

    # midtone contrast about 0.5
    x = np.clip(0.5 + (x - 0.5) * gain, 0.0, 1.0)

    # soft-knee highlight compression
    over = x > knee
    span = 1.0 - knee
    if span > 1e-6:
        t = (x[over] - knee) / span
        x[over] = knee + span * (1.0 - (1.0 - t) ** 2) * 0.62

    # spatial shadow lift: face keeps its contrast, jacket gains a ghost line
    h = L.shape[0]
    rows = np.arange(h, dtype=np.float64) / h
    t = np.clip((rows - ramp[0]) / max(ramp[1] - ramp[0], 1e-6), 0.0, 1.0)
    t = t * t * (3 - 2 * t)                      # smoothstep
    lift = (lift_face + (lift_body - lift_face) * t)[:, None]

    x = x + lift * (1.0 - x) * np.exp(-x / 0.20)
    return np.clip(x, 0.0, 1.0)


def fs_serpentine(L, mask=None):
    h, w = L.shape
    buf = L.astype(np.float64).copy()
    out = np.zeros((h, w), np.uint8)
    for y in range(h):
        rng = range(w) if y % 2 == 0 else range(w - 1, -1, -1)
        step = 1 if y % 2 == 0 else -1
        for x in rng:
            if mask is not None and not mask[y, x]:
                buf[y, x] = 0.0
                continue
            old = buf[y, x]
            new = 1.0 if old >= 0.5 else 0.0
            out[y, x] = new
            err = old - new
            for dx, dy, k in ((step, 0, 7/16), (-step, 1, 3/16),
                              (0, 1, 5/16), (step, 1, 1/16)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and (mask is None or mask[ny, nx]):
                    buf[ny, nx] += err * k
    return out


def render(bits, fg, bg, scale):
    h, w = bits.shape
    c = np.zeros((h * scale, w * scale, 3), np.uint8)
    c[:] = bg
    ys, xs = np.nonzero(bits)
    d = max(1, scale - 1)
    for y, x in zip(ys, xs):
        c[y*scale:y*scale+d, x*scale:x*scale+d] = fg
    return Image.fromarray(c)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--y0", type=int, default=45)
    ap.add_argument("--y1", type=int, default=810)
    ap.add_argument("--cx", type=int, default=560)
    ap.add_argument("--thr-scale", type=float, default=1.0)
    ap.add_argument("--lo", type=float, default=2.0)
    ap.add_argument("--hi", type=float, default=99.0)
    ap.add_argument("--knee", type=float, default=0.78)
    ap.add_argument("--lift-face", type=float, default=0.06)
    ap.add_argument("--lift-body", type=float, default=0.34)
    ap.add_argument("--ramp", type=float, nargs=2, default=[0.52, 0.76])
    ap.add_argument("--gain", type=float, default=1.45)
    ap.add_argument("--sharp", type=int, default=140)
    ap.add_argument("--scale", type=int, default=2)
    ap.add_argument("--tag", default="v2")
    args = ap.parse_args()

    crop, box = build_crop("source_portrait.png", args.y0, args.y1, args.cx)
    print(f"crop {box}  {crop.size}  aspect {crop.size[0]/crop.size[1]:.4f}")
    a = np.asarray(crop).astype(np.float32)

    fg_full, _, thr = segment(a, args.thr_scale)
    print(f"otsu thr {thr:.1f} | mask coverage {fg_full.mean()*100:.1f}%")

    # downsample to the dot grid
    gray = crop.convert("L").resize((GRID_W, GRID_H), Image.LANCZOS)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=3, percent=args.sharp))
    L = np.asarray(gray).astype(np.float64) / 255.0
    mask = np.asarray(Image.fromarray((fg_full * 255).astype(np.uint8))
                      .resize((GRID_W, GRID_H), Image.LANCZOS)) > 140
    mask = ndimage.binary_opening(mask, np.ones((3, 3)))
    mask = ndimage.binary_fill_holes(mask)
    print(f"grid mask coverage {mask.mean()*100:.1f}%")

    # --- dark
    Ld = tone(L, mask, args.lo, args.hi, args.knee,
              args.lift_face, args.lift_body, args.ramp, args.gain)
    bits_d = fs_serpentine(Ld, mask=mask)
    face = mask.copy(); face[int(GRID_H*0.52):, :] = False
    shoulder = mask.copy(); shoulder[:int(GRID_H*0.72), :] = False
    print(f"DARK dots={bits_d.sum():5d} subject-fill={bits_d.sum()/mask.sum()*100:5.1f}% "
          f"face={bits_d[face].mean()*100:5.1f}% shoulder={bits_d[shoulder].mean()*100:5.1f}%")
    render(bits_d, DOT_DARK, PANEL_BG, args.scale).save(f"prev_{args.tag}_dark.png")

    # --- light: keep the backdrop, dots draw the dark parts
    Ll = tone(1.0 - L, None, args.lo, args.hi, args.knee,
              args.lift_face * 0.5, args.lift_face * 0.5, args.ramp, args.gain)
    bits_l = fs_serpentine(Ll, mask=None)
    print(f"LIGHT dots={bits_l.sum():5d} ink={bits_l.mean()*100:5.1f}%")
    render(bits_l, DOT_LIGHT, PAPER, args.scale).save(f"prev_{args.tag}_light.png")

    np.savez_compressed(f"bits_{args.tag}.npz", dark=bits_d, light=bits_l, mask=mask)
    print(f"wrote prev_{args.tag}_*.png bits_{args.tag}.npz")


if __name__ == "__main__":
    main()
