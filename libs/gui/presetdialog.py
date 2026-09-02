"""Naming a preset, and choosing what goes into it."""

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from libs import presets
from libs.gui import theme
from libs.gui.widgets import label, rule

CAPTIONS = {
    "camera": "Camera",
    "lens": "Lens",
    "film": "Film",
    "lab": "Lab",
    "scan": "Scanner",
    "tags": "Tags",
    "location": "Location",
}


class SavePresetDialog(QDialog):
    """Everything the current post could contribute, ticked by default."""

    def __init__(self, values, existing=(), parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save as preset")
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setStyleSheet(theme.QSS)

        self._existing = {name.casefold() for name in existing}
        self._boxes = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)

        card = QFrame()
        card.setObjectName("card")
        box = QVBoxLayout(card)
        box.setContentsMargins(20, 18, 20, 16)
        box.setSpacing(8)

        title = QLabel("Save as preset")
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: %s;" % theme.TEXT)
        box.addWidget(title)

        box.addWidget(label("NAME", "label"))
        self.name = QLineEdit()
        self.name.setPlaceholderText("Leica and Portra")
        self.name.textChanged.connect(self._revalidate)
        box.addWidget(self.name)

        self.warning = label("", "warn")
        box.addWidget(self.warning)

        box.addSpacing(4)
        box.addWidget(label("WHAT IT CARRIES", "label"))
        box.addWidget(rule())

        for field in presets.FIELDS:
            value = values.get(field, "").strip()
            if not value:
                continue
            check = QCheckBox("%s — %s" % (CAPTIONS[field], value))
            check.setChecked(True)
            check.toggled.connect(self._revalidate)
            self._boxes[field] = (check, value)
            box.addWidget(check)

        box.addSpacing(10)
        buttons = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        self.save = QPushButton("Save")
        self.save.setObjectName("primary")
        self.save.clicked.connect(self.accept)
        buttons.addStretch(1)
        buttons.addWidget(cancel)
        buttons.addWidget(self.save)
        box.addLayout(buttons)

        outer.addWidget(card)
        self._revalidate()

    def _revalidate(self):
        name = self.name.text().strip()
        ticked = any(check.isChecked() for check, _ in self._boxes.values())
        self.save.setEnabled(bool(name) and ticked)
        self.warning.setText(
            "A preset of that name already exists — saving replaces it."
            if name.casefold() in self._existing
            else ""
        )

    def chosen(self):
        """(name, {field: value}) for the ticked rows."""
        return self.name.text().strip(), {
            field: value
            for field, (check, value) in self._boxes.items()
            if check.isChecked()
        }
