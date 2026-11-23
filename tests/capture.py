"""Render a captured test run as a PNG, for `evidence/screenshots/`.

Task: T25 (evidence).

**What this is and is not.** It renders the text that `tests/run.py --evidence`
actually captured in `evidence/run.txt`. It is a picture of a real run's
output, suitable for a portfolio or a slide, and it is nothing more than that —
the authority is `run.txt` and `results.md`, which are plain text and can be
re-run. Said plainly here so that an image is never mistaken for the proof
itself.

Requires Pillow. If Pillow is absent the evidence run still succeeds without
the image, because a missing picture must not be able to fail a test suite.

    python tests/capture.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness import ROOT, configure_stdout  # noqa: E402

RUN_TXT = ROOT / "evidence" / "run.txt"
OUT_PNG = ROOT / "evidence" / "screenshots" / "test-run.png"

BACKGROUND = (24, 26, 31)
FOREGROUND = (222, 226, 232)
PASS_COLOUR = (120, 200, 140)
FAIL_COLOUR = (235, 110, 110)
HEADING = (140, 180, 235)
MARGIN = 24
LINE_HEIGHT = 20
FONT_SIZE = 14
MAX_LINES = 70

FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    "C:/Windows/Fonts/consola.ttf",
)


def pick_lines(text, limit=MAX_LINES):
    """Reduce the run to what a reader needs at a glance.

    Drops the passing checks one by one — they are all in `results.md` — and
    keeps the per-suite totals, **every failure**, and the traceability block.
    A summary that hid failures would be marketing, so the filter removes only
    lines beginning "ok".
    """
    kept = []
    dropped = 0
    for line in text.splitlines():
        if line.strip().startswith("ok "):
            dropped += 1
            continue
        kept.append(line)
    if dropped:
        kept.append("")
        kept.append("(%d passing checks listed individually in evidence/results.md)" % dropped)
    if len(kept) > limit:
        overflow = len(kept) - limit
        kept = kept[:limit]
        kept.append("")
        kept.append("... %d further lines in evidence/run.txt" % overflow)
    return kept


def colour_for(line):
    stripped = line.strip()
    if stripped.startswith("FAIL") or "FAIL" in stripped.split(" ")[:1]:
        return FAIL_COLOUR
    if " failed" in line and "0 failed" not in line:
        return FAIL_COLOUR
    if stripped.startswith("ok "):
        return PASS_COLOUR
    if stripped.startswith(("p2p-lending", "Traceability", "unit:", "===", "---")):
        return HEADING
    return FOREGROUND


def render():
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Pillow is not installed; skipping the screenshot.", file=sys.stderr)
        return None

    if not RUN_TXT.exists():
        print("No evidence/run.txt yet — run: python tests/run.py --evidence", file=sys.stderr)
        return None

    font = None
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            font = ImageFont.truetype(candidate, FONT_SIZE)
            break
    if font is None:
        font = ImageFont.load_default()

    lines = pick_lines(RUN_TXT.read_text(encoding="utf-8"))
    width = MARGIN * 2 + max(
        (int(font.getlength(line)) for line in lines), default=400
    )
    height = MARGIN * 2 + LINE_HEIGHT * len(lines)

    image = Image.new("RGB", (max(width, 640), height), BACKGROUND)
    draw = ImageDraw.Draw(image)
    for index, line in enumerate(lines):
        draw.text(
            (MARGIN, MARGIN + index * LINE_HEIGHT),
            line,
            font=font,
            fill=colour_for(line),
        )

    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUT_PNG)
    return OUT_PNG


if __name__ == "__main__":
    configure_stdout()
    path = render()
    if path:
        print("wrote %s" % path)
