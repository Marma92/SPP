"""Signing in to Instagram inside the app, and keeping the session.

Instagram answers a first login from an unknown device with a challenge bound
to *that device*, which is why clearing it in a browser never cleared it for
the library. Hosting the login here means the browser that gets verified is
ours, and the session it earns is the one we keep — nobody has to know what a
cookie is, or open developer tools.
"""

from PySide6.QtCore import QUrl, Signal
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QDialog, QHBoxLayout, QPushButton, QVBoxLayout

from libs import config
from libs.gui import theme
from libs.gui.widgets import label

LOGIN_URL = "https://www.instagram.com/accounts/login/"
SESSION_COOKIE = "sessionid"
DOMAIN = "instagram.com"


def _text(value):
    """QNetworkCookie hands back a QByteArray for the name and the value, and
    a plain str for the domain. A QByteArray is neither bytes nor str, so
    testing for those two silently turns every cookie into its repr."""
    if isinstance(value, str):
        return value
    try:
        return bytes(value).decode("utf-8", "replace")
    except TypeError:
        return str(value)


def browser_profile(parent=None):
    """A profile that keeps what it earns, and does not announce itself."""
    profile = QWebEngineProfile("instagram", parent)
    profile.setPersistentStoragePath(str(config.WEBENGINE_DIR))
    profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
    # The default user agent carries a QtWebEngine token. Instagram has no
    # reason to be told it is talking to an embedded browser, and the token
    # only invites a different page than the one everyone else gets.
    profile.setHttpUserAgent(
        " ".join(
            word
            for word in profile.httpUserAgent().split()
            if not word.startswith("QtWebEngine/")
        )
    )
    return profile


class InstagramLoginDialog(QDialog):
    """The login page, watched for the one cookie that matters."""

    captured = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sign in to Instagram")
        self.setModal(True)
        self.resize(560, 720)
        self.setStyleSheet(theme.QSS)

        self.session_id = ""

        box = QVBoxLayout(self)
        box.setContentsMargins(14, 14, 14, 14)
        box.setSpacing(10)

        self.status = label(
            "Sign in as you would in a browser. Any verification Instagram "
            "asks for happens here.",
            "hint",
        )
        self.status.setWordWrap(True)
        box.addWidget(self.status)

        self._profile = browser_profile(self)
        self._profile.cookieStore().cookieAdded.connect(self._on_cookie)

        self.view = QWebEngineView(self)
        self.view.setPage(QWebEnginePage(self._profile, self.view))
        box.addWidget(self.view, 1)

        buttons = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        self.use = QPushButton("Use this session")
        self.use.setObjectName("primary")
        self.use.setEnabled(False)
        self.use.clicked.connect(self.accept)
        buttons.addStretch(1)
        buttons.addWidget(cancel)
        buttons.addWidget(self.use)
        box.addLayout(buttons)

        self.view.load(QUrl(LOGIN_URL))

    def _on_cookie(self, cookie):
        """Instagram only sets this one once the account is really signed in."""
        if _text(cookie.name()) != SESSION_COOKIE:
            return
        if DOMAIN not in _text(cookie.domain()):
            return

        value = _text(cookie.value())
        if not value:
            return

        self.session_id = value
        self.status.setText("Signed in — the session has been captured.")
        self.use.setEnabled(True)
        self.captured.emit(value)
