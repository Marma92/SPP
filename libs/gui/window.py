"""The SPP window.

The left half is `prepare()` made visible: the picture each platform will
actually receive, and the caption it will actually publish. Nothing here
reimplements any posting logic — it drives the same publishers as the CLI.
"""

import html
import re
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QSize, Qt, QStringListModel
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QGraphicsOpacityEffect,
    QCompleter,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QFileDialog,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from libs import exif, lastpost, presets, vocabulary
from libs.gui import theme
from libs.gui.presetdialog import SavePresetDialog
from libs.gui.settingsdialog import SettingsDialog
from libs.gui.publishing import PublishDialog
from libs.gui import logos
from libs.gui.widgets import (
    PICTURE_FILTER,
    DropArea,
    Field,
    SegmentedBar,
    ToggleSwitch,
    label,
    section,
)
from libs.gui.workers import PrepareWorker, PublishWorker
from libs.post import Post

PREVIEW_PANE = 620
PREVIEW_BOX = (578, 318)
TAG_PATTERN = re.compile(r"(#\w+)")

# How full a caption must be before its counter is worth showing.
CROWDED = 0.8


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
        self.vocabulary = vocabulary.load()
        self.completions = {}
        self.presets = presets.load()
        # A post has gone out and is still on screen. The next picture is what
        # ends it, not the publishing.
        self.published = False
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
        """The picture's name, and the way into the settings. Nothing else.

        The wordmark said what the title bar already says, and a row of status
        chips repeated what the footer now shows plainly.
        """
        bar = QFrame()
        bar.setObjectName("chrome")
        bar.setFixedHeight(52)
        box = QHBoxLayout(bar)
        box.setContentsMargins(20, 0, 20, 0)
        box.setSpacing(12)

        self.filename = label("Simple Photo Poster", "mono")
        self.filename.setStyleSheet("color: %s; font-size: 12px;" % theme.TEXT_DIM)
        box.addWidget(self.filename)

        self.change_button = QPushButton("Change…")
        self.change_button.setObjectName("quiet")
        self.change_button.setCursor(Qt.PointingHandCursor)
        self.change_button.setToolTip("Post a different picture, or fix the wrong one")
        self.change_button.clicked.connect(self._choose_photo)
        self.change_button.hide()
        box.addWidget(self.change_button)
        box.addStretch(1)

        self.settings_button = QPushButton()
        self.settings_button.setObjectName("icon")
        self.settings_button.setIcon(QIcon(logos.pixmap(logos.GEAR, 34, theme.MUTED)))
        self.settings_button.setIconSize(QSize(17, 17))
        self.settings_button.setFixedSize(30, 30)
        self.settings_button.setToolTip("Settings")
        self.settings_button.setCursor(Qt.PointingHandCursor)
        self.settings_button.clicked.connect(self._open_settings)
        box.addWidget(self.settings_button)
        return bar

    def _choose_photo(self):
        """Swap the picture without restarting: a second post, or a misclick."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose a picture", str(self.post.filepath.parent) if self.post else "",
            PICTURE_FILTER,
        )
        if path:
            self.load_photo(path)

    def _open_settings(self):
        if SettingsDialog(self).exec() == QDialog.Accepted:
            self._refresh_availability()

    def _refresh_availability(self):
        """Credentials may have just changed: ask every platform again."""
        for publisher in self.publishers:
            reason = publisher.unavailable()
            hint = reason or "Post to %s" % publisher.name.capitalize()

            switch = self.checks[publisher.name]
            became_usable = reason is None and not switch.isEnabled()
            switch.setEnabled(reason is None)
            switch.setToolTip(hint)
            self.counters[publisher.name].setToolTip(hint)
            if reason is not None:
                switch.setChecked(False)
            elif became_usable:
                # Newly configured: switch it on. One turned off on purpose
                # stays off.
                switch.setChecked(True)
        self._refresh_footer()

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
        # The name alone: what each platform receives is already spelled out in
        # the line under the preview, and five specs no longer fit across.
        self.tabs.set_items(
            [p.name.capitalize() for p in self.publishers],
            ["receives the %s" % p.image_label for p in self.publishers],
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
        head.addWidget(label("Caption as posted", "label"))
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

        # One quiet control where a full-width combo and a solid button used to
        # sit: presets are reached now and then, not on every post.
        self.preset_button = QPushButton("Presets")
        self.preset_button.setObjectName("quiet")
        self.preset_button.setCursor(Qt.PointingHandCursor)
        # Owned by the button it belongs to rather than by the window.
        self.preset_menu = QMenu(self.preset_button)
        self.preset_menu.aboutToShow.connect(self._fill_preset_menu)
        self.preset_button.setMenu(self.preset_menu)

        chooser = QHBoxLayout()
        chooser.addStretch(1)
        chooser.addWidget(self.preset_button)
        box.addLayout(chooser)

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

        self._refresh_presets()

        for key, field in (
            ("camera", self.f_camera),
            ("lens", self.f_lens),
            ("film", self.f_film),
            ("lab", self.f_lab),
            ("scan", self.f_scan),
            ("location", self.f_location),
        ):
            self._complete(key, field)

        area.setWidget(holder)
        outer.addWidget(area)
        return pane

    def _preset_fields(self):
        return {
            "camera": self.f_camera,
            "lens": self.f_lens,
            "film": self.f_film,
            "lab": self.f_lab,
            "scan": self.f_scan,
            "tags": self.f_tags,
            "location": self.f_location,
        }

    def _refresh_presets(self):
        self.presets = presets.load()

    def _fill_preset_menu(self):
        """Built when opened, so it always shows what is on disk right now."""
        self.preset_menu.clear()
        for name in self.presets:
            action = QAction(name, self.preset_menu)
            action.triggered.connect(lambda _=False, chosen=name: self._apply_preset(chosen))
            self.preset_menu.addAction(action)
        if self.presets:
            self.preset_menu.addSeparator()

        save = QAction("Save as preset…", self.preset_menu)
        save.triggered.connect(self._save_preset)
        save.setEnabled(
            self.post is not None
            and any(getattr(self.post, name, "") for name in self._preset_fields())
        )
        self.preset_menu.addAction(save)

    def _apply_preset(self, name):
        values = self.presets.get(name, {})
        if not values:
            return
        # A preset carrying a film is a film preset: bring those fields back
        # into view before writing into them.
        if any(values.get(field) for field in ("film", "lab", "scan")):
            self.digital.setChecked(False)
        for field_name, field in self._preset_fields().items():
            if values.get(field_name):
                field.widget.setText(values[field_name])
                field.flag("preset")
        self._on_edit()

    def _save_preset(self):
        self._sync_post()
        values = {
            name: getattr(self.post, name, "") for name in self._preset_fields()
        }
        dialog = SavePresetDialog(values, self.presets, self)
        if dialog.exec() != QDialog.Accepted:
            return
        name, chosen = dialog.chosen()
        presets.save(name, chosen)
        self._refresh_presets()

    def _complete(self, key, field):
        """Offer back everything already typed into this field, in any post."""
        model = QStringListModel(self.vocabulary.get(key, []), self)
        completer = QCompleter(model, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        # Contains, not starts-with: "delta" should find "Ilford Delta 100".
        completer.setFilterMode(Qt.MatchContains)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        field.widget.setCompleter(completer)
        self.completions[key] = model

    def _refresh_completions(self):
        self.vocabulary = vocabulary.load()
        for key, model in self.completions.items():
            model.setStringList(self.vocabulary.get(key, []))

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
        box.setSpacing(20)

        self.checks = {}
        self.counters = {}
        self.marks = {}
        for publisher in self.publishers:
            # A platform whose client library is missing, or whose credentials
            # are absent, cannot be switched on -- and says why on hover.
            reason = publisher.unavailable()
            hint = reason or "Post to %s" % publisher.name.capitalize()

            mark = QLabel()
            mark.setPixmap(logos.platform(publisher.name, 19, theme.TEXT_DIM))
            mark.setToolTip(hint)
            mark.setFixedWidth(19)
            # An effect rather than a second colour: it fades Flickr's blue and
            # pink along with the monochrome marks, in one rule.
            fade = QGraphicsOpacityEffect(mark)
            mark.setGraphicsEffect(fade)
            self.marks[publisher.name] = fade

            switch = ToggleSwitch()
            switch.setChecked(reason is None)
            switch.setEnabled(reason is None)
            switch.setToolTip(hint)
            switch.toggled.connect(self._on_edit)

            counter = label("", "mono")
            counter.setToolTip(hint)
            self.checks[publisher.name] = switch
            self.counters[publisher.name] = counter

            group = QWidget()
            row = QHBoxLayout(group)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(9)
            row.addWidget(mark)
            row.addWidget(switch)
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

        # A worker still preparing the previous picture would otherwise deliver
        # it into this post's images, and that is what would be uploaded.
        if self._worker is not None:
            try:
                self._worker.ready.disconnect(self._image_ready)
                self._worker.failed.disconnect(self._image_failed)
            except (RuntimeError, TypeError):
                pass

        self.post = Post(filepath=picture)
        self.hints = exif.read(picture)
        self.remembered = lastpost.load()
        self._refresh_completions()
        self._refresh_presets()
        self.images = {}
        self.pixmaps = {}
        self.metas = {}
        try:
            with Image.open(picture) as image:
                self.source_size = image.size
        except Exception:
            self.source_size = None

        self.filename.setText(picture.name)
        self.change_button.show()

        if self.published:
            # The previous frame went out and this is a different one, so its
            # title, legend and alt text belonged to it. The gear, tags and
            # place stay: the next frame is usually from the same session.
            for field in (self.f_title, self.f_legend, self.f_alt):
                field.widget.clear()
            self.published = False

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
        """Propose what the new picture knows, without erasing what you typed.

        Camera, lens, date and coordinates belong to the file, so a new file
        replaces them. Film, lab and scanner belong to the session rather than
        the frame: they are only offered into a field left empty, or the roll
        you typed by hand would vanish on the next picture.
        """
        for field, value in (
            (self.f_camera, self.hints.camera),
            (self.f_lens, self.hints.lens),
            (self.f_date, self.hints.date),
            (self.f_lat, self.hints.lat),
            (self.f_lng, self.hints.lng),
        ):
            field.widget.setText(value)
            field.flag("exif" if value else None)

        for field, value in (
            (self.f_film, self.remembered["film"]),
            (self.f_lab, self.remembered["lab"]),
            (self.f_scan, self.remembered["scan"]),
        ):
            if field.widget.text():
                continue
            field.widget.setText(value)
            field.flag("last" if value else None)

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
            self.marks[publisher.name].setOpacity(
                1.0 if check.isChecked() and check.isEnabled() else 0.32
            )
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
            over = used > publisher.limit
            # Five counters reading far below their limit are five things to
            # ignore. It speaks when the caption is close, and shouts when past.
            if not over and used < publisher.limit * CROWDED:
                counter.setText("")
                continue
            counter.setText("%d / %d" % (used, publisher.limit))
            counter.setStyleSheet(
                "color: %s;" % (theme.DANGER if over else theme.MUTED)
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
        # Whatever went out is now worth suggesting next time.
        self._refresh_completions()
        # Noted, not acted on: what was just published stays on screen to be
        # read back. Choosing the next picture is what closes the post.
        self.published = self.published or dialog.posted
