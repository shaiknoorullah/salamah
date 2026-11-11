"""CLI: `j1 PNG`, `compare GOLDEN ACTUAL --name N`, `contact OUT PNG...`."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from PIL import Image

from tools.visual.compare import SizeMismatch, diff, load_masks
from tools.visual.pixel import check_j1


def _j1(args: argparse.Namespace) -> int:
    errors = check_j1(Image.open(args.png))
    for e in errors:
        print(f"{args.png}: {e}")
    return 1 if errors else 0


def _compare(args: argparse.Namespace) -> int:
    masks = load_masks(Path(args.masks), args.name)
    try:
        differing, compared = diff(Image.open(args.golden), Image.open(args.actual), masks=masks)
    except SizeMismatch as err:
        print(err)
        return 1
    ratio = differing / compared if compared else 0.0
    print(f"{differing}/{compared} pixels differ, ratio {ratio:.6f}")
    return 1 if ratio > args.max_ratio else 0


def _contact(args: argparse.Namespace) -> int:
    imgs = [Image.open(p).convert("RGB") for p in args.pngs]
    sheet = Image.new("RGB", (sum(i.width for i in imgs), max(i.height for i in imgs)))
    x = 0
    for img in imgs:
        sheet.paste(img, (x, 0))
        x += img.width
    sheet.save(args.out)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools.visual")
    sub = parser.add_subparsers(dest="cmd", required=True)
    j1 = sub.add_parser("j1")
    j1.add_argument("png")
    j1.set_defaults(func=_j1)
    cmp = sub.add_parser("compare")
    cmp.add_argument("golden")
    cmp.add_argument("actual")
    cmp.add_argument("--name", required=True)
    cmp.add_argument("--max-ratio", type=float, default=0.001)
    cmp.add_argument("--masks", default="tests/visual/masks.toml")
    cmp.set_defaults(func=_compare)
    contact = sub.add_parser("contact")
    contact.add_argument("out")
    contact.add_argument("pngs", nargs="+")
    contact.set_defaults(func=_contact)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
