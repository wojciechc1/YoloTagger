# app/windows/main_window.py
from PyQt5.QtWidgets import (
    QMainWindow,
    QAction,
    QPushButton,
    QHBoxLayout,
    QFileDialog,
    QMessageBox,
    QWidget,
    QVBoxLayout,
    QDialog,
    QShortcut,
    QLabel,
    QComboBox,
)
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt, QTimer
import os

# --- Core imports ---
from app.core.dataset.dataset_service import DatasetService
from app.core.label_service import LabelService
from app.core.session_state import SessionState
from app.core.session_controller import SessionController
from app.core.model.model_handler import ModelHandler
from app.core.class_color_registry import ClassColorRegistry

# --- GUI imports ---
from app.gui.image_panel import ImagePanel
from app.gui.dataset_panel import DatasetPanel
from app.gui.class_panel import ClassPanel
from app.gui.dialogs.save_dialog import SaveDialog
from app.gui.dialogs.load_labels_dialog import LoadDialog
from app.gui.dialogs.label_type_dialog import LabelTypeDialog
from typing import Optional


class MainWindow(QMainWindow):
    """Main application window for YoloTagger."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("YoloTagger")
        self.setGeometry(100, 100, 1200, 600)

        # --- Core session/state ---
        self.session = SessionState()
        self.dataset_service = DatasetService()
        self.label_service = LabelService()
        self.model_handler = ModelHandler()
        self.color_registry = ClassColorRegistry()

        # --- Panels ---
        self.image_panel = ImagePanel(color_callback=self.color_registry.get_color)
        self.dataset_panel = DatasetPanel()
        self.class_panel = ClassPanel(color_callback=self.color_registry.get_color)

        # --- Controller ---
        self.session_controller = SessionController(
            self.dataset_service,
            self.label_service,
            self.model_handler,
            self.color_registry,
            self.session,
        )

        # --- Signal connections ---
        self.session.label_mode_changed.connect(self.on_label_mode_changed)
        self.session_controller.datasetLoaded.connect(
            self.dataset_panel.refresh_file_list
        )
        self.session_controller.requestLabelMode.connect(self.show_label_type_dialog)
        self.session_controller.requestLabelRefresh.connect(
            self.image_panel.update_labels
        )
        self.session_controller.classesUpdated.connect(
            self.class_panel.refresh_classes_list
        )
        self.session_controller.fileChanged.connect(self.image_panel.load_image)
        self.session_controller.saveCompleted.connect(self.on_save_completed)

        # --- Class panel events ---
        self.class_panel.addClassRequested.connect(self.session_controller.add_class)
        self.class_panel.editClassRequested.connect(self.session_controller.edit_class)
        self.class_panel.removeClassRequested.connect(
            self.session_controller.remove_class
        )
        self.class_panel.classSelected.connect(self.on_class_selected)

        # --- Label events ---
        self.image_panel.labelAdded.connect(self.session_controller.add_label)
        self.image_panel.labelRemoved.connect(self.session_controller.remove_label)
        self.image_panel.labelChanged.connect(self.session_controller.update_label)

        # --- Keyboard shortcuts ---
        QShortcut(QKeySequence("Right"), self).activated.connect(
            self.session_controller.show_next_file
        )
        QShortcut(QKeySequence("Left"), self).activated.connect(
            self.session_controller.show_prev_file
        )
        QShortcut(QKeySequence("R"), self).activated.connect(self.draw_label)
        QShortcut(QKeySequence("P"), self).activated.connect(self.draw_label)

        # --- Setup UI ---
        self._createMenu()
        self._createCentralWidget()
        self.image_panel.rectangleDrawRequested.connect(self.rect.click)
        self._filtered_paths = None
        self.dataset_panel.fileSelected.connect(self.session_controller.show_file)
        self.box_filter.currentIndexChanged.connect(self.apply_box_filter)
        self.session_controller.datasetLoaded.connect(self.reset_box_filter)
        self.session_controller.datasetLoaded.connect(self.update_image_progress)
        self.session_controller.fileChanged.connect(self.update_image_progress)
        self.session_controller.requestLabelRefresh.connect(self.refresh_box_filter)
        self.update_image_progress()

        self.save_notification = QMessageBox(self)
        self.save_notification.setWindowTitle("Saved")
        self.save_notification.setIcon(QMessageBox.Information)
        self.save_notification.setStandardButtons(QMessageBox.NoButton)
        self.save_notification.setModal(False)
        self.save_notification.setAttribute(Qt.WA_ShowWithoutActivating)
        self.save_notification_timer = QTimer(self)
        self.save_notification_timer.setSingleShot(True)
        self.save_notification_timer.timeout.connect(self.save_notification.hide)

    # ---------------- Menu ----------------
    def _createMenu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        edit_menu = menu.addMenu("Edit")
        tools_menu = menu.addMenu("Tools")
        view_menu = menu.addMenu("View")

        # --- File menu ---
        open_file = QAction("Open File", self)
        open_folder = QAction("Open Folder", self)
        open_dataset = QAction("Open Dataset", self)
        save_as = QAction("Save Labels As", self)
        save = QAction("Save Labels", self)
        load_labels = QAction("Load Labels", self)

        open_file.triggered.connect(self.on_open_file_clicked)
        open_folder.triggered.connect(self.on_open_folder_clicked)
        open_dataset.triggered.connect(self.on_open_dataset_clicked)
        save_as.triggered.connect(self.on_save_as_clicked)
        save.triggered.connect(self.on_save_clicked)
        load_labels.triggered.connect(self.on_load_labels_clicked)

        file_menu.addActions([open_file, open_folder, open_dataset])
        file_menu.addSeparator()
        file_menu.addActions([save_as, save])
        file_menu.addSeparator()
        file_menu.addAction(load_labels)

        # --- Edit menu ---
        next_file = QAction("Next", self)
        prev_file = QAction("Prev", self)
        delete_label = QAction("Delete Selected Label", self)
        next_file.triggered.connect(self.session_controller.show_next_file)
        prev_file.triggered.connect(self.session_controller.show_prev_file)
        delete_label.triggered.connect(self.image_panel.delete_selected_items)
        edit_menu.addActions([next_file, prev_file, delete_label])

        # --- Tools menu ---
        select_model = QAction("Select Model", self)
        predict_image = QAction("Predict Current Image", self)
        predict_image.triggered.connect(self.session_controller.predict_image)
        select_model.triggered.connect(self.on_select_model)
        tools_menu.addActions([select_model, predict_image])

        # --- View menu (zoom controls) ---
        zoom_in = QAction("Zoom In", self)
        zoom_out = QAction("Zoom Out", self)
        zoom_reset = QAction("Reset Zoom", self)
        zoom_in.triggered.connect(lambda: self.image_panel.zoom(1.25))
        zoom_out.triggered.connect(lambda: self.image_panel.zoom(0.8))
        zoom_reset.triggered.connect(lambda: self.image_panel.reset_zoom())
        view_menu.addActions([zoom_in, zoom_out, zoom_reset])

    # ---------------- Layout ----------------
    def _createCentralWidget(self):
        """Create main layout with image panel and side panels."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        # --- Left column (tools) ---
        col1 = QVBoxLayout()
        next_btn = QPushButton("Next")
        next_btn.clicked.connect(self.session_controller.show_next_file)
        col1.addWidget(next_btn)

        prev_btn = QPushButton("Prev")
        prev_btn.clicked.connect(self.session_controller.show_prev_file)
        col1.addWidget(prev_btn)

        self.rect: QPushButton = QPushButton("Draw Rectangle")
        self.rect.clicked.connect(self.draw_label)
        self.rect.setEnabled(False)
        col1.addWidget(self.rect)

        self.polygon: QPushButton = QPushButton("Draw Polygon")
        self.polygon.clicked.connect(self.draw_label)
        self.polygon.setEnabled(False)
        col1.addWidget(self.polygon)

        remove_label = QPushButton("Remove Label")
        remove_label.clicked.connect(self.image_panel.delete_selected_items)
        col1.addWidget(remove_label)

        self.clear_labels_button = QPushButton("Clear All Labels\n(Current Image)")
        self.clear_labels_button.clicked.connect(
            self.session_controller.clear_current_labels
        )
        self.clear_labels_button.setToolTip(
            "Clear all annotations on the displayed image. Use Save Labels to save."
        )
        col1.addWidget(self.clear_labels_button)

        self.save_button = QPushButton("Save Labels")
        self.save_button.clicked.connect(self.on_save_clicked)

        for button in (
            next_btn,
            prev_btn,
            self.rect,
            self.polygon,
            remove_label,
            self.clear_labels_button,
            self.save_button,
        ):
            button.setMinimumSize(150, 48)
            button.setStyleSheet("font-weight: bold; padding: 8px 12px;")

        col1.addStretch()

        layout.addLayout(col1)

        # --- Middle column (image canvas) ---
        col2 = QVBoxLayout()
        image_info = QHBoxLayout()
        self.image_progress = QLabel()
        self.image_progress.setToolTip(
            "Passed and left count images before and after the current image. "
            "They do not indicate saved or confirmed reviews."
        )
        self.image_progress.setStyleSheet("font-weight: bold; padding: 6px;")
        image_info.addWidget(self.image_progress)
        image_info.addStretch()
        col2.addLayout(image_info)
        col2.addWidget(self.image_panel)
        self.box_count = QLabel("Bounding boxes: 0")
        self.box_count.setStyleSheet(
            "font-weight: bold; font-size: 24px; padding: 10px;"
        )
        image_actions = QHBoxLayout()
        image_actions.addStretch()
        image_actions.addWidget(self.box_count)
        image_actions.addWidget(self.save_button)
        image_actions.addStretch()
        col2.addLayout(image_actions)
        layout.addLayout(col2, stretch=2)

        # --- Right column (class & dataset panels) ---
        col3 = QVBoxLayout()
        col3.addWidget(self.class_panel, 1)
        col3.addWidget(QLabel("Filter images by bounding boxes:"))
        self.box_filter = QComboBox()
        self.box_filter.addItem("All images", None)
        for count in range(4):
            self.box_filter.addItem(f"Exactly {count} bounding boxes", count)
        self.box_filter.addItem("3+ bounding boxes", "3+")
        self.box_filter.setToolTip("Load your labels first, then select a box count.")
        col3.addWidget(self.box_filter)
        col3.addWidget(self.dataset_panel, 1)
        layout.addLayout(col3)

    # ---------------- Slots ----------------
    def reset_box_filter(self) -> None:
        self.box_filter.blockSignals(True)
        self.box_filter.setCurrentIndex(0)
        self.box_filter.blockSignals(False)
        self.session_controller.box_count_filter = None
        self._filtered_paths = None

    def apply_box_filter(self) -> None:
        self.session_controller.box_count_filter = self.box_filter.currentData()
        indices = self.session_controller.visible_file_indices()
        if indices and self.session.current_index not in indices:
            file_path = self.session.files[indices[0]]["path"]
            self.session_controller.show_file(file_path)
        else:
            self.refresh_box_filter()

    def refresh_box_filter(self, labels: Optional[list] = None) -> None:
        indices = self.session_controller.visible_file_indices()
        files = [self.session.files[index] for index in indices]
        paths = tuple(file["path"] for file in files)
        if paths != self._filtered_paths:
            self.dataset_panel.refresh_file_list(files)
            self._filtered_paths = paths
        self.update_image_progress()

    def update_image_progress(self) -> None:
        indices = self.session_controller.visible_file_indices()
        total = len(indices)
        position = (
            indices.index(self.session.current_index) + 1
            if self.session.current_index in indices
            else 0
        )
        passed = max(0, position - 1)
        self.image_progress.setText(
            f"Image {position} / {total}   |   Passed: {passed}   |   Left: {total - position}"
        )
        if self.session.files and not position:
            self.image_progress.setText(
                f"Matching images: {total} | Current image does not match filter"
            )
        labels = []
        if self.session.files:
            image_path = self.session.files[self.session.current_index]["path"]
            labels = self.label_service.labels.get(image_path, [])
        self.update_box_count(labels)
        self.clear_labels_button.setEnabled(bool(self.session.files))

    def update_box_count(self, labels: list) -> None:
        count = sum(label.get("type") == "rect" for label in labels)
        self.box_count.setText(f"Bounding boxes: {count}")

    def draw_label(self) -> None:
        """Trigger label drawing based on current mode."""
        self.image_panel.draw_label(self.session.label_mode, self.session.current_class)

    def on_label_mode_changed(self, mode: Optional[str]) -> None:
        """Enable/disable drawing buttons based on selected label mode."""
        self.rect.setEnabled(mode == "rect")
        self.polygon.setEnabled(mode == "polygon")

    def on_class_selected(self, selected_class: Optional[int]) -> None:
        """Set the currently selected class."""
        self.session.current_class = selected_class

    def on_select_model(self) -> None:
        # --- Open file dialog ---
        file_path, _ = QFileDialog.getOpenFileName(
            None, "Select YOLO Model (.pt)", "", "PyTorch Model (*.pt)"
        )
        if not file_path:
            return  # user cancelled

        self.session_controller.on_select_model(file_path)

    # ---------------- File actions ----------------
    def on_save_as_clicked(self) -> None:
        """Save labels to a custom path and format."""
        dialog = SaveDialog(self.session, self)
        if dialog.exec_() == QDialog.Accepted:
            result = dialog.get_results()
            self.session_controller.save(result["path"], result["format"])

    def on_save_clicked(self) -> None:
        """Quick save using last save path."""
        if not self.session.save_path:
            self.on_save_as_clicked()
            return
        self.session_controller.save()

    def on_save_completed(self, path_or_error: str) -> None:
        """Display result message after save."""
        if path_or_error == "error_no_path":
            QMessageBox.warning(self, "Error", "No save path selected.")
        else:
            self.save_notification.setText(f"Files saved to: {path_or_error}")
            self.save_notification.show()
            self.save_notification_timer.start(1000)

    def on_open_file_clicked(self) -> None:
        """Open a single image file."""
        ext_filter = " ".join(
            f"*{ext}" for ext in self.dataset_service.get_extensions()
        )
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", f"Images ({ext_filter});;All Files (*)"
        )
        if file_path:
            self.session_controller.open_file(file_path)

    def on_open_folder_clicked(self) -> None:
        """Open folder with images."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.session_controller.open_folder(folder)

    def on_open_dataset_clicked(self) -> None:
        """Open YOLO-style dataset folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Dataset Folder")
        if not folder:
            return
        images_train = os.path.join(folder, "images", "train")
        labels_train = os.path.join(folder, "labels", "train")
        if os.path.exists(images_train) and os.path.exists(labels_train):
            self.session_controller.open_dataset(folder)

    # ---------------- Label actions ----------------
    def show_label_type_dialog(self) -> None:
        """Ask user for label type (rect/polygon)."""
        dialog = LabelTypeDialog(self.session, self)
        if dialog.exec_() != QDialog.Accepted:
            self.session.label_mode = dialog.selected_mode

    def on_load_labels_clicked(self) -> None:
        """Load labels from external file."""
        dialog = LoadDialog(self.session, self)
        if dialog.exec_() == QDialog.Accepted:
            result = dialog.get_results()
            self.session_controller.load_labels(result["path"], result["format"])
