from pathlib import Path

import pytest
from PIL import Image

from tools.visual.__main__ import main
from tools.visual.compare import SizeMismatch, diff, load_masks


def _img(size=(10, 10), colour=(100, 100, 100)) -> Image.Image:
    return Image.new("RGB", size, colour)


def _changed(delta: int) -> Image.Image:
    img = _img()
    img.putpixel((3, 3), (100 + delta, 100, 100))
    return img


def test_identical_no_diff():
    assert diff(_img(), _img()) == (0, 100)


def test_change_above_threshold():
    assert diff(_img(), _changed(30)) == (1, 100)


def test_change_below_threshold():
    assert diff(_img(), _changed(20)) == (0, 100)


def test_mask_excludes():
    from tools.visual.pixel import Box

    assert diff(_img(), _changed(30), masks=[Box(0, 0, 5, 5)]) == (0, 75)


def test_size_mismatch_reports():
    with pytest.raises(SizeMismatch) as err:
        diff(_img((1920, 1080)), _img((1280, 800)))
    assert "1920x1080" in str(err.value)
    assert "1280x800" in str(err.value)


def test_load_masks(tmp_path: Path):
    path = tmp_path / "masks.toml"
    path.write_text("[a]\nboxes = [[1, 2, 3, 4]]\n")
    boxes = load_masks(path, "a")
    assert [(b.x, b.y, b.w, b.h) for b in boxes] == [(1, 2, 3, 4)]
    assert load_masks(path, "missing") == []
    assert load_masks(tmp_path / "none.toml", "a") == []


def test_compare_cli_exit_codes(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    golden, same, bad, small = (tmp_path / n for n in ("g.png", "s.png", "b.png", "m.png"))
    _img().save(golden)
    _img().save(same)
    _changed(30).save(bad)
    _img((5, 5)).save(small)
    assert main(["compare", str(golden), str(same), "--name", "x"]) == 0
    assert "0/100" in capsys.readouterr().out
    assert main(["compare", str(golden), str(bad), "--name", "x"]) == 1
    assert "1/100" in capsys.readouterr().out
    assert main(["compare", str(golden), str(bad), "--name", "x", "--max-ratio", "0.5"]) == 0
    assert main(["compare", str(golden), str(small), "--name", "x"]) == 1
    assert "10x10" in capsys.readouterr().out


def test_j1_and_contact_cli(tmp_path: Path):
    white = tmp_path / "w.png"
    _img((200, 100), (255, 255, 255)).save(white)
    assert main(["j1", str(white)]) == 1
    out = tmp_path / "c.png"
    assert main(["contact", str(out), str(white), str(white)]) == 0
    assert Image.open(out).size[0] >= 400
