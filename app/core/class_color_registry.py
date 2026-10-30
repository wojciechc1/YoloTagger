from PyQt5.QtGui import QColor
import random
import zlib
import logging
from typing import Optional, Dict, Union

logger = logging.getLogger(__name__)


class ClassColorRegistry:
    """Registry colors for classes, generates unique random colors if needed."""

    def __init__(self) -> None:
        self.colors: Dict[int, QColor] = {}  # mapping: class_id -> QColor

    def _generate_color(self, class_id: int) -> QColor:
        """Generate a visually distinct, slightly darker color using HSL.

        Derived from class_id so a class keeps the same color between runs.
        """
        try:
            index = int(class_id)
        except (TypeError, ValueError):
            # non-numeric ids (e.g. class names) still need a stable index
            index = zlib.crc32(str(class_id).encode())
        rng = random.Random(index)
        # golden-angle hue steps keep neighbouring class ids far apart
        hue = int((index * 137.508) % 360)
        saturation = rng.randint(180, 255)
        lightness = rng.randint(50, 120)
        color = QColor.fromHsl(hue, saturation, lightness)
        logger.debug(
            "Generated darker color HSL(%d,%d,%d): %s",
            hue,
            saturation,
            lightness,
            color.name(),
        )
        return color

    def set_color(
        self, class_id: int, color: Optional[Union[QColor, str]] = None
    ) -> None:
        """
        Set a color for a class. If no color is provided, generate one automatically.
        Accepts QColor or string (hex code).
        """
        if color is None:
            color = self._generate_color(class_id)
            logger.info("Auto-assigned color %s to class %s", color.name(), class_id)
        elif isinstance(color, str):
            color = QColor(color)
            logger.info("Assigned color %s to class %s", color.name(), class_id)
        else:
            logger.info("Assigned QColor %s to class %s", color.name(), class_id)
        self.colors[class_id] = color

    def get_color(self, class_id: int, default: Optional[QColor] = None) -> QColor:
        """
        Get the QColor for a class. If not set, generate one automatically.
        Returns default (QColor) if generation fails.
        """
        if class_id not in self.colors:
            if default:
                self.colors[class_id] = default
                logger.debug(
                    "Assigned default color %s to class %s", default.name(), class_id
                )
            else:
                self.set_color(class_id)
        return self.colors[class_id]

    def remove_color(self, class_id: int) -> None:
        """Remove the color assigned to a class."""
        if class_id in self.colors:
            removed = self.colors.pop(class_id)
            logger.info("Removed color %s for class %s", removed.name(), class_id)
