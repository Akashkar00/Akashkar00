# Banner generator

**These scripts and the `.npz`/`.npy` data are the source of truth — not the SVGs.**
Regenerate rather than hand-editing `assets/banner-*.svg`; the dot coordinates,
dotted leaders and animation keyTimes are all computed.

## Run

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python pillow numpy scipy svgelements matplotlib pyyaml

.venv/bin/python 05_pipeline.py --tag v6 --face-target-light 0.36 --bg-white 0.94
.venv/bin/python 06_logos.py          # ~90s: rasterises + Hungarian matching
.venv/bin/python 07_banner.py
.venv/bin/python 08_validate.py
```

Then copy `dark.svg` / `light.svg` to `../assets/banner-{dark,light}.svg`.

## Pipeline

| script | does |
|---|---|
| `01_analyze.py` | go/no-go segmentation check on the raw photo |
| `02_crop_segment.py` | crop, then backdrop segmentation in opponent colour space |
| `03_dither.py`, `04_pipeline.py` | superseded — kept for the record of what failed |
| `05_pipeline.py` | **current**: crop → segment → face-anchored tone → serpentine Floyd–Steinberg |
| `06_logos.py` | traces the three marks, samples 900 points each, matches by optimal transport |
| `07_banner.py` | assembles both SVGs |
| `08_validate.py` | SMIL structural validation |

## Things that will bite you

**Tone must be anchored on the face.** Earlier versions took the white point from
the blown-out white shirt, which pushed all facial midtones down and produced a
flat silhouette. `05_pipeline.py` locates the face by *skin chroma* (`detect_skin`)
and solves a gamma so its median lands on `--face-target`. A hardcoded grid-fraction
window sampled the hair instead and drove the solved gamma into its clamp.

**The jacket needs a spatial shadow lift.** Black suit on a `#0A101F` panel maps to
near-zero dot density and the shoulders dissolve. But a *global* lift makes the
jacket denser than the face and inverts the hierarchy. `--lift-face` / `--lift-body`
with a smoothstep ramp between them is the fix.

**Never cluster the drift directly.** Drift is a linear function of position, so
quantising it into bands mathematically recreates a square grid and the dissolve
looks blocky. `NOISE_SIGMA` perturbs each dot before clustering. `07_banner.py`
prints a straightness metric — **~0.03 is organic, >0.10 means you rebuilt the grid.**

**Two portrait layers is deliberate.** The intro reveals ~60 scattered groups; the
loop drifts ~94 spatially-coherent bands. Incompatible partitions of the same dots,
so the data is emitted twice. Merging them breaks the intro. This is most of the
file size.

**Even-odd, not nonzero.** The Google Cloud mark's inner counter winds the same way
as its outer contour, so a nonzero fill floods it into a featureless blob.

**Verify by measurement, then check in a browser.** `08_validate.py` catches the
silent SMIL failures (keySplines one short, keyTimes not ending at 1). It cannot
tell you it looks good. Headless render:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless \
  --screenshot=frame.png --window-size=1180,610 --virtual-time-budget=9000 \
  "file://$PWD/dark.svg"
```

`--virtual-time-budget` advances SMIL, so 1200 ≈ intro, 9000 ≈ first logo,
12500 ≈ third logo.

## Known: file size

`banner-dark.svg` ≈ 1.0 MB, `banner-light.svg` ≈ 1.3 MB. Light is heavier because it
keeps the backdrop and draws the *dark* parts — your hair and suit are large dark
regions, so it carries ~29.6k dots against dark mode's ~19.4k.

To trade quality for bytes: lower `--face-target-light`, or drop `GRID_W/GRID_H`
below 300×340. Fewer, larger dots is also the only real fix for the faint 1080p
moiré, which vanishes on zoom and most visitors never notice.
