from PyQt5.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QLineEdit,
    QWidget,
    QHBoxLayout,
    QListWidgetItem,
    QDialog,
)
from PyQt5.QtCore import pyqtSignal, Qt
from app.gui.dialogs.edit_class_dialog import EditClassDialog


class ClassPanel(QWidget):
    """Panel for managing object classes (add, edit, remove, select)."""

    classSelected = pyqtSignal(object)  # emits selected class ID
    addClassRequested = pyqtSignal(str)  # emits new class name
    removeClassRequested = pyqtSignal(int)  # emits class ID to remove
    editClassRequested = pyqtSignal(int, str, str)  # emits class ID, name, color

    def __init__(self, color_callback):
        super().__init__()
        self._setup_ui()
        self.get_color_callback = color_callback

    def _setup_ui(self):
        """Create layout and connect UI elements."""
        layout = QVBoxLayout(self)

        label = QLabel("Classes:")
        layout.addWidget(label)

        # --- Input row (add new class) ---
        input_layout = QHBoxLayout()
        self.class_input = QLineEdit()
        self.class_input.setPlaceholderText("Enter new class name...")
        self.add_btn = QPushButton("Add Class")
        self.add_btn.clicked.connect(self.add_class)
        input_layout.addWidget(self.class_input)
        input_layout.addWidget(self.add_btn)
        layout.addLayout(input_layout)

        # --- Edit / Remove buttons ---
        btn_layout = QHBoxLayout()
        self.edit_btn = QPushButton("Edit Selected")
        self.edit_btn.clicked.connect(self.edit_selected_class)
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self.remove_selected_class)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.remove_btn)
        layout.addLayout(btn_layout)

        # --- Class list ---
        self.class_list_widget = QListWidget()
        self.class_list_widget.itemClicked.connect(self.on_class_selected)
        layout.addWidget(self.class_list_widget)

    # --- Add new class ---
    def add_class(self):
        new_class = self.class_input.text().strip()
        if not new_class:
            return
        self.class_input.clear()
        self.addClassRequested.emit(new_class)

    # --- Remove selected class ---
    def remove_selected_class(self):
        selected = self.class_list_widget.currentItem()
        if not selected:
            return
        class_id = int(selected.text().split(":")[0])
        self.removeClassRequested.emit(class_id)
        self.classSelected.emit(None)

    # --- Edit selected class ---
    def edit_selected_class(self):
        selected = self.class_list_widget.currentItem()
        if not selected:
            return

        data = selected.data(Qt.UserRole)
        class_id = data["id"] if isinstance(data, dict) else data
        class_color = self.get_color_callback(class_id)
        class_name = selected.text().split(": ", 1)[1]

        dialog = EditClassDialog(class_name, class_color, self)
        if dialog.exec_() == QDialog.Accepted:
            new_name, new_color = dialog.get_values()
            selected.setText(new_name)
            self.editClassRequested.emit(class_id, new_name, new_color)

    # --- Refresh list ---
    def refresh_classes_list(self, class_dict):
        """Rebuild class list from a dict {id: name}."""
        self.class_list_widget.clear()
        for cid, cname in class_dict.items():
            item = QListWidgetItem(f"{cid}: {cname}")
            item.setData(Qt.UserRole, cid)
            self.class_list_widget.addItem(item)

    # --- On class selected ---
    def on_class_selected(self, item):
        class_id = item.data(Qt.UserRole)
        self.classSelected.emit(class_id)
