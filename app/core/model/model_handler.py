import logging
logger = logging.getLogger(__name__)

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None
    logger.warning("Ultralytics YOLO not available - using dummy mode.")


class ModelHandler:
    def __init__(self):
        self.model = None

    def load_model(self, path):
        """Load YOLO model and return unique classes as {id: name}."""
        self.model = YOLO(path)
        return {i: name for i, name in self.model.names.items()}

    def predict(self, image_path, conf=0.3):
        if self.model is None:
            raise ValueError("Model not loaded")

        results = self.model.predict(image_path, conf=conf)
        predictions = []

        for r in results:
            # bounding boxes
            for i, box in enumerate(r.boxes.xyxy.cpu().numpy()):
                x1, y1, x2, y2 = box
                class_id = int(r.boxes.cls[i])
                predictions.append({"bbox": [(x1, y1), (x2, y2)], "class_id": class_id})

            # masks
            if getattr(r, "masks", None) is not None:
                for i, mask in enumerate(r.masks.xy):
                    class_id = int(r.boxes.cls[i])
                    predictions.append({"mask": mask, "class_id": class_id})

        return predictions
