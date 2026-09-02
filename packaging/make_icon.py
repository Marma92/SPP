"""Draw the application icon.

A lens ring in the accent colour on the window's own background: legible at
16 pixels, where anything with lettering or fine stripes turns to mush.
"""

from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 512
BACKGROUND = (30, 28, 26, 255)
ACCENT = (227, 162, 74, 255)
SIZES = [(n, n) for n in (16, 24, 32, 48, 64, 128, 256)]


def draw():
    image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    pen = ImageDraw.Draw(image)

    pen.rounded_rectangle([0, 0, SIZE - 1, SIZE - 1], radius=96, fill=BACKGROUND)

    margin, thickness = 104, 46
    pen.ellipse(
        [margin, margin, SIZE - margin, SIZE - margin], outline=ACCENT, width=thickness
    )

    # An off-centre highlight, so the ring reads as a lens rather than an O.
    dot = 54
    centre = SIZE // 2
    pen.ellipse(
        [centre - dot, centre - dot - 26, centre + dot, centre + dot - 26], fill=ACCENT
    )
    return image


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    icon = draw()
    icon.save(here / "spp.ico", sizes=SIZES)
    icon.resize((256, 256), Image.Resampling.LANCZOS).save(here / "spp.png")
    print("spp.ico", (here / "spp.ico").stat().st_size // 1024, "KB")
