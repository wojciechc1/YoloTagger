from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QRadioButton,
    QButtonGroup,
    QDialogButtonBox,
)


class LabelTypeDialog(QDialog):
    """Dialog to select label type (rect or polygon) for the session."""

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Label Type")
        self.resize(300, 150)
        self.session = session

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Choose label type for this session:"))

        # --- Radio buttons ---
        self.rect_rb = QRadioButton("Bounding Boxes (Rectangles)")
        self.poly_rb = QRadioButton("Polygons")

        # set default selection based on session
        if self.session.label_mode == "polygon":
            self.poly_rb.setChecked(True)
        else:
            self.rect_rb.setChecked(True)

        # group buttons (only one can be selected)
        self.group = QButtonGroup(self)
        self.group.addButton(self.rect_rb)
        self.group.addButton(self.poly_rb)

        layout.addWidget(self.rect_rb)
        layout.addWidget(self.poly_rb)

        # --- OK / Cancel ---
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self):
        """Save the selection to session before closing."""
        self.session.label_mode = "polygon" if self.poly_rb.isChecked() else "rect"
        super().accept()
