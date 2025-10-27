from PyQt5.QtWidgets import (
    QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsItem, QGraphicsPolygonItem
)
from PyQt5.QtGui import QPen, QBrush, QPolygonF, QColor
from PyQt5.QtCore import Qt, QRectF, pyqtSignal, QPointF


# --- Handle (draggable corner/point) ---
class Handle(QGraphicsEllipseItem):
    """Small draggable handle for resizing or shaping items."""
    moved = pyqtSignal()  # emitted when handle is moved

    def __init__(self, x, y, radius=5, class_color=Qt.blue, parent=None):
        self.base_radius = float(radius)

        # create ellipse centered at (0,0) in local coords
        super().__init__(-self.base_radius, -self.base_radius,
                         self.base_radius * 2, self.base_radius * 2, parent)
        self.setPos(x, y)
        self.setBrush(QBrush(class_color))
        self.setPen(QPen(Qt.black))
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemSendsGeometryChanges |
            QGraphicsItem.ItemIsSelectable
        )

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            parent = self.parentItem()
            if parent and hasattr(parent, "img_rect"):
                # Keep handle inside image boundaries
                new_scene_pos = parent.mapToScene(value)
                x = max(parent.img_rect.left(), min(new_scene_pos.x(), parent.img_rect.right()))
                y = max(parent.img_rect.top(), min(new_scene_pos.y(), parent.img_rect.bottom()))
                value = parent.mapFromScene(QPointF(x, y))

            # Notify parent about movement
            if parent and hasattr(parent, "handle_moved"):
                parent.handle_moved()

            return value
        return super().itemChange(change, value)

    # scale radius to zoom
    def update_size(self, zoom):
        try:
            z = float(zoom) if zoom and zoom > 0 else 1.0
        except Exception:
            z = 1.0

        r = max(3.0, (self.base_radius * 10) / z)
        self.setRect(-r, -r, 2 * r, 2 * r)


# --- RectItem (bounding box with 2 handles) ---
class RectItem(QGraphicsRectItem):
    """Rectangle annotation with draggable handles."""
    updated = pyqtSignal(str, int, list)

    def __init__(self, coords, label_id, class_id, file_path, img_rect,
                 change_callback=None, get_color_callback=None, parent=None):
        super().__init__(parent)
        self.label_id = label_id
        self.class_id = class_id
        self.file_path = file_path
        self.img_rect = img_rect
        self.change_callback = change_callback
        self.get_color_callback = get_color_callback

        self.setPen(QPen(Qt.red, 2))
        self.setBrush(QBrush(Qt.transparent))
        self.setFlags(
            QGraphicsRectItem.ItemIsSelectable |
            QGraphicsRectItem.ItemIsMovable |
            QGraphicsRectItem.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)

        color = self.get_color_callback(self.class_id)

        # Create two handles
        self.start_handle = Handle(coords[0][0], coords[0][1], class_color=color, parent=self)
        self.end_handle = Handle(coords[1][0], coords[1][1], class_color=color, parent=self)

        self.update_rect()

    def paint(self, painter, option, widget=None):
        zoom = getattr(self.scene(), "zoom_factor", 1.0)
        base_color = self.get_color_callback(self.class_id)
        pen_color = QColor(Qt.yellow) if self.isSelected() else QColor(base_color)
        pen = QPen(pen_color,  10 / zoom)

        fill_color = QColor(base_color)
        fill_color.setAlpha(60)
        brush = QBrush(fill_color)

        self.setPen(pen)
        self.setBrush(brush)
        super().paint(painter, option, widget)

        for h in self.start_handle, self.end_handle:
            h.update_size(zoom)

        # --- Label (centered) ---
        label = str(self.class_id)
        font = painter.font()
        font.setPointSizeF(50 / zoom)
        painter.setFont(font)

        rect = self.rect()
        fm = painter.fontMetrics()
        text_w = fm.horizontalAdvance(label) + 10 / zoom
        text_h = fm.height() + 6 / zoom


        bg_x = rect.center().x() - text_w / 2
        bg_y = rect.center().y() - text_h / 2
        bg_rect = QRectF(bg_x, bg_y, text_w, text_h)

        bg_color = QColor(base_color)
        bg_color.setAlpha(220)
        painter.fillRect(bg_rect, bg_color)

        painter.setPen(Qt.white)
        painter.drawText(bg_rect, Qt.AlignCenter, label)


    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and isinstance(value, QPointF):
            img_rect = getattr(self, "img_rect", None)
            if img_rect:
                rect = self.rect()
                new_x = min(max(value.x(), img_rect.left() - rect.left()), img_rect.right() - rect.right())
                new_y = min(max(value.y(), img_rect.top() - rect.top()), img_rect.bottom() - rect.bottom())
                value = QPointF(new_x, new_y)
                self.update_rect()
                self.on_change()
        return super().itemChange(change, value)

    def on_change(self):
        """Emit updated rectangle coordinates."""
        start_scene = self.mapToScene(self.start_handle.pos())
        end_scene = self.mapToScene(self.end_handle.pos())
        coords = [(start_scene.x(), start_scene.y()), (end_scene.x(), end_scene.y())]
        self.change_callback(self.file_path, self.label_id, coords)

    def handle_moved(self):
        """Called when a handle moves."""
        self.update_rect()
        self.on_change()

    def update_rect(self):
        """Recalculate rectangle based on handle positions."""
        x1, y1 = self.start_handle.pos().x(), self.start_handle.pos().y()
        x2, y2 = self.end_handle.pos().x(), self.end_handle.pos().y()
        rect = QRectF(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
        self.setRect(rect)


# --- PolygonItem (multi-point shape) ---
class PolygonItem(QGraphicsPolygonItem):
    """Polygon annotation with multiple draggable handles."""

    def __init__(self, points, label_id, class_id, file_path, img_rect,
                 change_callback=None, get_color_callback=None, parent=None):
        super().__init__(parent)
        self.label_id = label_id
        self.class_id = class_id
        self.file_path = file_path
        self.img_rect = img_rect
        self.get_color = get_color_callback
        self.change_callback = change_callback

        self.setPen(QPen(Qt.red, 2))
        self.setBrush(QBrush(Qt.transparent))
        self.setFlags(
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)

        color = self.get_color(self.class_id)
        # Create handles for polygon points
        self.handles = [Handle(pt[0], pt[1], class_color=color, parent=self) for pt in points]
        self.update_polygon()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and isinstance(value, QPointF):
            img_rect = getattr(self, "img_rect", None)
            if img_rect:
                min_x = min(h.pos().x() for h in self.handles)
                max_x = max(h.pos().x() for h in self.handles)
                min_y = min(h.pos().y() for h in self.handles)
                max_y = max(h.pos().y() for h in self.handles)

                # Keep polygon within image bounds
                new_x = min(max(value.x(), img_rect.left() - min_x), img_rect.right() - max_x)
                new_y = min(max(value.y(), img_rect.top() - min_y), img_rect.bottom() - max_y)
                value = QPointF(new_x, new_y)
                self.on_change()
        return super().itemChange(change, value)

    def handle_moved(self):
        """Called when a handle is moved."""
        self.update_polygon()
        self.on_change()

    def update_polygon(self):
        """Rebuild polygon from handle positions."""
        polygon = QPolygonF([h.pos() for h in self.handles])
        self.setPolygon(polygon)

    def on_change(self):
        """Emit updated polygon coordinates."""
        coords = [(self.mapToScene(h.pos()).x(), self.mapToScene(h.pos()).y()) for h in self.handles]
        self.change_callback(self.file_path, self.label_id, coords)

    def paint(self, painter, option, widget=None):
        zoom = getattr(self.scene(), "zoom_factor", 1.0)

        base_color = self.get_color(self.class_id)
        pen_color = QColor(Qt.yellow) if self.isSelected() else QColor(base_color)
        pen = QPen(pen_color, 10 / zoom)

        fill_color = QColor(base_color)
        fill_color.setAlpha(60)
        brush = QBrush(fill_color)

        self.setPen(pen)
        self.setBrush(brush)
        super().paint(painter, option, widget)

        # --- Update handle sizes ---
        for h in self.handles:
            h.update_size(zoom)

        # --- Label (centered in polygon) ---
        label = str(self.class_id)
        font = painter.font()
        font.setPointSizeF(50 / zoom)
        painter.setFont(font)

        fm = painter.fontMetrics()
        text_w = fm.horizontalAdvance(label) + 10 / zoom
        text_h = fm.height() + 6 / zoom

        rect = self.boundingRect()
        bg_x = rect.center().x() - text_w / 2
        bg_y = rect.center().y() - text_h / 2
        bg_rect = QRectF(bg_x, bg_y, text_w, text_h)

        bg_color = QColor(base_color)
        bg_color.setAlpha(220)
        painter.fillRect(bg_rect, bg_color)

        painter.setPen(Qt.white)
        painter.drawText(bg_rect, Qt.AlignCenter, label)

