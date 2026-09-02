"""The SPP window.

The left half is `prepare()` made visible: the picture each platform will
actually receive, and the caption it will actually publish. Nothing here
reimplements any posting logic — it drives the same publishers as the CLI.
"""

import html
import re
from pathlib import Path

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from libs import exif, lastpost
from libs.gui import theme
from libs.gui.publishing import PublishDialog
from libs.gui.widgets import DropArea, Field, SegmentedBar, label, section
from libs.gui.workers import PrepareWorker, PublishWorker
from libs.post import Post

PREVIEW_PANE = 620
PREVIEW_BOX = (578, 318)
TAG_PATTERN = re.compile(r"(#\w+)")


def escape(text):
    return html.escape(text).replace("\n", "<br>")


def with_tags(text):
    """Colour the hashtags, escaping each piece of the raw text separately.

    Escaping the whole string first would leave entities like &#x27; in it, and
    the hashtag pattern would then match the #x27 inside one and break it.
    """
    parts = []
    for chunk in TAG_PATTERN.split(text):
        if not chunk:
            continue
        if chunk.startswith("#") and len(chunk) > 1:
            parts.append('<span style="color:%s">%s</span>' % (theme.ACCENT, escape(chunk)))
        else:
            parts.append(escape(chunk))
    return "".join(parts)


def caption_html(kept, dropped):
    """The caption as posted, with whatever the platform drops struck through."""
    body = with_tags(kept)
    if dropped:
        body += '<span style="color:%s; text-decoration:line-through">%s</span>' % (
            theme.GHOST,
            escape(dropped),
        )
    return '<span style="color:%s">%s</span>' % (theme.TEXT_DIM, body)


def repolish(widget):
    """Make Qt re-read a dynamic property the stylesheet selects on."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def dot(color):
    marker = QFrame()
    marker.setFixedSize(6, 6)
    marker.setStyleSheet("background: %s; border-radius: 3px;" % color)
    return marker


class MainWindow(QMainWindow):
    def __init__(self, publishers):
        super().__init__()
        self.publishers = list(publishers)
        self.post = None
        self.images = {}
        self.pixmaps = {}
        self.metas = {}
        self.source_size = None
        self.hints = exif.ExifHints()
        self.remembered = lastpost.load()
        self._worker = None

        self.setWindowTitle("SPP — Simple Photo Poster")
        self.resize(1180, 760)
        self.setAcceptDrops(True)

        root = QWidget()
        box = QVBoxLayout(root)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(0)
        box.addWidget(self._build_chrome())

        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_drop_page())
        self.pages.addWidget(self._build_editor_page())
        box.addWidget(self.pages, 1)

        box.addWidget(self._build_footer())
        self.setCentralWidget(root)
        self._set_ready(False)

    # ------------------------------------------------------------------ build

    def _build_chrome(self):
        bar = QFrame()
        bar.setObjectName("chrome")
        bar.setFixedHeight(52)
        box = QHBoxLayout(bar)
        box.setContentsMargins(20, 0, 20, 0)
        box.setSpacing(12)

        box.addWidget(label("SPP", "wordmark"))
        divider = QFrame()
        divider.setFixedSize(1, 16)
        divider.setStyleSheet("background: #3a352f;")
        box.addWidget(divider)

        self.filename = label("Simple Photo Poster", "mono")
        self.filename.setStyleSheet("color: %s; font-size: 12px;" % theme.TEXT_DIM)
        box.addWidget(self.filename)
        box.addStretch(1)

        for publisher in self.publishers:
            reason = publisher.unavailable()
            chip = QWidget()
            row = QHBoxLayout(chip)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(6)
            row.addWidget(dot(theme.OK if reason is None else "#4a443c"))
            name = label(publisher.name, "mono")
            name.setToolTip(reason or "ready")
            row.addWidget(name)
            box.addWidget(chip)
            box.addSpacing(10)
        return bar

    def _build_drop_page(self):
        page = QWidget()
        box = QVBoxLayout(page)
        box.setAlignment(Qt.AlignCenter)
        box.setSpacing(20)

        area = DropArea()
        area.picked.connect(self.load_photo)
        box.addWidget(area, 0, Qt.AlignCenter)
        box.addWidget(
            label("Film, lab and scanner are carried over from your last post.", "hint"),
            0,
            Qt.AlignCenter,
        )
        return page

    def _build_editor_page(self):
        page = QWidget()
        box = QHBoxLayout(page)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(0)
        box.addWidget(self._build_preview())
        box.addWidget(self._build_form(), 1)
        return page

    def _build_preview(self):
        pane = QWidget()
        pane.setFixedWidth(PREVIEW_PANE)
        box = QVBoxLayout(pane)
        box.setContentsMargins(20, 18, 20, 18)
        box.setSpacing(12)

        self.tabs = SegmentedBar()
        self.tabs.set_items(
            ["%s · %s" % (p.name.capitalize(), p.image_label) for p in self.publishers]
        )
        self.tabs.changed.connect(lambda _index: self._on_tab())
        row = QHBoxLayout()
        row.addWidget(self.tabs)
        row.addStretch(1)
        box.addLayout(row)

        frame = QFrame()
        frame.setObjectName("preview")
        frame.setFixedHeight(PREVIEW_BOX[1])
        inner = QVBoxLayout(frame)
        inner.setContentsMargins(8, 8, 8, 8)
        self.image = QLabel("Preparing…")
        self.image.setAlignment(Qt.AlignCenter)
        self.image.setStyleSheet("color: %s;" % theme.FAINT)
        inner.addWidget(self.image)
        box.addWidget(frame)

        head = QHBoxLayout()
        head.addWidget(label("CAPTION AS POSTED", "label"))
        head.addStretch(1)
        self.counter = label("", "counter", over="false")
        head.addWidget(self.counter)
        box.addLayout(head)

        self.caption = QTextEdit()
        self.caption.setObjectName("caption")
        self.caption.setReadOnly(True)
        box.addWidget(self.caption, 1)

        self.warning = label("", "warn")
        box.addWidget(self.warning)

        self.meta = label("", "mono")
        box.addWidget(self.meta)
        return pane

    def _line(self, caption, fields, **kwargs):
        """A field whose edits refresh the preview."""
        widget = QLineEdit()
        widget.setPlaceholderText(kwargs.get("placeholder", ""))
        widget.textChanged.connect(self._on_edit)
        field = Field(caption, widget)
        fields.append(field)
        return field

    def _build_form(self):
        pane = QFrame()
        pane.setObjectName("formPane")
        outer = QVBoxLayout(pane)
        outer.setContentsMargins(0, 0, 0, 0)

        area = QScrollArea()
        area.setWidgetResizable(True)
        holder = QWidget()
        box = QVBoxLayout(holder)
        box.setContentsMargins(20, 18, 20, 18)
        box.setSpacing(7)

        collected = []
        self.f_title = self._line("Title", collected)
        legend = QPlainTextEdit()
        legend.setFixedHeight(52)
        legend.textChanged.connect(self._on_edit)
        self.f_legend = Field("Legend", legend)
        self.f_alt = self._line("Alt text", collected, placeholder="blank reuses the legend")
        self.f_tags = self._line("Tags", collected, placeholder="argentique portra400")

        box.addWidget(self.f_title)
        box.addWidget(self.f_legend)
        box.addWidget(self.f_alt)
        box.addWidget(self.f_tags)

        self.digital = QCheckBox("Digital")
        self.digital.setToolTip("Hide the film, lab and scanner fields")
        self.digital.toggled.connect(self._on_digital)
        box.addWidget(section("Gear", self.digital))

        self.f_camera = self._line("Camera", collected)
        self.f_lens = self._line("Lens", collected)
        self.f_film = self._line("Film", collected)
        self.f_lab = self._line("Lab", collected)
        self.f_scan = self._line("Scanner", collected)
        self.f_date = self._line("Date", collected)
        box.addWidget(self.f_camera)
        box.addWidget(self.f_lens)
        # Film and lab share a row of their own so the pair can be hidden as one.
        self.film_row = QWidget()
        film_box = QHBoxLayout(self.film_row)
        film_box.setContentsMargins(0, 0, 0, 0)
        film_box.setSpacing(10)
        film_box.addWidget(self.f_film, 1)
        film_box.addWidget(self.f_lab, 1)
        box.addWidget(self.film_row)
        # Hiding the scanner simply lets the date take the whole row.
        box.addLayout(self._pair(self.f_scan, self.f_date))

        box.addWidget(section("Place"))
        self.f_location = self._line("Location name", collected)
        self.f_lat = self._line("Lat", collected)
        self.f_lng = self._line("Lng", collected)
        self.f_usertag = self._line("Tag someone", collected, placeholder="@username")
        place = QHBoxLayout()
        place.setSpacing(10)
        place.addWidget(self.f_location, 2)
        place.addWidget(self.f_lat, 1)
        place.addWidget(self.f_lng, 1)
        box.addLayout(place)
        box.addWidget(self.f_usertag)
        box.addStretch(1)

        area.setWidget(holder)
        outer.addWidget(area)
        return pane

    def _pair(self, left, right):
        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(left, 1)
        row.addWidget(right, 1)
        return row

    def _build_footer(self):
        bar = QFrame()
        bar.setObjectName("footer")
        bar.setFixedHeight(64)
        box = QHBoxLayout(bar)
        box.setContentsMargins(20, 0, 20, 0)
        box.setSpacing(22)

        self.checks = {}
        self.counters = {}
        for publisher in self.publishers:
            # A platform whose client library is missing, or whose credentials
            # are not in .env, cannot be ticked -- and says why on hover.
            reason = publisher.unavailable()
            check = QCheckBox(publisher.name.capitalize())
            check.setChecked(reason is None)
            check.setEnabled(reason is None)
            check.setToolTip(reason or "")
            check.toggled.connect(self._on_edit)
            counter = label("", "mono")
            if reason is not None:
                counter.setText("unavailable")
                counter.setToolTip(reason)
            self.checks[publisher.name] = check
            self.counters[publisher.name] = counter

            group = QWidget()
            row = QHBoxLayout(group)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(9)
            row.addWidget(check)
            row.addWidget(counter)
            box.addWidget(group)

        box.addStretch(1)
        self.publish_button = QPushButton("Publish")
        self.publish_button.setObjectName("primary")
        self.publish_button.clicked.connect(self._publish)
        box.addWidget(self.publish_button)
        return bar

    # ----------------------------------------------------------------- photo

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile():
                self.load_photo(url.toLocalFile())
                return

    def load_photo(self, path):
        picture = Path(path)
        if not picture.is_file():
            return

        self.post = Post(filepath=picture)
        self.hints = exif.read(picture)
        self.remembered = lastpost.load()
        self.images = {}
        self.pixmaps = {}
        self.metas = {}
        try:
            with Image.open(picture) as image:
                self.source_size = image.size
        except Exception:
            self.source_size = None

        self.filename.setText(picture.name)
        self._fill_form()
        # The EXIF only proposes; the box stays the photographer's to untick.
        self.digital.setChecked(self.hints.digital)
        self.pages.setCurrentIndex(1)
        self._set_ready(True)
        self.image.setText("Preparing…")
        self.image.setPixmap(QPixmap())

        self._worker = PrepareWorker(self.publishers, self.post, self)
        self._worker.ready.connect(self._image_ready)
        self._worker.failed.connect(self._image_failed)
        self._worker.start()
        self._on_edit()

    def _fill_form(self):
        for field, value, kind in (
            (self.f_camera, self.hints.camera, "exif"),
            (self.f_lens, self.hints.lens, "exif"),
            (self.f_date, self.hints.date, "exif"),
            (self.f_lat, self.hints.lat, "exif"),
            (self.f_lng, self.hints.lng, "exif"),
            (self.f_film, self.remembered["film"], "last"),
            (self.f_lab, self.remembered["lab"], "last"),
            (self.f_scan, self.remembered["scan"], "last"),
        ):
            field.widget.setText(value)
            field.flag(kind if value else None)

    def _on_digital(self, digital):
        """A digital frame has no film, no lab and no scanner: hide all three.

        They are cleared as well as hidden -- a field nobody can see must not
        find its way into the caption.
        """
        self.film_row.setVisible(not digital)
        self.f_scan.setVisible(not digital)
        for field, remembered in (
            (self.f_film, self.remembered["film"]),
            (self.f_lab, self.remembered["lab"]),
            (self.f_scan, self.remembered["scan"]),
        ):
            if digital:
                field.widget.clear()
                field.flag(None)
            elif not field.widget.text():
                field.widget.setText(remembered)
                field.flag("last" if remembered else None)
        self._on_edit()

    def _image_ready(self, name, path):
        path = Path(path)
        self.images[name] = path
        pixmap = QPixmap(str(path))
        if not pixmap.isNull():
            self.metas[name] = self._describe(path, pixmap)
            self.pixmaps[name] = pixmap.scaled(
                PREVIEW_BOX[0] - 20,
                PREVIEW_BOX[1] - 20,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        if self.publishers[self.tabs.current()].name == name:
            self._refresh_visual()

    def _image_failed(self, name, detail):
        if self.publishers[self.tabs.current()].name == name:
            self.image.setText("Could not prepare: %s" % detail)

    # ---------------------------------------------------------------- preview

    def _sync_post(self):
        post = self.post
        post.title = self.f_title.widget.text().strip()
        post.description = self.f_legend.widget.toPlainText().strip()
        post.alt = self.f_alt.widget.text().strip()
        post.tags = self.f_tags.widget.text().strip()
        post.camera = self.f_camera.widget.text().strip()
        post.lens = self.f_lens.widget.text().strip()
        post.film = self.f_film.widget.text().strip()
        post.lab = self.f_lab.widget.text().strip()
        post.scan = self.f_scan.widget.text().strip()
        post.date = self.f_date.widget.text().strip()
        post.location = self.f_location.widget.text().strip()
        post.lat = self.f_lat.widget.text().strip()
        post.lng = self.f_lng.widget.text().strip()
        post.usertag = self.f_usertag.widget.text().strip()

    def _on_edit(self):
        """The typing path. It must never touch a file: reloading and
        rescaling the prepared picture on every keystroke is what made this
        window crawl."""
        if self.post is None:
            return
        self._sync_post()
        self._refresh_text()
        self._refresh_footer()

    def _on_tab(self):
        self._refresh_text()
        self._refresh_visual()

    def _refresh_text(self):
        if self.post is None:
            return
        publisher = self.publishers[self.tabs.current()]
        caption = self.post.caption
        kept, dropped = publisher.split_text(self.post)
        self.caption.setHtml(caption_html(kept, dropped))

        used = publisher.measure(caption)
        if publisher.limit is None:
            self.counter.setText("no limit")
            over = False
        else:
            self.counter.setText("%d / %d" % (used, publisher.limit))
            over = used > publisher.limit
        self.counter.setProperty("over", "true" if over else "false")
        repolish(self.counter)

        self.warning.setText(
            "%d over — everything after the cut is dropped." % (used - publisher.limit)
            if dropped
            else ""
        )

    def _refresh_visual(self):
        """The picture and its numbers, both prepared once per photo."""
        publisher = self.publishers[self.tabs.current()]
        pixmap = self.pixmaps.get(publisher.name)
        if pixmap is None:
            self.image.setPixmap(QPixmap())
            self.image.setText("Preparing…")
            self.meta.setText("")
            return
        self.image.setPixmap(pixmap)
        self.meta.setText(self.metas.get(publisher.name, ""))

    def _describe(self, path, pixmap):
        if self.source_size is None:
            return ""
        return "%d×%d → %d×%d · %d KB" % (
            self.source_size[0],
            self.source_size[1],
            pixmap.width(),
            pixmap.height(),
            path.stat().st_size // 1024,
        )

    def _refresh_footer(self):
        caption = self.post.caption if self.post else ""
        chosen = 0
        for publisher in self.publishers:
            counter = self.counters[publisher.name]
            check = self.checks[publisher.name]
            if not check.isEnabled():
                counter.setText("unavailable")
                continue
            if not check.isChecked():
                counter.setText("")
                continue
            chosen += 1
            if publisher.limit is None:
                counter.setText("")
                continue
            used = publisher.measure(caption)
            counter.setText("%d / %d" % (used, publisher.limit))
            counter.setStyleSheet(
                "color: %s;" % (theme.DANGER if used > publisher.limit else theme.MUTED)
            )
        self.publish_button.setText(
            "Publish to %d platform%s" % (chosen, "" if chosen == 1 else "s")
            if chosen
            else "Publish"
        )
        self.publish_button.setEnabled(bool(chosen) and self.post is not None)

    def _set_ready(self, ready):
        """Nothing can be published before a picture is in."""
        self.publish_button.setEnabled(False)
        if ready:
            self._refresh_footer()

    # --------------------------------------------------------------- publish

    def _publish(self):
        selected = [p for p in self.publishers if self.checks[p.name].isChecked()]
        if not selected or self.post is None:
            return
        self._sync_post()

        dialog = PublishDialog(selected, self.post, self.images, parent=self)
        worker = PublishWorker(selected, self.post, self.images, parent=self)
        worker.progress.connect(dialog.on_event)
        worker.finished.connect(dialog.on_finished)
        worker.start()
        dialog.exec()
