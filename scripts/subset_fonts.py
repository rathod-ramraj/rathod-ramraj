#!/usr/bin/env python3
"""
Subset source fonts using fonttools' pyftsubset for inclusion in SVG cards.

Embeds printable ASCII (U+0020-007E) plus essential UI symbols:
  - U+00B7 (· middle dot)
  - U+2019 (' right single quotation mark)
  - U+2190-2199 (← ↑ → ↓ ↔ ↕ ↖ ↗ ↘ ↙ directional arrows)
  - U+2605 (★ black star)

Outputs compact WOFF fonts into fonts/ ready for base64 embedding.
Usage:
    python scripts/subset_fonts.py
"""
import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
FONTS_DIR = os.path.join(ROOT, "fonts")

# Essential character ranges
UNICODES = "U+0020-007E,U+00B7,U+2019,U+2190-2199,U+2605"


def subset_font(in_path, out_path=None):
    if out_path is None:
        out_path = in_path

    cmd = [
        sys.executable,
        "-m",
        "fontTools.subset",
        in_path,
        f"--output-file={out_path}",
        "--flavor=woff",
        f"--unicodes={UNICODES}",
        "--layout-features=*",
        "--desubroutinize",
    ]
    print(f"Subsetting {os.path.basename(in_path)} -> {os.path.basename(out_path)}...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error subsetting {in_path}: {res.stderr}", file=sys.stderr)
    else:
        size_kb = os.path.getsize(out_path) / 1024
        print(f"  OK: {size_kb:.1f} KB")


def main():
    woff_files = glob.glob(os.path.join(FONTS_DIR, "*.woff"))
    if not woff_files:
        print("No WOFF files found in fonts/")
        return

    for font_path in sorted(woff_files):
        subset_font(font_path)


if __name__ == "__main__":
    main()

