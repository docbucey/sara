#!/usr/bin/env python3
"""
Standalone: raster PNG -> multi-size Windows .ico (taskbar / shortcuts).

  pip install pillow
  python tools/png_to_ico.py --input "C:\\path\\sara_desktop.png" --output "C:\\path\\sara.ico"

For a *Python* window to show this icon in the taskbar you still need either:
  - a .lnk shortcut whose icon points at this .ico, or
  - PyInstaller / pythonw + native host — the .ico file is what Windows reads.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser(description="Convert PNG to multi-resolution ICO.")
    p.add_argument("--input", "-i", required=True, type=Path, help="Source PNG (RGBA or RGB)")
    p.add_argument("--output", "-o", required=True, type=Path, help="Destination .ico path")
    p.add_argument(
        "--sizes",
        default="16,32,48,64,128,256",
        help="Comma-separated square sizes (default: 16,32,48,64,128,256)",
    )
    args = p.parse_args()

    try:
        from PIL import Image
    except ImportError:
        print("Install Pillow:  pip install pillow", file=sys.stderr)
        return 1

    src = args.input.expanduser().resolve()
    if not src.is_file():
        print(f"Not found: {src}", file=sys.stderr)
        return 1

    sizes = [int(x.strip()) for x in args.sizes.split(",") if x.strip()]
    if not sizes:
        print("No sizes parsed.", file=sys.stderr)
        return 1

    im = Image.open(src).convert("RGBA")
    frames: list[Image.Image] = []
    for s in sizes:
        frames.append(im.resize((s, s), Image.Resampling.LANCZOS))

    out = args.output.expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        out,
        format="ICO",
        sizes=[(f.width, f.height) for f in frames],
        append_images=frames[1:],
    )
    print(f"Wrote {out} ({len(frames)} sizes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
