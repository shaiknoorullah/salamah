from PIL import Image, ImageDraw

from tools.visual.pixel import Box, bbox_non_bg, check_j1, dominant

BG = (14, 19, 22)


def _bar(width: int = 200, height: int = 100) -> Image.Image:
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, width - 1, 31), fill=BG)
    draw.rectangle((10, 10, 40, 20), fill=(220, 220, 220))
    return img


def test_dominant_and_bbox():
    img = _bar()
    assert dominant(img, Box(0, 0, 200, 32)) == BG
    assert bbox_non_bg(img, Box(0, 0, 200, 32), BG) == Box(10, 10, 31, 11)
    assert bbox_non_bg(img, Box(100, 0, 100, 32), BG) is None


def test_check_j1_pass_and_fail():
    assert check_j1(_bar()) == []
    assert check_j1(Image.new("RGB", (200, 100), (255, 255, 255)))


def test_check_j1_fails_without_text():
    img = Image.new("RGB", (200, 100), BG)
    errors = check_j1(img)
    assert errors
    assert not any("colour" in e for e in errors)
