"""Launch the SPP window."""

import sys

from PySide6.QtWidgets import QApplication

from libs import publishers
from libs.gui import theme
from libs.gui.window import MainWindow


def main(argv=None):
    argv = list(sys.argv if argv is None else argv)
    app = QApplication(argv)
    app.setApplicationName("SPP")
    app.setStyleSheet(theme.QSS)

    window = MainWindow([cls() for cls in publishers.ALL])
    window.show()
    if len(argv) > 1:
        window.load_photo(argv[1])
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
