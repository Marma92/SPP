"""The screen that replaces editing a .env by hand."""

from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from libs import __version__, settings
from libs.gui import theme
from libs.gui.widgets import label, section


class SettingsDialog(QDialog):
    """Every credential the app knows about, on one scrollable sheet."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumSize(520, 560)
        self.setStyleSheet(theme.QSS)

        self._inputs = {}
        current = settings.current()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)

        card = QFrame()
        card.setObjectName("card")
        box = QVBoxLayout(card)
        box.setContentsMargins(20, 18, 20, 16)
        box.setSpacing(10)

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: %s;" % theme.TEXT)
        box.addWidget(title)
        box.addWidget(
            label(
                "Stored in your own data directory, not beside the "
                "application. SPP %s." % __version__,
                "hint",
            )
        )

        area = QScrollArea()
        area.setWidgetResizable(True)
        holder = QWidget()
        fields = QVBoxLayout(holder)
        fields.setContentsMargins(0, 8, 8, 8)
        fields.setSpacing(6)

        for heading, group in settings.GROUPS:
            fields.addWidget(section(heading))
            for name, caption, secret in group:
                fields.addWidget(label(caption.upper(), "label"))
                widget = QLineEdit(current.get(name, ""))
                if secret:
                    widget.setEchoMode(QLineEdit.Password)
                fields.addWidget(widget)
                self._inputs[name] = widget
                if name == "INSTAGRAM_SESSIONID":
                    self.sign_in = QPushButton("Sign in to Instagram…")
                    self.sign_in.setToolTip(
                        "Sign in here and the session is captured for you"
                    )
                    self.sign_in.clicked.connect(self._sign_in)
                    fields.addWidget(self.sign_in)
        fields.addStretch(1)

        area.setWidget(holder)
        box.addWidget(area, 1)

        self.reveal = QPushButton("Show secrets")
        self.reveal.setCheckable(True)
        self.reveal.toggled.connect(self._reveal)

        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        self.save = QPushButton("Save")
        self.save.setObjectName("primary")
        self.save.clicked.connect(self._save)

        buttons = QHBoxLayout()
        buttons.addWidget(self.reveal)
        buttons.addStretch(1)
        buttons.addWidget(cancel)
        buttons.addWidget(self.save)
        box.addLayout(buttons)

        outer.addWidget(card)

    def _sign_in(self):
        """Host Instagram's own login, and keep the session it hands out.

        Imported here rather than at the top: Qt WebEngine is a heavy import,
        and the rest of the screen has no use for it.
        """
        try:
            from libs.gui.instagramlogin import InstagramLoginDialog
        except ImportError as error:
            self.sign_in.setEnabled(False)
            self.sign_in.setText("Sign in unavailable — %s" % error)
            return

        dialog = InstagramLoginDialog(self)
        if dialog.exec() == QDialog.Accepted and dialog.session_id:
            self._inputs["INSTAGRAM_SESSIONID"].setText(dialog.session_id)
            # The session stands in for the password, so leave no doubt which
            # of the two is now in use.
            self._inputs["INSTAGRAM_PASSWORD"].clear()

    def _reveal(self, shown):
        for name, _label, secret in (
            field for _heading, group in settings.GROUPS for field in group
        ):
            if secret:
                self._inputs[name].setEchoMode(
                    QLineEdit.Normal if shown else QLineEdit.Password
                )
        self.reveal.setText("Hide secrets" if shown else "Show secrets")

    def values(self):
        return {name: widget.text() for name, widget in self._inputs.items()}

    def _save(self):
        settings.write(self.values())
        self.accept()
