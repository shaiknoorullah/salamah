"""Pixel helpers: dominant colour, text bounding box and the J1 bar check."""

from collections import Counter
from dataclasses import dataclass

from PIL import Image

BAR_HEIGHT = 32
BAR_BG = (14, 19, 22)
BAR_TOL = 8


@dataclass(frozen=True)
class Box:
    x: int
    y: int
    w: int
    h: int


def _clip(img: Image.Image, box: Box) -> tuple[int, int, int, int]:
    x0, y0 = max(box.x, 0), max(box.y, 0)
    return x0, y0, min(box.x + box.w, img.width), min(box.y + box.h, img.height)


def dominant(img: Image.Image, box: Box) -> tuple[int, int, int]:
    """Most common RGB colour inside `box`."""
    crop = img.convert("RGB").crop(_clip(img, box))
    counts = Counter(crop.get_flattened_data())
    if not counts:
        raise ValueError("empty box")
    return counts.most_common(1)[0][0]


def _near(pixel: tuple[int, int, int], bg: tuple[int, int, int], tol: int) -> bool:
    return all(abs(a - b) <= tol for a, b in zip(pixel, bg, strict=True))


def bbox_non_bg(img: Image.Image, box: Box, bg: tuple[int, int, int], tol: int = 8) -> Box | None:
    """Bounding box of pixels in `box` that differ from `bg` by more than `tol`."""
    x0, y0, x1, y1 = _clip(img, box)
    rgb = img.convert("RGB")
    xs: list[int] = []
    ys: list[int] = []
    for y in range(y0, y1):
        for x in range(x0, x1):
            if not _near(rgb.getpixel((x, y)), bg, tol):  # type: ignore[arg-type]
                xs.append(x)
                ys.append(y)
    if not xs:
        return None
    return Box(min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)


def check_j1(img: Image.Image) -> list[str]:
    """Check the boot-to-bar screenshot. Returns error strings; [] means pass."""
    bar = Box(0, 0, img.width, BAR_HEIGHT)
    errors: list[str] = []
    colour = dominant(img, bar)
    if not _near(colour, BAR_BG, BAR_TOL):
        errors.append(f"bar colour {colour} is not within {BAR_TOL} of {BAR_BG}")
    text = bbox_non_bg(img, bar, BAR_BG, BAR_TOL)
    if text is None:
        errors.append("no text found in the bar")
    elif text.y + text.h > BAR_HEIGHT or text.x + text.w > img.width:
        errors.append(f"text box {text} is outside the bar")
    return errors
