import logging
from typing import Optional, Any, TYPE_CHECKING

logger = logging.getLogger(__name__)

# During type checking (e.g. mypy/CI), import only for hints — not at runtime.
# At runtime, try importing normally; fallback to Any if unavailable.
if TYPE_CHECKING:
    from ultralytics import YOLO as YOLOModel
else:
    try:
        from ultralytics import YOLO as YOLOModel
    except ImportError:
        YOLOModel: Any = None
        logger.warning("Ultralytics YOLO not available - using dummy mode.")


class ModelHandler:
    def __init__(self):
        self.model: Optional[Any] = None

    def load_model(self, path: str):
        """Load YOLO model and return unique classes as {id: name}."""
        if YOLOModel is None:
            raise ImportError("Ultralytics YOLO not available")
        self.model = YOLOModel(path)
        return {i: name for i, name in self.model.names.items()}

    def predict(self, image_path: str, conf: float = 0.3):
        if self.model is None:
            raise ValueError("Model not loaded")

        results = self.model.predict(image_path, conf=conf)
        predictions = []

        for r in results:
            for i, box in enumerate(r.boxes.xyxy.cpu().numpy()):
                x1, y1, x2, y2 = box
                class_id = int(r.boxes.cls[i])
                predictions.append({"bbox": [(x1, y1), (x2, y2)], "class_id": class_id})

            if getattr(r, "masks", None) is not None:
                for i, mask in enumerate(r.masks.xy):
                    class_id = int(r.boxes.cls[i])
                    predictions.append({"mask": mask, "class_id": class_id})

        return predictions
