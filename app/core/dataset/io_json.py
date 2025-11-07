import os
import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


# --- Save labels to JSON ---
def save_labels_json(
    all_labels: Dict[str, List[Dict[str, Any]]], save_path: str
) -> str:
    """
    Save all labels to labels.json.
    Keys: filenames, Classes as ID (int)
    """
    clean_labels = {}

    for path, labels in all_labels.items():
        filename = os.path.basename(path)
        cleaned = []

        for lbl in labels:
            cleaned.append(
                {
                    "id": lbl.get("id", -1),
                    "class": int(lbl.get("class", -1)),  # store class ID
                    "type": lbl.get("type", "rect"),
                    "coords": lbl.get("coords", []),
                    "img_size": lbl.get("img_size", [0, 0]),
                }
            )

        clean_labels[filename] = cleaned

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(clean_labels, f, indent=4, ensure_ascii=False)

    abs_path = os.path.abspath(save_path)
    logger.info(f"Saved JSON labels to {abs_path}")
    return abs_path


# --- Load labels from JSON ---
def load_labels_json(
    json_path: str, available_images: List[str]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Load labels.json and map labels to images by filename.
    Returns class IDs as int.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        label_data: Dict[str, List[Dict[str, Any]]] = json.load(f)

    mapped_labels: Dict[str, List[Dict[str, Any]]] = {}

    for img_path in available_images:
        filename = os.path.basename(img_path)
        if filename in label_data:
            labels: List[Dict[str, Any]] = []
            for lbl in label_data[filename]:
                labels.append(
                    {
                        "id": lbl.get("id", -1),
                        "class": int(lbl.get("class", -1)),  # map as ID
                        "type": lbl.get("type", "rect"),
                        "coords": lbl.get("coords", []),
                        "img_size": lbl.get("img_size", [0, 0]),
                    }
                )
            mapped_labels[img_path] = labels

    logger.info(f"Loaded JSON labels for {len(mapped_labels)} images from {json_path}")
    return mapped_labels
