import os
import json
import yaml
import logging
from .items import DatasetItem

logger = logging.getLogger(__name__)


# --- Save COCO labels ---
def save_labels_coco(labels, files, save_path):
    """
    Save labels in COCO format.
    labels: dict { image_path: [ { "type": "rect"/"polygon", "coords": [...], "class": class_id } ] }
    files: list of dicts, e.g. [ {"path": "...", "size": (w, h)} ]
    """
    images = []
    annotations = []
    categories = {}
    ann_id = 1

    img_sizes = {f["path"]: f.get("size", (0, 0)) for f in files}

    for img_id, (file_path, img_labels) in enumerate(labels.items(), start=1):
        filename = os.path.basename(file_path)
        img_w, img_h = img_sizes.get(file_path, (0, 0))

        images.append(
            {"id": img_id, "file_name": filename, "width": img_w, "height": img_h}
        )

        for label in img_labels:
            if "coords" not in label or not label["coords"]:
                continue

            class_id = label.get("class")
            if class_id is None:
                continue

            if class_id not in categories:
                categories[class_id] = {"id": class_id, "name": f"class_{class_id}"}

            ann = {
                "id": ann_id,
                "image_id": img_id,
                "category_id": class_id,
                "iscrowd": 0,
            }

            if label["type"] == "rect":
                (x1, y1), (x2, y2) = label["coords"]
                bbox_w = x2 - x1
                bbox_h = y2 - y1
                ann["bbox"] = [x1, y1, bbox_w, bbox_h]
                ann["area"] = bbox_w * bbox_h
                ann["segmentation"] = [[x1, y1, x2, y1, x2, y2, x1, y2]]

            elif label["type"] == "polygon":
                poly = [coord for point in label["coords"] for coord in point]
                xs = [p[0] for p in label["coords"]]
                ys = [p[1] for p in label["coords"]]
                x_min, y_min = min(xs), min(ys)
                x_max, y_max = max(xs), max(ys)

                ann["segmentation"] = [poly]
                ann["bbox"] = [x_min, y_min, x_max - x_min, y_max - y_min]
                ann["area"] = (x_max - x_min) * (y_max - y_min)

            annotations.append(ann)
            ann_id += 1

    coco_dict = {
        "images": images,
        "annotations": annotations,
        "categories": list(categories.values()),
    }

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(coco_dict, f, indent=4, ensure_ascii=False)

    logger.info(f"Saved COCO labels to {save_path}")
    return os.path.abspath(save_path)


# --- Save dataset COCO + YAML for YOLO ---
def save_all_coco(current_item, all_labels, save_folder):
    """
    Save dataset in COCO format.
    Also generates dataset.yaml for YOLOv8/YOLOv9-seg.
    """
    saved_files = []

    if isinstance(current_item, DatasetItem):
        labels_dir = os.path.join(current_item.dataset_dir, "labels")
        os.makedirs(labels_dir, exist_ok=True)

        train_json = os.path.join(labels_dir, "instances_train.json")
        val_json = os.path.join(labels_dir, "instances_val.json")

        train_files = [{"path": f.path, "size": f.img_size} for f in current_item.train]
        val_files = [{"path": f.path, "size": f.img_size} for f in current_item.val]

        train_labels = {
            path: labels
            for path, labels in all_labels.items()
            if any(f["path"] == path for f in train_files)
        }
        val_labels = {
            path: labels
            for path, labels in all_labels.items()
            if any(f["path"] == path for f in val_files)
        }

        if train_labels:
            save_labels_coco(train_labels, train_files, train_json)
            saved_files.append(train_json)
        if val_labels:
            save_labels_coco(val_labels, val_files, val_json)
            saved_files.append(val_json)

        dataset_yaml = os.path.join(current_item.dataset_dir, "data.yaml")
        all_classes = sorted(
            {
                lbl["class"]
                for lbls in all_labels.values()
                for lbl in lbls
                if "class" in lbl
            }
        )

        yaml_data = {
            "train": os.path.join(current_item.dataset_dir, "images", "train"),
            "val": os.path.join(current_item.dataset_dir, "images", "val"),
            "nc": len(all_classes),
            "names": all_classes,
        }

        with open(dataset_yaml, "w", encoding="utf-8") as f:
            yaml.dump(yaml_data, f, sort_keys=False, allow_unicode=True)

        saved_files.append(dataset_yaml)
        logger.info(f"Saved dataset COCO JSON and YAML to {current_item.dataset_dir}")

    else:
        os.makedirs(save_folder, exist_ok=True)
        json_path = os.path.join(save_folder, "annotations.json")
        files = [
            {"path": path, "size": lbls[0].get("img_size", (0, 0))}
            for path, lbls in all_labels.items()
        ]

        save_labels_coco(all_labels, files, json_path)
        saved_files.append(json_path)
        logger.info(f"Saved COCO JSON to {json_path}")

    return saved_files


# --- Load COCO labels ---
def load_labels_coco(path_or_json, available_images=None):
    mapped_labels = {}

    if os.path.isfile(path_or_json) and path_or_json.lower().endswith(".json"):
        with open(path_or_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Loaded COCO JSON from {path_or_json}")
        return _map_coco_labels(data, available_images)

    elif os.path.isdir(path_or_json):
        labels_root = os.path.join(path_or_json, "labels")
        if not os.path.exists(labels_root):
            labels_root = path_or_json

        json_paths = []
        for subset in ["train", "val"]:
            subset_json = os.path.join(labels_root, f"instances_{subset}.json")
            if os.path.exists(subset_json):
                json_paths.append(subset_json)

        if not json_paths:
            for fname in os.listdir(labels_root):
                if fname.lower().endswith(".json"):
                    json_paths.append(os.path.join(labels_root, fname))

        for jp in json_paths:
            with open(jp, "r", encoding="utf-8") as f:
                data = json.load(f)
            mapped_labels.update(_map_coco_labels(data, available_images))
            logger.info(f"Loaded COCO JSON from {jp}")

        return mapped_labels

    else:
        logger.warning(f"No COCO JSON found at {path_or_json}")
        return {}


# --- Map COCO annotations to image paths ---
def _map_coco_labels(coco_data, available_images):
    id_to_img = {img["id"]: img for img in coco_data.get("images", [])}
    valid_image_names = (
        {os.path.basename(p["path"]): p["path"] for p in available_images}
        if available_images
        else {img["file_name"]: img["file_name"] for img in coco_data.get("images", [])}
    )

    mapped_labels = {}

    for ann in coco_data.get("annotations", []):
        img_info = id_to_img.get(ann["image_id"])
        if not img_info:
            continue

        filename = img_info["file_name"]
        if filename not in valid_image_names:
            continue

        img_path = valid_image_names[filename]
        width, height = img_info.get("width", 0), img_info.get("height", 0)

        x, y, w, h = ann.get("bbox", [0, 0, 0, 0])
        label_type = "rect"
        coords = [(x, y), (x + w, y + h)]

        seg = ann.get("segmentation")
        if seg and isinstance(seg, list) and len(seg) > 0:
            poly = seg[0]
            if len(poly) >= 6:
                coords = [[poly[i], poly[i + 1]] for i in range(0, len(poly), 2)]
                label_type = "polygon"

        label_dict = {
            "id": ann["id"],
            "class": ann.get("category_id", -1),
            "type": label_type,
            "coords": coords,
            "img_size": (width, height),
        }

        mapped_labels.setdefault(img_path, []).append(label_dict)

    logger.info(f"Mapped {len(mapped_labels)} images from COCO data")
    return mapped_labels
