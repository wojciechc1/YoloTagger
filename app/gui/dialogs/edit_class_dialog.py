from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QColorDialog,
    QLabel,
    QDialogButtonBox,
)
from PyQt5.QtGui import QColor
from typing import Tuple


class EditClassDialog(QDialog):
    """Dialog to edit class name and color."""

    def __init__(self, class_name: str, class_color: str = "#FF0000", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Class")
        self.new_color = QColor(class_color)

        layout = QVBoxLayout(self)

        # --- Name input ---
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("Class name:"))
        self.name_edit = QLineEdit(class_name)
        h_layout.addWidget(self.name_edit)
        layout.addLayout(h_layout)

        # --- Color selection ---
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Class color:"))
        self.color_button = QPushButton()
        self.update_color_button()
        self.color_button.clicked.connect(self.select_color)
        color_layout.addWidget(self.color_button)
        layout.addLayout(color_layout)

        # --- OK / Cancel buttons ---
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # --- Update button background to current color ---
    def update_color_button(self) -> None:
        self.color_button.setStyleSheet(f"background-color: {self.new_color.name()};")

    # --- Open color picker dialog ---
    def select_color(self) -> None:
        color = QColorDialog.getColor(self.new_color, self, "Select Class Color")
        if color.isValid():
            self.new_color = color
            self.update_color_button()

    # --- Return current values ---
    def get_values(self) -> Tuple[str, str]:
        return self.name_edit.text(), self.new_color.name()
