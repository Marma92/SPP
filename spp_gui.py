"""Launch the SPP window."""

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from libs import publishers
from libs.gui import theme
from libs.gui.window import MainWindow


def window_icon():
    """The icon, from the bundle when frozen and from the checkout otherwise."""
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    path = root / "packaging" / "spp.ico"
    return QIcon(str(path)) if path.exists() else QIcon()


def main(argv=None):
    argv = list(sys.argv if argv is None else argv)
    app = QApplication(argv)
    app.setApplicationName("SPP")
    app.setWindowIcon(window_icon())
    app.setStyleSheet(theme.QSS)

    window = MainWindow([cls() for cls in publishers.ALL])
    window.show()
    if len(argv) > 1:
        window.load_photo(argv[1])
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
