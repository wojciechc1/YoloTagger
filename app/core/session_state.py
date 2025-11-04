import logging
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class SessionState(QObject):
    # --- Signals ---
    label_mode_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._label_mode = None
        self._save_format = None
        self._save_path = None
        self._current_class = None
        self.files = []  # list of dataset files
        self.current_index = 0  # current file index

    # --- Label mode ---
    @property
    def label_mode(self):
        return self._label_mode

    @label_mode.setter
    def label_mode(self, value):
        if value != self._label_mode:
            self._label_mode = value
            self.label_mode_changed.emit(value)
            logger.info("Label mode changed to: %s", value)

    # --- Save format ---
    @property
    def save_format(self):
        return self._save_format

    @save_format.setter
    def save_format(self, value):
        if value != self._save_format:
            self._save_format = value
            logger.info("Save format changed to: %s", value)

    # --- Save path ---
    @property
    def save_path(self):
        return self._save_path

    @save_path.setter
    def save_path(self, value):
        if value != self._save_path:
            self._save_path = value
            logger.info("Save path changed to: %s", value)

    # --- Current class ---
    @property
    def current_class(self):
        return self._current_class

    @current_class.setter
    def current_class(self, value):
        if value != self._current_class:
            self._current_class = value
            logger.info("Current class changed to: %s", value)
