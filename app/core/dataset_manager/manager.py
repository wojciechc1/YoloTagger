import logging
from app.core.dataset_manager.items import DatasetItem, FolderItem, FileItem
from app.core.dataset_manager.io_json import load_labels_json, save_labels_json
from app.core.dataset_manager.io_yolo import get_all_yolo_labels, save_yaml_yolo, save_all_yolo, load_yolo_labels_auto
from app.core.dataset_manager.io_coco import save_all_coco, load_labels_coco

logger = logging.getLogger(__name__)

class DatasetManager:
    def __init__(self):
        self.exts = (".jpg", ".jpeg", ".png")
        self.current_item = None  # FileItem, FolderItem or DatasetItem

    # --- Open images ---
    def open_file(self, path):
        self.current_item = FileItem(path)
        logger.info("Opened file: %s", path)

    def open_folder(self, path):
        self.current_item = FolderItem(path)
        logger.info("Opened folder: %s (%d images)", path, len(self.current_item.files))

    def open_dataset(self, path):
        self.current_item = DatasetItem(path)
        n_train = len(self.current_item.train)
        n_val = len(self.current_item.val)
        logger.info("Opened dataset: %s (train=%d, val=%d)", path, n_train, n_val)

    # --- Load labels ---
    def load_json(self, path, available_images):
        labels = load_labels_json(path, available_images)
        logger.info("Loaded JSON labels from %s", path)
        return labels

    def load_yolo(self, path, available_images):
        labels = load_yolo_labels_auto(path, available_images)
        logger.info("Loaded YOLO labels from %s", path)
        return labels

    def load_coco(self, path, available_images):
        labels = load_labels_coco(path, available_images)
        logger.info("Loaded COCO labels from %s", path)
        return labels

    # --- Save labels ---
    def save_json(self, all_labels, save_path):
        save_labels_json(all_labels, save_path)
        logger.info("Saved JSON labels to %s", save_path)

    def save_yolo(self, files, all_labels, unique_classes, save_folder):
        all_yolo = get_all_yolo_labels(files, all_labels)
        save_all_yolo(self.current_item, all_yolo, save_folder)
        save_yaml_yolo(self.current_item, unique_classes)
        logger.info("Saved YOLO labels and data.yaml to %s", save_folder or self.current_item.dataset_dir)

    def save_coco(self, all_labels, save_folder):
        save_all_coco(self.current_item, all_labels, save_folder)
        logger.info("Saved COCO labels to %s", save_folder or self.current_item.dataset_dir)

    # --- Get files list ---
    def get_all_files(self):
        """Return list of dicts with path, size and type."""
        if not self.current_item:
            return []

        files = []
        if hasattr(self.current_item, "path"):  # single file
            files.append({"path": self.current_item.path, "size": self.current_item.img_size, "type": "file"})
        elif hasattr(self.current_item, "files"):  # folder
            for f in self.current_item.files:
                files.append({"path": f.path, "size": f.img_size, "type": "folder"})
        elif hasattr(self.current_item, "train") and hasattr(self.current_item, "val"):  # dataset
            for f in self.current_item.train:
                files.append({"path": f.path, "size": f.img_size, "type": "train"})
            for f in self.current_item.val:
                files.append({"path": f.path, "size": f.img_size, "type": "val"})
        return files

    # --- Get FileItem by path ---
    def get_file_item(self, file_path):
        """Return FileItem for given path or None."""
        if not self.current_item:
            return None

        if isinstance(self.current_item, FileItem):
            return self.current_item if self.current_item.path == file_path else None
        elif isinstance(self.current_item, FolderItem):
            for f in self.current_item.files:
                if f.path == file_path:
                    return f
        elif isinstance(self.current_item, DatasetItem):
            for f in self.current_item.train + self.current_item.val:
                if f.path == file_path:
                    return f
        return None

    # --- Get allowed extensions ---
    def get_extensions(self):
        return self.exts

    # --- Set image size manually ---
    def set_img_size(self, file_path, size):
        """Set img_size for FileItem matching path."""
        file_item = self.get_file_item(file_path)
        if file_item:
            file_item._img_size = size
            logger.info("Set img_size for %s: %s", file_item.path, file_item.img_size)
