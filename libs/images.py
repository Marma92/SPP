"""Preparing a picture for each platform.

Only Pillow is used here. `python-resize-image` was dropped: unmaintained since
2018 and redundant with `Image.thumbnail`. `Image.ANTIALIAS`, which the previous
version called, was removed in Pillow 10 -- the resize simply crashed on any
recent install.
"""

import datetime

from PIL import Image, ImageOps

from libs.config import INSTAGRAM_DIR, RESIZE_DIR

SUPPORTED_FORMATS = {"JPEG", "PNG", "BMP", "TIFF", "WEBP"}

TWITTER_MAX_EDGE = 2048
TWITTER_MAX_BYTES = 5 * 1024 * 1024
INSTAGRAM_SIDE = 1440

# Quality ladder walked down until a JPEG fits under the platform's size cap.
QUALITY_STEPS = (95, 90, 85, 78, 70, 60)


def _load(filepath):
    """Open a picture as RGB, with its EXIF orientation already applied."""
    with Image.open(filepath) as image:
        if image.format not in SUPPORTED_FORMATS:
            raise ValueError(
                "Unsupported image format %r (supported: %s)"
                % (image.format, ", ".join(sorted(SUPPORTED_FORMATS)))
            )
        # Without this, a portrait frame straight out of the camera is posted
        # lying on its side.
        return ImageOps.exif_transpose(image).convert("RGB")


def _fit(image, width, height):
    """Scale (up or down) so the picture fits inside width x height."""
    ratio = min(width / image.width, height / image.height)
    size = (max(1, round(image.width * ratio)), max(1, round(image.height * ratio)))
    return image.resize(size, Image.Resampling.LANCZOS)


def _target_path(directory):
    directory.mkdir(parents=True, exist_ok=True)
    return directory / (datetime.datetime.now().strftime("%Y%m%d%H%M%S%f") + ".jpeg")


def _save_jpeg(image, target, max_bytes=None):
    for quality in QUALITY_STEPS:
        image.save(target, "JPEG", quality=quality, subsampling=0, optimize=True)
        if max_bytes is None or target.stat().st_size <= max_bytes:
            break
    return target


def prepare_for_twitter(filepath):
    """Shrink to 2048px on the long edge and under the 5MB upload cap."""
    image = _load(filepath)
    if max(image.size) > TWITTER_MAX_EDGE:
        image = _fit(image, TWITTER_MAX_EDGE, TWITTER_MAX_EDGE)
    return _save_jpeg(image, _target_path(RESIZE_DIR), TWITTER_MAX_BYTES)


def prepare_for_instagram(filepath):
    """Centre the picture in a 1440x1440 white square (the white bands look)."""
    image = _fit(_load(filepath), INSTAGRAM_SIDE, INSTAGRAM_SIDE)
    canvas = Image.new("RGB", (INSTAGRAM_SIDE, INSTAGRAM_SIDE), (255, 255, 255))
    offset = ((INSTAGRAM_SIDE - image.width) // 2, (INSTAGRAM_SIDE - image.height) // 2)
    canvas.paste(image, offset)
    return _save_jpeg(canvas, _target_path(INSTAGRAM_DIR))
