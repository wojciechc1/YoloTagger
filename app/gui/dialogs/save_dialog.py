from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QButtonGroup,
    QFileDialog,
    QDialogButtonBox,
)
from typing import Any, Optional


class SaveDialog(QDialog):
    """Dialog for selecting label save options (format + folder)."""

    def __init__(self, session: Any, parent: Optional[QDialog] = None) -> None:
        """
        session: object containing info about label mode, e.g., session.label_mode = "rect" / "polygon"
        """
        super().__init__(parent)
        self.setWindowTitle("Save Options")
        self.resize(400, 200)
        self.save_path = ""

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select format to save:"))

        # --- Format selection ---
        self.raw_rb = QRadioButton("Raw (.json)")
        self.yolo_rb = QRadioButton("YOLO (.txt)")
        self.coco_rb = QRadioButton("COCO (.json)")
        self.raw_rb.setChecked(True)

        self.format_group = QButtonGroup(self)
        for rb in (self.raw_rb, self.yolo_rb, self.coco_rb):
            self.format_group.addButton(rb)
            layout.addWidget(rb)

        # --- Enable/disable formats based on session mode ---
        if session.label_mode == "rect":
            self.raw_rb.setEnabled(True)
            self.yolo_rb.setEnabled(True)
            self.coco_rb.setEnabled(False)
            self.yolo_rb.setChecked(True)
        elif session.label_mode == "polygon":
            self.raw_rb.setEnabled(True)
            self.yolo_rb.setEnabled(False)
            self.coco_rb.setEnabled(True)
            self.coco_rb.setChecked(True)

        # --- Path selection ---
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Select save folder...")
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.select_folder)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)

        # --- OK / Cancel buttons ---
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def select_folder(self) -> None:
        """Open folder selection dialog."""
        folder = QFileDialog.getExistingDirectory(self, "Select Save Folder")
        if folder:
            self.path_edit.setText(folder)
            self.save_path = folder

    def get_results(self) -> dict[str, str]:
        """Return selected format and save folder."""
        if self.raw_rb.isChecked():
            fmt = "raw"
        elif self.yolo_rb.isChecked():
            fmt = "yolo"
        elif self.coco_rb.isChecked():
            fmt = "coco"
        else:
            fmt = None

        return {"format": fmt or "", "path": self.path_edit.text()}
