"""Platform marks, drawn rather than downloaded.

Flickr, Instagram and Bluesky have shapes simple enough to reproduce faithfully.
Mastodon's and Pixelfed's are approximations: they carry the silhouette, not the
official artwork. All five only have to do one job — tell five rows apart at
eighteen pixels — and the name is on every tooltip for when they do not.
"""

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

# Flickr's dots are its identity, so they keep their colours. The rest follow
# the interface, which is what makes a row of them look like one set.
MARKS = {
    "flickr": (
        '<circle cx="7.5" cy="12" r="4.6" fill="#0063DC"/>'
        '<circle cx="16.5" cy="12" r="4.6" fill="#FF0084"/>'
    ),
    "instagram": (
        '<rect x="3" y="3" width="18" height="18" rx="5.2" fill="none"'
        ' stroke="{c}" stroke-width="1.9"/>'
        '<circle cx="12" cy="12" r="4.1" fill="none" stroke="{c}" stroke-width="1.9"/>'
        '<circle cx="17.1" cy="6.9" r="1.25" fill="{c}"/>'
    ),
    "bluesky": (
        '<path d="M12 10.6C10.9 8.4 8 4.5 5.4 4.05 3.6 3.75 2.2 4.9 2.2 7.05c0 2.15'
        " 1.2 5.5 2 6.5 1 1.25 2.55 1.55 4.1 1.25-2.35.5-3.2 1.85-2.25 3.5.9 1.45"
        " 3.15 1.35 4.5-.4.75-1 1.15-1.95 1.45-2.65.3.7.7 1.65 1.45 2.65 1.35 1.75"
        " 3.6 1.85 4.5.4.95-1.65.1-3-2.25-3.5 1.55.3 3.1 0 4.1-1.25.8-1 2-4.35 2-6.5"
        ' 0-2.15-1.4-3.3-3.2-3C16 4.5 13.1 8.4 12 10.6z" fill="{c}"/>'
    ),
    "mastodon": (
        '<path d="M12 2.4c4.3 0 7.4 1.6 7.4 5.4 0 2.6.1 5.9-1 7.6-1.4 2.1-5.4 2.3-6.4'
        ' 2.3-1 0-5-.2-6.4-2.3-1.1-1.7-1-5-1-7.6 0-3.8 3.1-5.4 7.4-5.4z" fill="none"'
        ' stroke="{c}" stroke-width="1.8"/>'
        '<path d="M8.4 13.2V9.3c0-.9.7-1.5 1.5-1.5.9 0 1.4.6 1.4 1.5v1.4M12 10.7V9.3'
        'c0-.9.5-1.5 1.4-1.5.8 0 1.5.6 1.5 1.5v3.9" fill="none" stroke="{c}"'
        ' stroke-width="1.8" stroke-linecap="round"/>'
        '<path d="M9.5 19.4c1.7.5 3.6.5 5.3 0" fill="none" stroke="{c}"'
        ' stroke-width="1.8" stroke-linecap="round"/>'
    ),
    "pixelfed": (
        '<circle cx="12" cy="12" r="9.2" fill="none" stroke="{c}" stroke-width="1.8"/>'
        '<path d="M9.6 17.4V7.6h3.3c1.9 0 3.1 1.1 3.1 2.9s-1.2 3-3.1 3h-1.6"'
        ' fill="none" stroke="{c}" stroke-width="1.9" stroke-linecap="round"'
        ' stroke-linejoin="round"/>'
    ),
}

GEAR = (
    '<circle cx="12" cy="12" r="3.1" fill="none" stroke="{c}" stroke-width="1.7"/>'
    '<path d="M19.4 14a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0'
    " 0-1.8-.3 1.6 1.6 0 0 0-1 1.5V20a2 2 0 1 1-4 0v-.1A1.6 1.6 0 0 0 9 18.4a1.6 1.6 0"
    " 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.6 1.6 0 0 0 .3-1.8 1.6 1.6 0 0 0-1.5-1H3"
    "a2 2 0 1 1 0-4h.1A1.6 1.6 0 0 0 4.6 8a1.6 1.6 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8"
    "l.1.1a1.6 1.6 0 0 0 1.8.3H9a1.6 1.6 0 0 0 1-1.5V2a2 2 0 1 1 4 0v.1a1.6 1.6 0 0 0 1"
    " 1.5 1.6 1.6 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0-.3 1.8V9a1.6"
    ' 1.6 0 0 0 1.5 1H22a2 2 0 1 1 0 4h-.1a1.6 1.6 0 0 0-1.5 1z" fill="none"'
    ' stroke="{c}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>'
)

_CACHE = {}


def pixmap(body, size, colour):
    """Render one mark. Cached: the footer asks for the same five constantly."""
    key = (body, size, colour)
    if key in _CACHE:
        return _CACHE[key]

    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">%s</svg>' % (
        body.format(c=colour)
    )
    image = QPixmap(size, size)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    QSvgRenderer(QByteArray(svg.encode("utf-8"))).render(painter)
    painter.end()

    _CACHE[key] = image
    return image


def platform(name, size, colour):
    """The mark for a platform, or nothing at all for one we have no mark for."""
    body = MARKS.get(name)
    return pixmap(body, size, colour) if body else QPixmap()
