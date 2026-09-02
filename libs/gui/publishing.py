"""The dialog that runs while the post goes out."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from libs import lastpost, runner
from libs.gui import theme
from libs.gui.widgets import label, rule
from libs.gui.workers import PublishWorker


class PlatformRow(QWidget):
    """One platform's line: where it is, and where the post landed."""

    retry = Signal(str)

    def __init__(self, name, parent=None):
        super().__init__(parent)
        self._name = name
        box = QHBoxLayout(self)
        box.setContentsMargins(0, 10, 0, 10)
        box.setSpacing(12)

        self.status = QLabel("○")
        self.status.setFixedWidth(16)
        self.status.setStyleSheet("color: %s;" % theme.FAINT)

        self.name = label(name.upper(), "mono")
        self.name.setFixedWidth(80)
        self.name.setStyleSheet("color: %s; font-size: 11px;" % theme.TEXT_DIM)

        self.detail = QLabel("Waiting…")
        self.detail.setStyleSheet("color: %s; font-size: 12.5px;" % theme.MUTED)
        self.detail.setOpenExternalLinks(True)
        self.detail.setTextInteractionFlags(Qt.TextBrowserInteraction)

        self.bar = QProgressBar()
        self.bar.setRange(0, 0)  # indeterminate: an upload reports no percentage
        self.bar.setTextVisible(False)
        self.bar.setFixedWidth(150)
        self.bar.hide()

        self.retry_button = QPushButton("Retry")
        self.retry_button.clicked.connect(lambda: self.retry.emit(self._name))
        self.retry_button.hide()

        box.addWidget(self.status)
        box.addWidget(self.name)
        box.addWidget(self.detail, 1)
        box.addWidget(self.bar)
        box.addWidget(self.retry_button)

    def working(self, text):
        self.status.setText("●")
        self.status.setStyleSheet("color: %s;" % theme.ACCENT)
        self.detail.setStyleSheet("color: %s; font-size: 12.5px;" % theme.MUTED)
        self.detail.setText(text)
        self.retry_button.hide()
        self.bar.show()

    def done(self, detail):
        self.status.setText("✓")
        self.status.setStyleSheet("color: %s;" % theme.OK)
        # A retry that succeeds must not keep the red of the attempt before it.
        self.detail.setStyleSheet("color: %s; font-size: 12.5px;" % theme.TEXT_DIM)
        self.retry_button.hide()
        self.bar.hide()
        if detail.startswith("http"):
            self.detail.setText(
                '<a href="%s" style="color:%s; text-decoration:none;">%s</a>'
                % (detail, theme.ACCENT, detail)
            )
        else:
            self.detail.setText(detail)

    def failed(self, detail):
        self.status.setText("✕")
        self.status.setStyleSheet("color: %s;" % theme.DANGER)
        self.bar.hide()
        self.detail.setText(detail)
        self.detail.setStyleSheet("color: %s; font-size: 12.5px;" % theme.DANGER)
        self.retry_button.show()


class PublishDialog(QDialog):
    def __init__(self, publishers, post, images=None, dry_run=False, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Publishing")
        self.setModal(True)
        self.setMinimumWidth(540)
        self.setStyleSheet(theme.QSS)

        self._post = post
        self._dry_run = dry_run
        self._by_name = {publisher.name: publisher for publisher in publishers}
        self._images = dict(images or {})
        self._retries = []
        self._rows = {}
        self._failures = 0
        self._successes = 0
        self._total = len(publishers)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)

        card = QFrame()
        card.setObjectName("card")
        box = QVBoxLayout(card)
        box.setContentsMargins(22, 20, 22, 18)
        box.setSpacing(0)

        head = QHBoxLayout()
        title = QLabel("Publishing" + (" (dry run)" if dry_run else ""))
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: %s;" % theme.TEXT)
        self.tally = label("0 of %d done" % self._total, "mono")
        head.addWidget(title)
        head.addStretch(1)
        head.addWidget(self.tally)
        box.addLayout(head)
        box.addSpacing(10)

        for publisher in publishers:
            box.addWidget(rule())
            row = PlatformRow(publisher.name)
            row.retry.connect(self._retry)
            self._rows[publisher.name] = row
            box.addWidget(row)

        box.addWidget(rule())
        box.addSpacing(12)

        footer = QHBoxLayout()
        self.note = label("Links open in your browser.", "hint")
        self.close_button = QPushButton("Cancel")
        self.close_button.clicked.connect(self.reject)
        footer.addWidget(self.note)
        footer.addStretch(1)
        footer.addWidget(self.close_button)
        box.addLayout(footer)

        outer.addWidget(card)

    def on_event(self, event):
        row = self._rows.get(event.platform)
        if row is None:
            return
        if event.kind == runner.START:
            row.working("Preparing…")
        elif event.kind == runner.PREPARED:
            row.working("Uploading…")
        elif event.kind == runner.DONE:
            self._successes += 1
            row.done(event.detail)
        elif event.kind == runner.FAILED:
            self._failures += 1
            row.failed(event.detail)
        self.tally.setText("%d of %d done" % (self._successes, self._total))

    def _retry(self, name):
        """Run one platform again, on the picture already prepared for it."""
        publisher = self._by_name.get(name)
        if publisher is None:
            return
        self._failures = max(0, self._failures - 1)
        self._rows[name].working("Retrying…")

        worker = PublishWorker(
            [publisher], self._post, self._images, self._dry_run, self
        )
        worker.progress.connect(self.on_event)
        worker.finished.connect(self.on_finished)
        # Held onto, or the thread would be collected while it runs.
        self._retries.append(worker)
        worker.start()

    def on_finished(self):
        """Called once a worker thread has run out of platforms."""
        if not self._dry_run and self._successes:
            # Only a post that actually went out is worth carrying over.
            lastpost.save(self._post)
        self.close_button.setText("Close")
        self.note.setText(
            "%d platform(s) failed — the others went out." % self._failures
            if self._failures
            else "Links open in your browser."
        )
