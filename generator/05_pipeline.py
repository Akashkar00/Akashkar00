"""Phase 1: crop -> segment -> tone -> 1-bit serpentine Floyd-Steinberg -> preview.

Tone is anchored on the face, which is the fix for both earlier failures:

  v2  white point taken from the blown shirt  -> face muddy, whole silhouette flat
  v3  global-then-ramped shadow lift          -> jacket denser than the face

Here a gamma is solved so the face's median luminance lands on --face-target.
The shirt then rolls off through a soft knee instead of setting the scale, and
the jacket gets a small spatial lift so it ghosts rather than either vanishing
or outshining the face.

Light mode anchors its white point on the backdrop itself, so the mid-grey wall
falls to near-zero density instead of covering the panel in a ~50% dot field.
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

# Face sampling window as fractions of the grid: central columns, brow-to-chin
# rows. Deliberately excludes hair, which would drag the median down.
FACE_ROWS = (0.20, 0.46)
FACE_COLS = (0.32, 0.68)


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
    """Opponent-space distance from a fitted smooth backdrop surface.

    Chroma is weighted above luminance so shadowed skin still separates from
    neutral grey; the surface fit absorbs the wall's brightness gradient.
    """
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
    return fg, lum, model[..., 0], thr


def detect_skin(a, fg):
    """Locate the face by skin chroma rather than by hardcoded grid fractions.

    Fixed-fraction windows sampled the hair on this photo, which dragged the
    "face median" down to 0.09 and drove the solved gamma into its clamp.
    Skin is reliably R > G > B with a clear red-green margin; hair, jacket and
    the neutral backdrop all fail that test.
    """
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    skin = (R > G + 10) & (G > B + 2) & (R > 55) & (R < 250) & fg
    skin = ndimage.binary_opening(skin, np.ones((7, 7)))
    skin = ndimage.binary_closing(skin, np.ones((9, 9)))
    lab, n = ndimage.label(skin)
    if n == 0:
        raise SystemExit("no skin region found -- check the segmentation mask")
    sizes = ndimage.sum(skin, lab, range(1, n + 1))
    skin = lab == (np.argmax(sizes) + 1)
    return skin


def face_window(skin_grid, mask):
    """Central core of the detected skin blob: cheeks and brow, not neck or ears."""
    ys, xs = np.nonzero(skin_grid)
    y0, y1 = ys.min(), ys.max()
    x0, x1 = xs.min(), xs.max()
    h, w = y1 - y0, x1 - x0
    fw = np.zeros_like(mask)
    fw[y0 + int(h * 0.12): y0 + int(h * 0.72),
       x0 + int(w * 0.18): x0 + int(w * 0.82)] = True
    fw &= skin_grid & mask
    print(f"  skin bbox rows[{y0}..{y1}] cols[{x0}..{x1}] "
          f"-> face window {fw.sum()} px")
    return fw


def soft_knee(x, knee, strength=0.62):
    over = x > knee
    span = 1.0 - knee
    if span > 1e-6:
        t = (x[over] - knee) / span
        x[over] = knee + span * (1.0 - (1.0 - t) ** 2) * strength
    return x


def spatial_lift(x, lift_face, lift_body, ramp):
    rows = np.arange(x.shape[0], dtype=np.float64) / x.shape[0]
    t = np.clip((rows - ramp[0]) / max(ramp[1] - ramp[0], 1e-6), 0.0, 1.0)
    t = t * t * (3 - 2 * t)
    lift = (lift_face + (lift_body - lift_face) * t)[:, None]
    return x + lift * (1.0 - x) * np.exp(-x / 0.20)


def tone_dark(L, mask, fw, args):
    """Face-anchored curve. Solves gamma so median face luminance -> face_target."""
    lo = np.percentile(L[mask], args.lo)
    hi = np.percentile(L[mask], args.hi)
    x = np.clip((L - lo) / max(hi - lo, 1e-6), 0.0, 1.0)

    fm = float(np.median(x[fw]))
    gamma = np.log(max(args.face_target, 1e-3)) / np.log(max(fm, 1e-3))
    gamma = float(np.clip(gamma, 0.25, 4.0))
    x = x ** gamma

    # local contrast about the face anchor, so modelling survives the gamma
    x = np.clip(args.face_target + (x - args.face_target) * args.gain, 0.0, 1.0)
    x = soft_knee(x, args.knee)
    x = spatial_lift(x, args.lift_face, args.lift_body, args.ramp)
    return np.clip(x, 0.0, 1.0), fm, gamma


def tone_light(L, mask, fw, bg_level, args):
    """Backdrop-anchored: wall -> ~0 density, dots draw what is darker than it."""
    white = bg_level * args.bg_white
    black = np.percentile(L[mask], args.lo)
    x = np.clip((white - L) / max(white - black, 1e-6), 0.0, 1.0)

    fm = float(np.median(x[fw]))
    gamma = np.log(max(args.face_target_light, 1e-3)) / np.log(max(fm, 1e-3))
    gamma = float(np.clip(gamma, 0.25, 4.0))
    x = x ** gamma
    x = np.clip(args.face_target_light + (x - args.face_target_light) * args.gain,
                0.0, 1.0)
    x = soft_knee(x, args.knee)
    return np.clip(x, 0.0, 1.0), fm, gamma


def fs_serpentine(L, mask=None):
    """1-bit Floyd-Steinberg, serpentine scan.

    Masked-off cells are forced dark and absorb no error, so diffusion cannot
    bleed the subject across the segmentation boundary.
    """
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


def report(name, bits, mask, fw):
    hair = mask.copy(); hair[int(GRID_H*0.22):, :] = False
    shirt = mask.copy(); shirt[:int(GRID_H*0.80), :] = False
    body = mask.copy(); body[:int(GRID_H*0.70), :] = False
    print(f"{name}: dots={bits.sum():6d}  face={bits[fw].mean()*100:5.1f}%  "
          f"hair={bits[hair].mean()*100:5.1f}%  body={bits[body].mean()*100:5.1f}%  "
          f"shirt={bits[shirt].mean()*100:5.1f}%  ink={bits.mean()*100:5.1f}%")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--y0", type=int, default=45)
    ap.add_argument("--y1", type=int, default=810)
    ap.add_argument("--cx", type=int, default=560)
    ap.add_argument("--thr-scale", type=float, default=1.0)
    ap.add_argument("--lo", type=float, default=1.5)
    ap.add_argument("--hi", type=float, default=99.0)
    ap.add_argument("--face-target", type=float, default=0.52)
    ap.add_argument("--face-target-light", type=float, default=0.42)
    ap.add_argument("--gain", type=float, default=1.30)
    ap.add_argument("--knee", type=float, default=0.74)
    ap.add_argument("--lift-face", type=float, default=0.03)
    ap.add_argument("--lift-body", type=float, default=0.16)
    ap.add_argument("--ramp", type=float, nargs=2, default=[0.55, 0.78])
    ap.add_argument("--bg-white", type=float, default=0.97)
    ap.add_argument("--sharp", type=int, default=140)
    ap.add_argument("--scale", type=int, default=2)
    ap.add_argument("--tag", default="v4")
    args = ap.parse_args()

    crop, box = build_crop("source_portrait.png", args.y0, args.y1, args.cx)
    a = np.asarray(crop).astype(np.float32)
    fg_full, lum_full, bg_model, thr = segment(a, args.thr_scale)
    print(f"crop {box} {crop.size} | otsu {thr:.1f} | mask {fg_full.mean()*100:.1f}%")

    gray = crop.convert("L").resize((GRID_W, GRID_H), Image.LANCZOS)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=3, percent=args.sharp))
    L = np.asarray(gray).astype(np.float64) / 255.0

    mask = np.asarray(Image.fromarray((fg_full * 255).astype(np.uint8))
                      .resize((GRID_W, GRID_H), Image.LANCZOS)) > 140
    mask = ndimage.binary_opening(mask, np.ones((3, 3)))
    mask = ndimage.binary_fill_holes(mask)

    skin_full = detect_skin(a, fg_full)
    skin_grid = np.asarray(Image.fromarray((skin_full * 255).astype(np.uint8))
                           .resize((GRID_W, GRID_H), Image.LANCZOS)) > 140
    fw = face_window(skin_grid, mask)

    bg_level = float(np.median(L[~mask]))
    print(f"grid mask {mask.mean()*100:.1f}% | face window {fw.sum()} px | "
          f"backdrop level {bg_level:.3f}")

    Ld, fm_d, g_d = tone_dark(L, mask, fw, args)
    bits_d = fs_serpentine(Ld, mask=mask)
    print(f"dark  face-median {fm_d:.3f} gamma {g_d:.2f}")
    report("DARK ", bits_d, mask, fw)
    render(bits_d, DOT_DARK, PANEL_BG, args.scale).save(f"prev_{args.tag}_dark.png")

    Ll, fm_l, g_l = tone_light(L, mask, fw, bg_level, args)
    bits_l = fs_serpentine(Ll, mask=None)
    print(f"light face-median {fm_l:.3f} gamma {g_l:.2f}")
    report("LIGHT", bits_l, mask, fw)
    render(bits_l, DOT_LIGHT, PAPER, args.scale).save(f"prev_{args.tag}_light.png")

    np.savez_compressed(f"bits_{args.tag}.npz", dark=bits_d, light=bits_l, mask=mask)
    print(f"wrote prev_{args.tag}_*.png bits_{args.tag}.npz")


if __name__ == "__main__":
    main()
