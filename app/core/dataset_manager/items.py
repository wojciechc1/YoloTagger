import os
import logging
from PIL import Image

logger = logging.getLogger(__name__)

# --- Single image file ---
class FileItem:
    def __init__(self, path, exts=(".jpg", ".jpeg", ".png")):
        self.path = os.path.normpath(path)
        self._img_size = None
        self.exts = exts
        self.labeled = False

    @property
    def img_size(self):
        # lazy-load image size
        if self._img_size is None:
            try:
                with Image.open(self.path) as img:
                    self._img_size = img.size  # (width, height)
            except Exception as e:
                logger.error("Failed to load image size for %s: %s", self.path, e)
                self._img_size = (0, 0)
        return self._img_size


# --- Folder with images ---
class FolderItem:
    def __init__(self, folder_path, exts=(".jpg", ".jpeg", ".png")):
        self.folder_path = os.path.normpath(folder_path)
        self.exts = exts
        self.files = []
        try:
            for f in os.listdir(folder_path):
                if f.lower().endswith(exts):
                    self.files.append(FileItem(os.path.join(folder_path, f)))
        except Exception as e:
            logger.error("Failed to load folder %s: %s", folder_path, e)


# --- Dataset with train/val splits ---
class DatasetItem:
    def __init__(self, dataset_dir, exts=(".jpg", ".jpeg", ".png")):
        self.dataset_dir = os.path.normpath(dataset_dir)
        self.train, self.val = [], []
        self._load_dataset(exts)

    def _load_dataset(self, exts):
        # load images from images/train and images/val
        for subset in ["train", "val"]:
            img_dir = os.path.join(self.dataset_dir, "images", subset)
            if os.path.exists(img_dir):
                try:
                    files = [
                        FileItem(os.path.join(img_dir, f))
                        for f in os.listdir(img_dir)
                        if f.lower().endswith(exts)
                    ]
                    setattr(self, subset, files)
                    logger.info("Loaded %d images for %s subset", len(files), subset)
                except Exception as e:
                    logger.error("Failed to load images from %s: %s", img_dir, e)
