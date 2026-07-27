"""Structural validation of the generated SVGs.

SMIL fails silently: a keySplines list one entry short, or keyTimes that do not
start at 0 and end at 1, makes the browser drop the animation with no error and
no visual clue. Everything checkable without a renderer is checked here.
"""
import sys
import xml.etree.ElementTree as ET

SVG = "{http://www.w3.org/2000/svg}"


def check(path):
    errs, warns = [], []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as e:
        return [f"XML parse error: {e}"], [], {}

    counts = {"path": 0, "animate": 0, "animateTransform": 0, "text": 0}
    for el in root.iter():
        tag = el.tag.replace(SVG, "")
        if tag in counts:
            counts[tag] += 1

        if tag in ("animate", "animateTransform"):
            vals = el.get("values")
            kt = el.get("keyTimes")
            ks = el.get("keySplines")
            mode = el.get("calcMode", "linear")
            who = f"{tag}[{el.get('attributeName')}]"

            if vals is not None and kt is not None:
                nv, nk = len(vals.split(";")), len(kt.split(";"))
                if nv != nk:
                    errs.append(f"{who}: {nv} values vs {nk} keyTimes")
                ts = [float(x) for x in kt.split(";")]
                if abs(ts[0]) > 1e-9:
                    errs.append(f"{who}: keyTimes starts at {ts[0]}, must be 0")
                if abs(ts[-1] - 1.0) > 1e-9:
                    errs.append(f"{who}: keyTimes ends at {ts[-1]}, must be 1")
                if any(b < a for a, b in zip(ts, ts[1:])):
                    errs.append(f"{who}: keyTimes not monotonic: {kt}")
                if mode == "spline":
                    nsp = len(ks.split(";")) if ks else 0
                    if nsp != nk - 1:
                        errs.append(f"{who}: {nsp} keySplines, needs {nk-1}")
            elif mode == "spline" and ks:
                warns.append(f"{who}: keySplines without keyTimes")

        if tag == "text":
            if el.get("textLength") and el.get("lengthAdjust") != "spacingAndGlyphs":
                warns.append(f"text {el.text!r}: textLength without spacingAndGlyphs")

    # geometry: nothing should sit outside the canvas
    vb = [float(x) for x in root.get("viewBox").split()]
    for el in root.iter(f"{SVG}text"):
        x = float(el.get("x", 0))
        tl = float(el.get("textLength", 0))
        if x + tl > vb[2] - 4:
            errs.append(f"text {el.text!r} overflows right edge: "
                        f"{x:.0f}+{tl:.0f} > {vb[2]-4:.0f}")
        if x < vb[0] + 4:
            errs.append(f"text {el.text!r} overflows left edge at x={x:.0f}")

    return errs, warns, counts


ok = True
for f in ("dark.svg", "light.svg"):
    errs, warns, counts = check(f)
    print(f"\n=== {f} ===")
    print("  elements:", ", ".join(f"{k}={v}" for k, v in counts.items()))
    for w in warns:
        print("  WARN ", w)
    for e in errs[:20]:
        print("  ERROR", e)
    if errs:
        ok = False
        print(f"  {len(errs)} error(s)")
    else:
        print("  structure OK")

sys.exit(0 if ok else 1)
