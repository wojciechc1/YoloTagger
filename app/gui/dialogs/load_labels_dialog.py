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
from typing import Any, Dict, Optional


class LoadDialog(QDialog):
    """Dialog for selecting label loading options (format + path)."""

    def __init__(self, session: Any, parent: Optional[QDialog] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Load Labels Options")
        self.resize(400, 200)
        self.load_path = ""

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Select format to load:"))

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
        self.path_edit.setPlaceholderText("Select file or folder...")
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.select_path)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)

        # --- OK / Cancel buttons ---
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def select_path(self) -> None:
        """Open file/folder dialog depending on selected format."""
        if self.yolo_rb.isChecked():
            folder = QFileDialog.getExistingDirectory(self, "Select YOLO Labels Folder")
            if folder:
                self.path_edit.setText(folder)
                self.load_path = folder

        elif self.coco_rb.isChecked():
            folder = QFileDialog.getExistingDirectory(self, "Select COCO Labels Folder")
            if folder:
                self.path_edit.setText(folder)
                self.load_path = folder

        else:  # raw format
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Label File", "", "JSON or YAML Files (*.json *.yaml)"
            )
            if file_path:
                self.path_edit.setText(file_path)
                self.load_path = file_path

    def get_results(self) -> Dict[str, str]:
        """Return selected format and path."""
        if self.raw_rb.isChecked():
            fmt = "raw"
        elif self.yolo_rb.isChecked():
            fmt = "yolo"
        elif self.coco_rb.isChecked():
            fmt = "coco"
        else:
            fmt = None

        return {"format": fmt or "", "path": self.path_edit.text()}
