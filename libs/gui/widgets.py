"""Small building blocks the window is assembled from."""

from PySide6.QtCore import QByteArray, Qt, Signal
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from libs.gui import theme

PICTURE_FILTER = "Pictures (*.jpg *.jpeg *.png *.tif *.tiff *.bmp *.webp)"

PHOTO_ICON = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
    'stroke="{stroke}" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round">'
    '<rect x="3" y="4" width="18" height="16" rx="2"/>'
    '<path d="M3 15.5 8.5 10l4.5 4.5 2.5-2.5L21 17"/>'
    '<circle cx="8.5" cy="8.5" r="1.4"/></svg>'
)


def icon_pixmap(svg, size):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    QSvgRenderer(QByteArray(svg.encode("utf-8"))).render(painter)
    painter.end()
    return pixmap


def label(text, role=None, **properties):
    widget = QLabel(text)
    if role:
        widget.setProperty("role", role)
    for name, value in properties.items():
        widget.setProperty(name, value)
    return widget


def rule():
    line = QFrame()
    line.setObjectName("rule")
    line.setFixedHeight(1)
    return line


def section(title, trailing=None):
    """A section heading, its hairline, and optionally a control on the right."""
    row = QWidget()
    box = QHBoxLayout(row)
    box.setContentsMargins(0, 6, 0, 2)
    box.setSpacing(10)
    box.addWidget(label(title.upper(), "section"))
    box.addWidget(rule(), 1)
    if trailing is not None:
        box.addWidget(trailing)
    return row


class Field(QWidget):
    """A labelled input that can say where its value came from."""

    def __init__(self, caption, widget, parent=None):
        super().__init__(parent)
        box = QVBoxLayout(self)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(4)

        self._head = QHBoxLayout()
        self._head.setContentsMargins(0, 0, 0, 0)
        self._head.setSpacing(7)
        self._head.addWidget(label(caption.upper(), "label"))
        self._head.addStretch(1)

        box.addLayout(self._head)
        box.addWidget(widget)
        self.widget = widget
        self._badge = None

    BADGES = {"exif": "exif", "last": "last post", "preset": "preset"}

    def flag(self, kind):
        """Say where the value came from, or nothing at all."""
        if self._badge is not None:
            self._head.removeWidget(self._badge)
            self._badge.deleteLater()
            self._badge = None
        if not kind:
            return
        self._badge = label(self.BADGES.get(kind, kind), "badge")
        self._badge.setProperty("kind", kind)
        self._head.insertWidget(1, self._badge)


class SegmentedBar(QWidget):
    """The platform picker sitting above the preview."""

    changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("segment")
        self.setStyleSheet("#segment { background: %s; border-radius: 7px; }" % theme.FIELD)
        self._box = QHBoxLayout(self)
        self._box.setContentsMargins(3, 3, 3, 3)
        self._box.setSpacing(3)
        self._buttons = []

    def set_items(self, captions, tooltips=()):
        for button in self._buttons:
            self._box.removeWidget(button)
            button.deleteLater()
        self._buttons = []

        for index, caption in enumerate(captions):
            button = QPushButton(caption)
            button.setProperty("role", "tab")
            if index < len(tooltips):
                button.setToolTip(tooltips[index])
            button.setCheckable(True)
            button.setChecked(index == 0)
            button.clicked.connect(lambda _=False, position=index: self.select(position))
            self._box.addWidget(button)
            self._buttons.append(button)

    def select(self, index):
        for position, button in enumerate(self._buttons):
            button.setChecked(position == index)
        self.changed.emit(index)

    def current(self):
        for index, button in enumerate(self._buttons):
            if button.isChecked():
                return index
        return 0


class DropArea(QFrame):
    """The only way into the app: a picture, dropped or picked."""

    picked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("drop")
        self.setAcceptDrops(True)
        self.setFixedSize(660, 330)

        box = QVBoxLayout(self)
        box.setSpacing(14)
        box.setAlignment(Qt.AlignCenter)

        icon = QLabel()
        icon.setPixmap(icon_pixmap(PHOTO_ICON.format(stroke="#6a6259"), 46))

        hint = label(
            "JPEG, PNG, TIFF or BMP — camera, lens and date are read from the EXIF",
            "hint",
        )
        for widget in (icon, label("Drop a photo here", "title"), hint):
            widget.setAlignment(Qt.AlignCenter)
            box.addWidget(widget)

        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse)
        box.addWidget(browse, 0, Qt.AlignCenter)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose a picture", "", PICTURE_FILTER)
        if path:
            self.picked.emit(path)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile():
                self.picked.emit(url.toLocalFile())
                return
