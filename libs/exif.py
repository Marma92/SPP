"""Reading back what the camera already recorded.

Everything here is optional and only ever used to pre-fill a prompt: a film
scan usually carries nothing at all, or the scanner's own metadata, and the
photographer stays free to overwrite whatever is proposed.
"""

import datetime
from dataclasses import dataclass

from PIL import ExifTags, Image


# What a camera records and a scanner does not. A film frame carries none of
# these; a scan that carries one is usually the scanner talking about itself,
# so two are required before calling a picture digital.
CAPTURE_TAGS = (
    ExifTags.Base.LensModel,
    ExifTags.Base.FNumber,
    ExifTags.Base.ExposureTime,
    ExifTags.Base.ISOSpeedRatings,
)


@dataclass
class ExifHints:
    camera: str = ""
    lens: str = ""
    date: str = ""
    lat: str = ""
    lng: str = ""
    digital: bool = False

    def filled(self):
        """Names of the fields that were actually found, for the summary line."""
        return [
            name
            for name, value in vars(self).items()
            if isinstance(value, str) and value
        ]


def _text(value):
    if isinstance(value, bytes):
        value = value.decode("utf-8", "replace")
    return str(value).replace("\x00", "").strip()


def _camera(ifd0):
    make = _text(ifd0.get(ExifTags.Base.Make, ""))
    model = _text(ifd0.get(ExifTags.Base.Model, ""))
    if not model:
        return make
    # "NIKON CORPORATION" + "NIKON D700" should read "NIKON D700", not both.
    brand = make.split()[0] if make else ""
    if brand and model.upper().startswith(brand.upper()):
        return model
    return ("%s %s" % (make, model)).strip()


def _lens(exif_ifd):
    lens = _text(exif_ifd.get(ExifTags.Base.LensModel, ""))
    make = _text(exif_ifd.get(ExifTags.Base.LensMake, ""))
    if lens and make and not lens.upper().startswith(make.upper()):
        return "%s %s" % (make, lens)
    return lens or make


def _date(exif_ifd, ifd0):
    raw = _text(exif_ifd.get(ExifTags.Base.DateTimeOriginal, "")) or _text(
        ifd0.get(ExifTags.Base.DateTime, "")
    )
    if not raw:
        return ""
    try:
        return datetime.datetime.strptime(raw, "%Y:%m:%d %H:%M:%S").date().isoformat()
    except ValueError:
        return raw


def _degrees(values, ref):
    """EXIF stores coordinates as degrees/minutes/seconds plus a hemisphere."""
    degrees, minutes, seconds = (float(value) for value in values)
    decimal = degrees + minutes / 60 + seconds / 3600
    if _text(ref).upper() in ("S", "W"):
        decimal = -decimal
    return "%.6f" % decimal


def _looks_digital(exif_ifd):
    """A guess, never a verdict -- the switch it sets is always overridable."""
    return sum(1 for tag in CAPTURE_TAGS if exif_ifd.get(tag) is not None) >= 2


def _coordinates(gps_ifd):
    try:
        latitude = _degrees(
            gps_ifd[ExifTags.GPS.GPSLatitude], gps_ifd[ExifTags.GPS.GPSLatitudeRef]
        )
        longitude = _degrees(
            gps_ifd[ExifTags.GPS.GPSLongitude], gps_ifd[ExifTags.GPS.GPSLongitudeRef]
        )
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return "", ""
    return latitude, longitude


def read(filepath):
    """Best-effort read; a file without EXIF simply yields empty hints."""
    try:
        with Image.open(filepath) as image:
            ifd0 = image.getexif()
            exif_ifd = ifd0.get_ifd(ExifTags.IFD.Exif)
            gps_ifd = ifd0.get_ifd(ExifTags.IFD.GPSInfo)
    except Exception:
        return ExifHints()

    latitude, longitude = _coordinates(gps_ifd)
    return ExifHints(
        camera=_camera(ifd0),
        lens=_lens(exif_ifd),
        date=_date(exif_ifd, ifd0),
        lat=latitude,
        lng=longitude,
        digital=_looks_digital(exif_ifd),
    )
