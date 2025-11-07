from PyQt5.QtWidgets import QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem, QWidget
from PyQt5.QtCore import pyqtSignal
import os
from typing import List, Dict, Any


class DatasetPanel(QWidget):
    """Displays dataset structure and allows file selection."""

    fileSelected = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Initialize layout and tree view."""
        layout = QVBoxLayout(self)

        label = QLabel("Files:")
        label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(label)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.itemClicked.connect(self.on_tree_item_clicked)
        layout.addWidget(self.tree_widget)

    def refresh_file_list(self, files: List[Dict[str, Any]]) -> None:
        """Rebuild tree view based on given file list."""
        self.tree_widget.clear()

        # Group files by type
        tree_dict: Dict[str, List[str]] = {}
        for f in files:
            file_type = f["type"]
            tree_dict.setdefault(file_type, []).append(f["path"])

        # Build tree structure
        for type_name, paths in tree_dict.items():
            parent_item = QTreeWidgetItem([type_name])
            self.tree_widget.addTopLevelItem(parent_item)
            for p in paths:
                child_item = QTreeWidgetItem([os.path.basename(p)])
                child_item.setData(0, 1, p)  # store full path
                parent_item.addChild(child_item)
            parent_item.setExpanded(True)

    def on_tree_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Emit selected file path when clicked."""
        path: str = item.data(0, 1)
        if path:
            self.fileSelected.emit(path)
