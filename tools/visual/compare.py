"""Pixel diff of two screenshots with masks, and the mask file reader."""

import tomllib
from collections.abc import Sequence
from pathlib import Path

from PIL import Image, ImageChops

from tools.visual.pixel import Box


class SizeMismatch(ValueError):
    """The two images differ in size."""


def _size(img: Image.Image) -> str:
    return f"{img.width}x{img.height}"


def diff(
    golden: Image.Image,
    actual: Image.Image,
    *,
    threshold: float = 0.1,
    masks: Sequence[Box] = (),
) -> tuple[int, int]:
    """Return (differing, compared) pixels outside `masks`.

    A pixel differs when its largest channel change / 255 exceeds `threshold`.
    """
    if golden.size != actual.size:
        raise SizeMismatch(f"size mismatch: golden {_size(golden)}, actual {_size(actual)}")
    delta = ImageChops.difference(golden.convert("RGB"), actual.convert("RGB"))
    limit = threshold * 255
    skip = bytearray(golden.width * golden.height)
    for m in masks:
        for y in range(max(m.y, 0), min(m.y + m.h, golden.height)):
            lo = y * golden.width + max(m.x, 0)
            hi = y * golden.width + min(m.x + m.w, golden.width)
            skip[lo:hi] = b"\x01" * max(hi - lo, 0)
    differing = compared = 0
    for i, px in enumerate(delta.get_flattened_data()):
        if skip[i]:
            continue
        compared += 1
        if max(px) > limit:
            differing += 1
    return differing, compared


def load_masks(path: Path, name: str) -> list[Box]:
    """Read `[<name>] boxes = [[x, y, w, h], ...]`; a missing file or name gives []."""
    if not path.is_file():
        return []
    data = tomllib.loads(path.read_text())
    return [Box(*map(int, b)) for b in data.get(name, {}).get("boxes", [])]
