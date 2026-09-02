"""Turn the source artwork into the application icon.

Two things matter beyond resizing.

The camera fills barely a third of the source; cropping to the body first gives
it every pixel an icon size can offer. And below 32 pixels the whole camera
turns to mush, so the small sizes are cropped tighter still, to the two lenses
-- the part that still says "camera" when nothing else survives. Hand-tuning
the small sizes is what icon sets have always done.

    python packaging/make_icon.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "spp-source.png"

# Measured on the artwork: the body without its reflection, and the lens block.
BODY_CENTRE, BODY_SIDE = (624, 632), 1176
LENS_CENTRE, LENS_SIDE = (616, 700), 760

# Below this, the body is unreadable and the lenses take over.
DETAIL_FLOOR = 32

SIZES = (16, 24, 32, 48, 64, 128, 256)

# The README shows the icon as a piece of artwork rather than a Windows icon,
# so that copy gets the rounded corners a square .ico must not have.
README_ICON = HERE.parent / "docs" / "icon.png"
README_SIZE, README_RADIUS = 256, 52


def _square(image, centre, side):
    x, y = centre
    half = side // 2
    return image.crop((x - half, y - half, x + half, y + half))


def render(image, size):
    source = _square(image, BODY_CENTRE, BODY_SIDE)
    if size < DETAIL_FLOOR:
        source = _square(image, LENS_CENTRE, LENS_SIDE)
    small = source.resize((size, size), Image.Resampling.LANCZOS)
    if size <= 64:
        # Downsampling softens pixel art; this puts the edges back.
        small = small.filter(ImageFilter.UnsharpMask(radius=1, percent=110, threshold=2))
    return small


def main():
    image = Image.open(SOURCE).convert("RGB")
    frames = [render(image, size) for size in SIZES]

    # Pillow writes one entry per size when they are handed over as append_images.
    frames[-1].save(
        HERE / "spp.ico",
        format="ICO",
        sizes=[(size, size) for size in SIZES],
        append_images=frames[:-1],
    )
    render(image, 256).save(HERE / "spp.png")

    rounded = render(image, README_SIZE).convert("RGBA")
    mask = Image.new("L", (README_SIZE, README_SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, README_SIZE - 1, README_SIZE - 1], radius=README_RADIUS, fill=255
    )
    rounded.putalpha(mask)
    README_ICON.parent.mkdir(parents=True, exist_ok=True)
    rounded.save(README_ICON)
    print("spp.ico", (HERE / "spp.ico").stat().st_size // 1024, "KB", "-", list(SIZES))


if __name__ == "__main__":
    main()
