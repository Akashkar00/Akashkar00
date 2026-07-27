#!/usr/bin/env python3
"""Assemble README.md from the fragments in parts/.

Edit the fragments, not README.md -- this script overwrites it. Keeping the
sections separate means the banner, stats, snake and badges can each be
regenerated without hand-merging a single large file.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent
PARTS = ROOT / "parts"

USER = "Akashkar00"

SNAKE = f"""### Contribution graph

<picture>
  <source media="(prefers-color-scheme: dark)"
          srcset="https://raw.githubusercontent.com/{USER}/{USER}/output/snake-dark.svg">
  <source media="(prefers-color-scheme: light)"
          srcset="https://raw.githubusercontent.com/{USER}/{USER}/output/snake-light.svg">
  <img alt="Contribution snake"
       src="https://raw.githubusercontent.com/{USER}/{USER}/output/snake-dark.svg" width="100%">
</picture>

<!-- These resolve only after the "Generate Snake" workflow has run green once:
     the `output` branch does not exist until then. -->
"""

ORDER = [
    ("body.md", None),
    (None, "### Stats"),
    ("stats.md", None),
    (None, SNAKE),
    (None, "### Find me"),
    ("badges.md", None),
]


def main():
    missing = [n for n, _ in ORDER if n and not (PARTS / n).exists()]
    if missing:
        sys.exit(f"missing fragments: {', '.join(missing)}")

    out = []
    for name, literal in ORDER:
        out.append((PARTS / name).read_text().strip() if name else literal.strip())

    text = "\n\n".join(out) + "\n"
    (ROOT / "README.md").write_text(text)

    n = len(text)
    print(f"wrote README.md  {n} chars, {text.count(chr(10))+1} lines")
    if "YOUR-INSTANCE" in text:
        print("REMINDER: README still contains YOUR-INSTANCE -- substitute your "
              "Vercel domain before the stats cards will render.")


if __name__ == "__main__":
    main()
