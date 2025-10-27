from PyQt5.QtGui import QColor
import random
import logging

logger = logging.getLogger(__name__)

class ClassColorManager:
    """Manages colors for classes, generates unique random colors if needed."""

    def __init__(self):
        self.colors = {}  # mapping: class_id -> QColor

    def _generate_color(self) -> QColor:
        """Generate a visually distinct, slightly darker color using HSL."""
        h = random.randint(0, 359)
        s = random.randint(180, 255)
        l = random.randint(50, 120)
        color = QColor.fromHsl(h, s, l)
        logger.debug("Generated darker color HSL(%d,%d,%d): %s", h, s, l, color.name())
        return color

    def set_color(self, class_id, color=None):
        """
        Set a color for a class. If no color is provided, generate one automatically.
        Accepts QColor or string (hex code).
        """
        if color is None:
            color = self._generate_color()
            logger.info("Auto-assigned color %s to class %s", color.name(), class_id)
        elif isinstance(color, str):
            color = QColor(color)
            logger.info("Assigned color %s to class %s", color.name(), class_id)
        else:
            logger.info("Assigned QColor %s to class %s", color.name(), class_id)
        self.colors[class_id] = color

    def get_color(self, class_id, default=None) -> QColor:
        """
        Get the QColor for a class. If not set, generate one automatically.
        Returns default (QColor) if generation fails.
        """
        if class_id not in self.colors:
            logger.debug("No color found for class %s, generating...", class_id)
            self.set_color(class_id)
        return self.colors.get(class_id, default or QColor("#FF0000"))

    def remove_color(self, class_id):
        """Remove the color assigned to a class."""
        if class_id in self.colors:
            removed = self.colors.pop(class_id)
            logger.info("Removed color %s for class %s", removed.name(), class_id)
