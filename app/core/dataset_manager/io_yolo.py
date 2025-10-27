import os
import logging
from .items import DatasetItem
from PIL import Image

logger = logging.getLogger(__name__)

# --- Convert all rect labels to YOLO format ---
def get_all_yolo_labels(files, labels):
    """
    Return {file_path: [YOLO lines]} for all files.
    Uses img_size from files if available.
    """
    img_sizes = {f["path"]: f.get("size") for f in files}
    all_labels = {}

    for file_path, img_labels in labels.items():
        yolo_lines = []
        img_w, img_h = img_sizes.get(file_path, (1, 1))

        for label in img_labels:
            if label.get("type") != "rect" or not label.get("coords"):
                continue
            class_id = label["class"]
            (x1, y1), (x2, y2) = label["coords"]
            x_center = (x1 + x2) / 2 / img_w
            y_center = (y1 + y2) / 2 / img_h
            width = abs(x2 - x1) / img_w
            height = abs(y2 - y1) / img_h
            yolo_lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

        all_labels[file_path] = yolo_lines

    logger.info(f"Converted {len(all_labels)} images to YOLO format")
    return all_labels


# --- Save single YOLO .txt ---
def save_yolo_labels(file_path, yolo_lines, export_folder):
    """
    Save single YOLO .txt file.
    """
    os.makedirs(export_folder, exist_ok=True)
    name = os.path.splitext(os.path.basename(file_path))[0]
    txt_path = os.path.join(export_folder, f"{name}.txt")

    with open(txt_path, "w") as f:
        f.writelines(line + "\n" for line in yolo_lines)

    logger.info(f"Saved YOLO labels for {file_path} to {txt_path}")
    return os.path.abspath(txt_path)


# --- Save all YOLO labels ---
def save_all_yolo(current_item, all_yolo, save_folder):
    """
    Save all YOLO labels for dataset, folder or file.
    """
    saved_files = []

    if isinstance(current_item, DatasetItem):
        train_folder = os.path.join(current_item.dataset_dir, "labels/train")
        val_folder = os.path.join(current_item.dataset_dir, "labels/val")
        os.makedirs(train_folder, exist_ok=True)
        os.makedirs(val_folder, exist_ok=True)

        for file_path, lines in all_yolo.items():
            if not lines:
                continue
            if any(f.path == file_path for f in current_item.train):
                saved_files.append(save_yolo_labels(file_path, lines, train_folder))
            elif any(f.path == file_path for f in current_item.val):
                saved_files.append(save_yolo_labels(file_path, lines, val_folder))
    else:
        folder = save_folder or os.path.dirname(list(all_yolo.keys())[0])
        os.makedirs(folder, exist_ok=True)
        for file_path, lines in all_yolo.items():
            if not lines:
                continue
            saved_files.append(save_yolo_labels(file_path, lines, folder))

    logger.info(f"Saved YOLO labels for {len(saved_files)} files")
    return saved_files


# --- Save YOLO data.yaml ---
def save_yaml_yolo(current_item, unique_classes):
    """
    Create data.yaml for YOLO dataset.
    """
    if not isinstance(current_item, DatasetItem):
        return None

    yaml_path = os.path.join(current_item.dataset_dir, "data.yaml")
    train_path = os.path.join(current_item.dataset_dir, "images/train").replace("\\", "/")
    val_path = os.path.join(current_item.dataset_dir, "images/val").replace("\\", "/")
    names_yaml = "\n  - ".join([name for key, name in sorted(unique_classes.items())])

    yaml_content = f"train: {train_path}\nval: {val_path}\nnc: {len(unique_classes)}\nnames:\n  - {names_yaml}\n"

    with open(yaml_path, "w") as f:
        f.write(yaml_content)

    logger.info(f"Created YOLO data.yaml at {yaml_path}")
    return yaml_path


# --- Load single YOLO file ---
def load_yolo_file_dict(txt_path, img_path, img_size=None):
    """
    Load YOLO labels from .txt file.
    """
    labels = []
    if not os.path.exists(txt_path):
        return labels

    if img_size is None:
        with Image.open(img_path) as img:
            img_size = img.size

    img_w, img_h = img_size

    with open(txt_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) != 5:
                continue
            class_id, x_center, y_center, w, h = map(float, parts)
            class_id = int(class_id)
            x1 = (x_center - w / 2) * img_w
            y1 = (y_center - h / 2) * img_h
            x2 = (x_center + w / 2) * img_w
            y2 = (y_center + h / 2) * img_h
            labels.append({
                "id": 0,
                "class": class_id,
                "type": "rect",
                "coords": [(x1, y1), (x2, y2)],
                "img_size": (img_w, img_h)
            })
    return labels


# --- Load YOLO labels automatically ---
def load_yolo_labels_auto(base_path, all_files, unique_classes=None):
    """
    Auto-load YOLO labels for images in all_files.
    """
    mapped_labels = {}

    # find label folders
    label_dirs = []
    if os.path.isdir(base_path) and any(f.lower().endswith(".txt") for f in os.listdir(base_path)):
        label_dirs = [base_path]
    elif os.path.exists(os.path.join(base_path, "labels")):
        labels_root = os.path.join(base_path, "labels")
        train_dir = os.path.join(labels_root, "train")
        val_dir = os.path.join(labels_root, "val")
        if os.path.exists(train_dir):
            label_dirs.append(train_dir)
        if os.path.exists(val_dir):
            label_dirs.append(val_dir)
        if not label_dirs and any(f.lower().endswith(".txt") for f in os.listdir(labels_root)):
            label_dirs.append(labels_root)

    if not label_dirs:
        logger.warning("No label folders found at '%s'", base_path)
        return mapped_labels

    # map image names → txt paths
    label_map = {}
    for ldir in label_dirs:
        for fname in os.listdir(ldir):
            if fname.lower().endswith(".txt"):
                name = os.path.splitext(fname)[0]
                label_map[name] = os.path.join(ldir, fname)

    # match each image with its .txt
    for file_info in all_files:
        img_path = file_info["path"]
        img_size = file_info.get("size")
        img_name = os.path.splitext(os.path.basename(img_path))[0]
        txt_path = label_map.get(img_name)
        if not txt_path or not os.path.exists(txt_path):
            continue
        labels = load_yolo_file_dict(txt_path, img_path, img_size)
        if labels:
            mapped_labels[img_path] = labels

    logger.info(f"Loaded YOLO labels for {len(mapped_labels)} images from '{base_path}'")
    return mapped_labels
