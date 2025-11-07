import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class LabelService:
    """Manages labels for images and tracks unique classes."""

    def __init__(self):
        self.labels: Dict[str, List[Dict[str, Any]]] = {}  # "img_path": [label_dicts]
        self.unique_classes: Dict[int, str] = {}
        self.next_class_id: int = max(self.unique_classes.keys(), default=-1) + 1

    # --- Label operations ---
    def add_label(
        self, img_path: str, selected_class: int, label_type: str, coords: List[Any]
    ) -> None:
        self.ensure_entry(img_path)
        label_id = self.get_next_id(img_path)
        label_data = {
            "id": label_id,
            "class": selected_class,
            "type": label_type,
            "coords": coords,
        }
        self.labels[img_path].append(label_data)
        logger.info("Added label %s to image %s", label_data, img_path)

    def update_label(self, img_path: str, label_id: int, coords: List[Any]) -> None:
        self.ensure_entry(img_path)
        for label in self.labels[img_path]:
            if label["id"] == label_id:
                label["coords"] = coords
                logger.info("Updated label %s with new coords %s", label_id, coords)
                break

    def remove_label(self, img_path: str, label_id: int) -> None:
        self.ensure_entry(img_path)
        before = len(self.labels[img_path])
        self.labels[img_path] = [
            label for label in self.labels[img_path] if label["id"] != label_id
        ]
        after = len(self.labels[img_path])
        logger.info(
            "Removed label %s from image %s (%d -> %d labels)",
            label_id,
            img_path,
            before,
            after,
        )

    def get_labels(self, img_path: str) -> List[Dict[str, Any]]:
        self.ensure_entry(img_path)
        return self.labels[img_path]

    def clear_labels(self, img_path: str) -> None:
        self.labels[img_path] = []
        logger.info("Cleared all labels for image %s", img_path)

    def has_labels(self, img_path: str) -> bool:
        return bool(self.labels.get(img_path))

    # --- Unique class operations ---
    def get_unique_classes(self) -> Dict[int, str]:
        return dict(sorted(self.unique_classes.items()))

    def add_unique_class(self, unique_class: str) -> int:
        for cid, cname in self.unique_classes.items():
            if cname == unique_class:
                return cid

        existing_ids = set(self.unique_classes.keys())
        new_id = 0
        while new_id in existing_ids:
            new_id += 1

        self.unique_classes[new_id] = unique_class
        self.next_class_id = max(self.next_class_id, new_id + 1)
        logger.info("Added unique class %s with id %d", unique_class, new_id)
        return new_id

    def edit_class(self, class_id: int, new_name: str) -> None:
        if class_id in self.unique_classes:
            old_name = self.unique_classes[class_id]
            self.unique_classes[class_id] = new_name
            logger.info("Renamed class %d: %s -> %s", class_id, old_name, new_name)

    def remove_unique_class(self, class_id: int) -> None:
        class_id = int(class_id)
        if class_id in self.unique_classes:
            removed = self.unique_classes[class_id]
            del self.unique_classes[class_id]
            logger.info("Removed unique class %d: %s", class_id, removed)
        for img_path, labels in self.labels.items():
            self.labels[img_path] = [
                label for label in labels if label["class"] != class_id
            ]

    # --- Loading / resetting ---
    def load_labels(self, mapped_labels: Dict[str, List[Dict[str, Any]]]) -> None:
        self.reset_labels()
        class_names = sorted(
            {label["class"] for labels in mapped_labels.values() for label in labels}
        )
        self.unique_classes = {i: name for i, name in enumerate(class_names)}
        self.next_class_id = len(self.unique_classes)

        for img_path, labels in mapped_labels.items():
            self.set_labels(img_path, labels)
        logger.info("Loaded labels for %d images", len(mapped_labels))

    def reset_labels(self) -> None:
        self.labels = {}
        self.unique_classes = {}
        self.next_class_id = 0
        logger.info("Reset all labels and unique classes")

    # --- Helpers ---
    def get_next_id(self, img_path: str) -> int:
        labels_for_img = self.labels.get(img_path, [])
        return max([label["id"] for label in labels_for_img], default=-1) + 1

    def set_labels(self, img_path: str, label_data: List[Dict[str, Any]]) -> None:
        self.labels[img_path] = label_data

    def ensure_entry(self, img_path: str) -> None:
        if img_path not in self.labels:
            self.labels[img_path] = []
