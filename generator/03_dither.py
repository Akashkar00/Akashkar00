"""Phase 1, step 3: 300x340 grid -> 1-bit Floyd-Steinberg, serpentine order.

Renders PNG previews only. SVG generation comes after we agree on the look.
Dark mode variants differ in shadow lift: the black jacket maps to ~zero dot
density otherwise, so the shoulders dissolve into the panel.
"""
import numpy as np
from PIL import Image, ImageOps, ImageFilter, ImageEnhance

GRID_W, GRID_H = 300, 340
PANEL_BG = (0x0A, 0x10, 0x1F)
DOT_DARK = (0xA7, 0x8B, 0xFA)
DOT_LIGHT = (0x7C, 0x3A, 0xED)
PAPER = (0xF6, 0xF7, 0xFB)


def prep(img, contrast=1.3):
    """autocontrast -> contrast -> unsharp, per the spec's numbers."""
    img = ImageOps.autocontrast(img, cutoff=1)
    img = ImageEnhance.Contrast(img).enhance(contrast)
    return img.filter(ImageFilter.UnsharpMask(radius=3, percent=140))


def shadow_lift(L, amount):
    """Raise only the low end. amount=0 is a no-op.

    Pulls deep shadows up toward `amount` while leaving midtones and highlights
    essentially untouched, so the jacket gains density without flattening the face.
    """
    if amount <= 0:
        return L
    return L + amount * (1.0 - L) * np.exp(-L / 0.22)


def fs_serpentine(L, mask=None):
    """1-bit Floyd-Steinberg with serpentine scan.

    mask: bool array; False cells are forced off and absorb no error, so
    diffusion cannot bleed the subject out across the segmented boundary.
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
            for dx, dy, k in ((step, 0, 7 / 16), (-step, 1, 3 / 16),
                              (0, 1, 5 / 16), (step, 1, 1 / 16)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    if mask is None or mask[ny, nx]:
                        buf[ny, nx] += err * k
    return out


def to_grid(gray_img, mask_full):
    g = gray_img.resize((GRID_W, GRID_H), Image.LANCZOS)
    m = Image.fromarray((mask_full * 255).astype(np.uint8)).resize(
        (GRID_W, GRID_H), Image.LANCZOS)
    return g, np.asarray(m) > 128


def render(bits, fg_rgb, bg_rgb, scale=3):
    """Preview render: one square dot per set cell, matching the SVG's crispEdges look."""
    h, w = bits.shape
    canvas = np.zeros((h * scale, w * scale, 3), np.uint8)
    canvas[:] = bg_rgb
    ys, xs = np.nonzero(bits)
    d = max(1, scale - 1)
    for y, x in zip(ys, xs):
        canvas[y * scale:y * scale + d, x * scale:x * scale + d] = fg_rgb
    return Image.fromarray(canvas)


def main():
    crop = Image.open("crop_full.png")
    mask_full = np.load("mask_crop.npy")
    gray, mask = to_grid(crop.convert("L"), mask_full)
    gray = prep(gray)
    L = np.asarray(gray).astype(np.float64) / 255.0

    results = {}

    # --- DARK: dots draw the lit subject, background segmented out.
    for name, lift in (("nolift", 0.0), ("lift", 0.30), ("lift_hi", 0.42)):
        bits = fs_serpentine(shadow_lift(L, lift), mask=mask)
        results[f"dark_{name}"] = bits
        cov = bits.sum() / mask.sum()
        low = mask.copy(); low[:int(GRID_H * 0.60), :] = False
        sh = bits[low].mean()
        print(f"dark/{name:7s}: dots={bits.sum():5d} "
              f"subject-fill={cov*100:5.1f}%  shoulder-fill={sh*100:5.1f}%")
        render(bits, DOT_DARK, PANEL_BG).save(f"prev_dark_{name}.png")

    # --- LIGHT: keep the background, dots draw the dark parts.
    Li = 1.0 - L
    bits = fs_serpentine(Li, mask=None)
    results["light"] = bits
    print(f"light      : dots={bits.sum():5d}  ink={bits.mean()*100:5.1f}%")
    render(bits, DOT_LIGHT, PAPER).save("prev_light.png")

    np.savez_compressed("dither_bits.npz", **results, mask=mask)
    print("\nwrote prev_*.png, dither_bits.npz")


if __name__ == "__main__":
    main()
