from PyQt5.QtGui import QColor
from app.core.class_color_registry import ClassColorRegistry


def test_set_and_get_color():
    registry = ClassColorRegistry()
    registry.set_color("cat", "#00FF00")

    color = registry.get_color("cat")
    assert isinstance(color, QColor)
    assert color.name().lower() == "#00ff00"


def test_auto_generate_color():
    registry = ClassColorRegistry()
    color = registry.get_color("dog")
    assert isinstance(color, QColor)
    assert color.name().startswith("#")


def test_remove_color():
    registry = ClassColorRegistry()
    registry.set_color("0", "#FF00FF")

    registry.remove_color("0")
    assert "0" not in registry.colors


def test_default_color_when_missing():
    registry = ClassColorRegistry()
    default_color = QColor("#123456")
    result = registry.get_color("unknown", default=default_color)
    assert result.name() == default_color.name()
