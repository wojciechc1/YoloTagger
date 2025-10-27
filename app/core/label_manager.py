import os
import logging

logger = logging.getLogger(__name__)

class LabelManager:
    """Manages labels for images and tracks unique classes."""

    def __init__(self):
        self.labels = {}  # "img_path": [label_dicts]
        self.unique_classes = {0: "Cat", 1: "Dog"}
        self.next_class_id = max(self.unique_classes.keys()) + 1

    # --- Label operations ---
    def add_label(self, img_path, selected_class, label_type, coords):
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

    def update_label(self, img_path, label_id, coords):
        self.ensure_entry(img_path)
        for label in self.labels[img_path]:
            if label["id"] == label_id:
                label["coords"] = coords
                logger.info("Updated label %s with new coords %s", label_id, coords)
                break

    def remove_label(self, img_path, label_id):
        self.ensure_entry(img_path)
        before = len(self.labels[img_path])
        self.labels[img_path] = [l for l in self.labels[img_path] if l["id"] != label_id]
        after = len(self.labels[img_path])
        logger.info("Removed label %s from image %s (%d -> %d labels)", label_id, img_path, before, after)

    def get_labels(self, img_path):
        self.ensure_entry(img_path)
        return self.labels[img_path]

    def clear_labels(self, img_path):
        self.labels[img_path] = []
        logger.info("Cleared all labels for image %s", img_path)

    def has_labels(self, img_path) -> bool:
        return bool(self.labels.get(img_path))

    # --- Unique class operations ---
    def get_unique_classes(self):
        return dict(sorted(self.unique_classes.items()))

    def add_unique_class(self, unique_class):
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

    def edit_class(self, class_id, new_name):
        if class_id in self.unique_classes:
            old_name = self.unique_classes[class_id]
            self.unique_classes[class_id] = new_name
            logger.info("Renamed class %d: %s -> %s", class_id, old_name, new_name)

    def remove_unique_class(self, class_id):
        class_id = int(class_id)
        if class_id in self.unique_classes:
            removed = self.unique_classes[class_id]
            del self.unique_classes[class_id]
            logger.info("Removed unique class %d: %s", class_id, removed)
        for img_path, labels in self.labels.items():
            self.labels[img_path] = [l for l in labels if l["class"] != class_id]

    # --- Loading / resetting ---
    def load_labels(self, mapped_labels):
        self.reset_labels()
        class_names = sorted({l['class'] for labels in mapped_labels.values() for l in labels})
        self.unique_classes = {i: name for i, name in enumerate(class_names)}
        self.next_class_id = len(self.unique_classes)

        for img_path, labels in mapped_labels.items():
            self.set_labels(img_path, labels)
        logger.info("Loaded labels for %d images", len(mapped_labels))

    def reset_labels(self):
        self.labels = {}
        self.unique_classes = {}
        self.next_class_id = 0
        logger.info("Reset all labels and unique classes")

    # --- Helpers ---
    def get_next_id(self, img_path):
        labels_for_img = self.labels.get(img_path, [])
        return max([l["id"] for l in labels_for_img], default=-1) + 1

    def set_labels(self, img_path, label_data):
        self.labels[img_path] = label_data

    def ensure_entry(self, img_path):
        if img_path not in self.labels:
            self.labels[img_path] = []
