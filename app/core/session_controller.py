import os
import logging
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class SessionController(QObject):
    # --- Signals for GUI ---
    datasetLoaded = pyqtSignal(list)
    fileChanged = pyqtSignal(str)
    labelsUpdated = pyqtSignal(list)
    classesUpdated = pyqtSignal(dict)
    sessionChanged = pyqtSignal()
    saveCompleted = pyqtSignal(str)
    requestLabelMode = pyqtSignal()
    requestLabelRefresh = pyqtSignal(list)

    def __init__(
        self,
        dataset_manager,
        label_manager,
        model_manager,
        color_manager,
        session_state,
    ):
        super().__init__()
        self.dataset_manager = dataset_manager
        self.label_manager = label_manager
        self.model_manager = model_manager
        self.color_manager = color_manager
        self.state = session_state

    # --- Save labels ---
    def save(self, path: str = None, fmt: str = None):
        path = path or self.state.save_path
        fmt = fmt or self.state.save_format

        if not path:
            self.saveCompleted.emit("error_no_path")
            logger.warning("Save failed: no path specified")
            return

        self.state.save_format = fmt
        self.state.save_path = path

        if fmt == "raw":
            save_path = os.path.join(path, "labels.json")
            self.dataset_manager.save_json(self.label_manager.labels, save_path)
            self.saveCompleted.emit(save_path)
            logger.info("Saved raw JSON labels to %s", save_path)
        elif fmt == "yolo":
            self.dataset_manager.save_yolo(
                self.state.files,
                self.label_manager.labels,
                self.label_manager.get_unique_classes(),
                self.state.save_path,
            )
            self.saveCompleted.emit(path)
            logger.info("Saved YOLO labels to %s", path)
        elif fmt == "coco":
            save_path = os.path.join(path, "coco.json")
            self.dataset_manager.save_coco(self.label_manager.labels, save_path)
            self.saveCompleted.emit(save_path)
            logger.info("Saved COCO labels to %s", save_path)

    # --- Load labels ---
    def load_labels(self, path, fmt):
        logger.info("Loading labels from %s (format: %s)", path, fmt)
        if fmt == "raw":
            available_images = [f["path"] for f in self.state.files]
            mapped_labels = self.dataset_manager.load_json(path, available_images)
        elif fmt == "yolo":
            mapped_labels = self.dataset_manager.load_yolo(path, self.state.files)
        elif fmt == "coco":
            mapped_labels = self.dataset_manager.load_coco(path, self.state.files)
        else:
            logger.warning("Unknown format: %s", fmt)
            return

        self.label_manager.load_labels(mapped_labels)
        self.classesUpdated.emit(self.label_manager.get_unique_classes())
        self.requestLabelRefresh.emit(
            self.label_manager.get_labels(
                self.state.files[self.state.current_index]["path"]
            )
        )
        logger.info("Loaded labels for %d images", len(mapped_labels))

    # --- File navigation ---
    def show_next_file(self):
        if self.state.current_index + 1 < len(self.state.files):
            self.state.current_index += 1
            next_file = self.state.files[self.state.current_index]["path"]
            self.fileChanged.emit(next_file)
            self.requestLabelRefresh.emit(self.label_manager.get_labels(next_file))
            logger.info("Switched to next file: %s", next_file)

    def show_prev_file(self):
        if self.state.current_index > 0:
            self.state.current_index -= 1
            prev_file = self.state.files[self.state.current_index]["path"]
            self.fileChanged.emit(prev_file)
            self.requestLabelRefresh.emit(self.label_manager.get_labels(prev_file))
            logger.info("Switched to previous file: %s", prev_file)

    # --- Open file/folder/dataset ---
    def open_file(self, file_path):
        self.dataset_manager.open_file(file_path)
        self.state.files = self.dataset_manager.get_all_files()
        self.state.current_index = 0
        self.label_manager.reset_labels()

        self.datasetLoaded.emit(self.state.files)
        self.fileChanged.emit(file_path)
        self.requestLabelMode.emit()
        self.classesUpdated.emit(self.label_manager.get_unique_classes())
        self.requestLabelRefresh.emit(self.label_manager.get_labels(file_path))
        logger.info("Opened single file: %s", file_path)

    def open_folder(self, folder):
        self.dataset_manager.open_folder(folder)
        self.state.files = self.dataset_manager.get_all_files()
        self.state.current_index = 0
        self.label_manager.reset_labels()

        self.datasetLoaded.emit(self.state.files)
        self.fileChanged.emit(self.state.files[0]["path"])
        self.requestLabelMode.emit()
        self.classesUpdated.emit(self.label_manager.get_unique_classes())
        self.requestLabelRefresh.emit(
            self.label_manager.get_labels(
                self.state.files[self.state.current_index]["path"]
            )
        )
        logger.info("Opened folder: %s, %d files loaded", folder, len(self.state.files))

    def open_dataset(self, folder):
        self.dataset_manager.open_dataset(folder)
        self.state.files = self.dataset_manager.get_all_files()
        self.state.current_index = 0
        self.label_manager.reset_labels()

        self.datasetLoaded.emit(self.state.files)
        self.fileChanged.emit(self.state.files[0]["path"])
        self.requestLabelMode.emit()
        self.classesUpdated.emit(self.label_manager.get_unique_classes())
        self.requestLabelRefresh.emit(
            self.label_manager.get_labels(self.state.files[0]["path"])
        )
        logger.info(
            "Opened dataset: %s, %d files loaded", folder, len(self.state.files)
        )

    # --- Class management ---
    def add_class(self, class_name):
        class_id = self.label_manager.add_unique_class(class_name)
        self.classesUpdated.emit(self.label_manager.get_unique_classes())
        logger.info("Added class '%s' with id %d", class_name, class_id)

    def remove_class(self, class_id):
        self.label_manager.remove_unique_class(class_id)
        self.classesUpdated.emit(self.label_manager.get_unique_classes())
        self.requestLabelRefresh.emit(
            self.label_manager.get_labels(
                self.state.files[self.state.current_index]["path"]
            )
        )
        logger.info("Removed class id %d", class_id)

    def edit_class(self, class_id, new_class_name, color):
        self.label_manager.edit_class(class_id, new_class_name)
        self.classesUpdated.emit(self.label_manager.get_unique_classes())
        self.color_manager.set_color(class_id, color)
        logger.info("Edited class id %d -> %s", class_id, new_class_name)

    # --- Label management ---
    def add_label(self, file, class_name, label_type, coords):
        self.label_manager.add_label(file, class_name, label_type, coords)
        self.requestLabelRefresh.emit(
            self.label_manager.get_labels(
                self.state.files[self.state.current_index]["path"]
            )
        )
        logger.info(
            "Added label to file %s, class %s, type %s", file, class_name, label_type
        )

    def remove_label(self, file, label_id):
        self.label_manager.remove_label(file, label_id)
        self.requestLabelRefresh.emit(
            self.label_manager.get_labels(
                self.state.files[self.state.current_index]["path"]
            )
        )
        logger.info("Removed label id %d from file %s", label_id, file)

    def update_label(self, file_path, label_id, coords):
        self.label_manager.update_label(file_path, label_id, coords)
        logger.info("Updated label id %d in file %s", label_id, file_path)

    # --- Model actions ---
    def on_select_model(self, path):
        try:
            model_classes = self.model_manager.load_model(path)
        except Exception as e:
            logger.warning("Failed to load model: %s", e)
            return

        self.label_manager.reset_labels()

        for class_id, class_name in model_classes.items():
            self.label_manager.add_unique_class(class_name)

        self.classesUpdated.emit(self.label_manager.get_unique_classes())

    def predict_image(self):
        image_path = self.state.files[self.state.current_index]["path"]
        predicted_labels = self.model_manager.predict(image_path)
        logger.info(
            "Predicted %d labels for image %s", len(predicted_labels), image_path
        )

        for pred in predicted_labels:
            if "bbox" in pred:
                label_type = "rect"
                coords = pred["bbox"]
            elif "mask" in pred:
                label_type = "polygon"
                coords = pred["mask"]
            else:
                continue

            class_name = pred.get("class_id")
            self.add_label(image_path, class_name, label_type, coords)
