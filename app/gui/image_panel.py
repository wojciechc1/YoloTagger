from PyQt5.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsPolygonItem,
)
from PyQt5.QtGui import QPixmap, QPen, QBrush, QPolygonF, QColor
from PyQt5.QtCore import Qt, QRectF, pyqtSignal
from app.items.annotator_items import RectItem, PolygonItem


# --- ImagePanel: main annotation canvas ---
class ImagePanel(QGraphicsView):
    """Interactive image view for drawing and editing annotations."""

    labelAdded = pyqtSignal(str, int, str, list)  # file, class_id, type, coords
    labelRemoved = pyqtSignal(str, int)  # file, label_id
    labelChanged = pyqtSignal(str, int, list)  # file, label_id, coords

    def __init__(self, color_callback):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.get_class_color = color_callback
        self.pixmap_item = None

        # --- Interaction state ---
        self.current_zoom = 1.0
        self.is_drawing = False
        self.label_type = None
        self.selected_class = None
        self.current_file = None
        self.current_point = None
        self.current_point_end = None
        self.temp_rect = None
        self.temp_polygon = None
        self.polygon_points = []
        self.img_rect = None

        # --- Crosshair lines ---
        self.crosshair_h = None
        self.crosshair_v = None

        self.setMouseTracking(True)
        # self.setDragMode(QGraphicsView.ScrollHandDrag)

    # --- Image loading ---
    def load_image(self, file_path):
        """Load and display image on scene."""
        pixmap = QPixmap(file_path)
        self.scene.clear()
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)
        self.setSceneRect(QRectF(pixmap.rect()))
        self.current_file = file_path
        self.img_rect = QRectF(0, 0, pixmap.width(), pixmap.height())
        self.reset_drawing_state()

        # --- Fit image to window ---
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
        self.current_zoom = 1.0

        # --- Zoom handling ---

    def wheelEvent(self, event):
        """Zoom in/out with mouse wheel."""
        if event.angleDelta().y() > 0:
            self.zoom(1.25)
        else:
            self.zoom(0.8)

    def zoom(self, factor: float):
        """Apply zoom with scaling limit."""
        new_zoom = self.current_zoom * factor
        if 0.1 <= new_zoom <= 10:
            self.scale(factor, factor)
            self.current_zoom = new_zoom

    def reset_zoom(self):
        """Reset zoom to fit image."""
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
        self.current_zoom = 1.0

    # --- State reset ---
    def reset_drawing_state(self):
        """Clear temporary shapes and drawing state."""
        if self.temp_rect:
            try:
                self.scene.removeItem(self.temp_rect)
            except RuntimeError:
                pass
            self.temp_rect = None

        if self.temp_polygon:
            try:
                self.scene.removeItem(self.temp_polygon)
            except RuntimeError:
                pass
            self.temp_polygon = None

        self.polygon_points.clear()
        self.current_point = None
        self.current_point_end = None
        self.is_drawing = False

    # --- Drawing setup ---
    def draw_label(self, label_type, selected_class):
        """Prepare to draw a new annotation."""
        self.is_drawing = True
        self.label_type = label_type
        self.selected_class = selected_class

    # --- Mouse events ---
    def mousePressEvent(self, event):
        if not self.is_drawing:
            super().mousePressEvent(event)
            return

        if self.selected_class is None:
            print("Select a class before drawing.")
            return

        pos = self.mapToScene(event.pos())

        # --- Draw rectangle ---
        if self.label_type == "rect" and event.button() == Qt.LeftButton:
            self.current_point = (pos.x(), pos.y())
            self.temp_rect = QGraphicsRectItem(0, 0, 0, 0)
            self.temp_rect.setBrush(QBrush(QColor(128, 128, 128, 100)))
            self.temp_rect.setPen(QPen(Qt.red, 1))
            self.scene.addItem(self.temp_rect)

        # --- Draw polygon ---
        elif self.label_type == "polygon":
            if event.button() == Qt.LeftButton:
                self.polygon_points.append(pos)
                if len(self.polygon_points) == 1:
                    self.temp_polygon = QGraphicsPolygonItem()
                    self.temp_polygon.setPen(QPen(Qt.red, 2))
                    self.temp_polygon.setBrush(QBrush(QColor(255, 0, 0, 50)))
                    self.scene.addItem(self.temp_polygon)
                else:
                    polygon = QPolygonF(self.polygon_points)
                    self.temp_polygon.setPolygon(polygon)
            elif event.button() == Qt.RightButton and self.temp_polygon:
                if len(self.polygon_points) > 2:
                    coords = [(p.x(), p.y()) for p in self.polygon_points]
                    self.labelAdded.emit(
                        self.current_file, self.selected_class, self.label_type, coords
                    )
                self.scene.removeItem(self.temp_polygon)
                self.temp_polygon = None
                self.polygon_points.clear()
                self.is_drawing = False
                self.clear_crosshair()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_drawing and self.selected_class is not None:
            pos = self.mapToScene(event.pos())

            # Update crosshair
            if self.crosshair_h is None:
                pen = QPen(Qt.red, 1, Qt.DotLine)
                self.crosshair_h = self.scene.addLine(0, pos.y(), 99999, pos.y(), pen)
                self.crosshair_v = self.scene.addLine(pos.x(), 0, pos.x(), 99999, pen)
            else:
                self.crosshair_h.setLine(-99999, pos.y(), 99999, pos.y())
                self.crosshair_v.setLine(pos.x(), -99999, pos.x(), 99999)

            # Update rectangle preview
            if self.label_type == "rect" and self.temp_rect:
                x1, y1 = self.current_point
                x2, y2 = pos.x(), pos.y()
                rect = QRectF(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
                self.temp_rect.setRect(rect)

            # Update polygon preview
            elif (
                self.label_type == "polygon"
                and self.temp_polygon
                and self.polygon_points
            ):
                preview_points = self.polygon_points + [pos]
                self.temp_polygon.setPolygon(QPolygonF(preview_points))
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if (
            self.is_drawing
            and self.label_type == "rect"
            and self.selected_class is not None
        ):
            if event.button() == Qt.LeftButton:
                pos = self.mapToScene(event.pos())
                self.current_point_end = (pos.x(), pos.y())
                coords = [self.current_point, self.current_point_end]
                self.labelAdded.emit(
                    self.current_file, self.selected_class, self.label_type, coords
                )
                self.scene.removeItem(self.temp_rect)
                self.temp_rect = None
                self.is_drawing = False
                self.clear_crosshair()
        else:
            super().mouseReleaseEvent(event)

    # --- Label management ---
    def on_label_change(self, file_path, label_id, coords):
        self.labelChanged.emit(file_path, label_id, coords)

    def update_labels(self, labels: list):
        """Redraw all annotation items for current image."""
        for item in self.scene.items():
            if isinstance(item, (RectItem, PolygonItem)):
                self.scene.removeItem(item)

        for label in labels:
            if label["type"] == "rect":
                rect = RectItem(
                    label["coords"],
                    label["id"],
                    label["class"],
                    self.current_file,
                    self.img_rect,
                    self.on_label_change,
                    get_color_callback=self.get_class_color,
                )
                self.scene.addItem(rect)
            elif label["type"] == "polygon":
                poly = PolygonItem(
                    label["coords"],
                    label["id"],
                    label["class"],
                    self.current_file,
                    self.img_rect,
                    self.on_label_change,
                    get_color_callback=self.get_class_color,
                )
                self.scene.addItem(poly)

    def delete_selected_items(self):
        """Delete selected annotations from scene."""
        for item in self.scene.selectedItems():
            if isinstance(item, (RectItem, PolygonItem)):
                self.labelRemoved.emit(item.file_path, item.label_id)
                self.scene.removeItem(item)

    # --- Crosshair helper ---
    def clear_crosshair(self):
        """Remove crosshair lines."""
        if self.crosshair_h:
            self.scene.removeItem(self.crosshair_h)
            self.crosshair_h = None
        if self.crosshair_v:
            self.scene.removeItem(self.crosshair_v)
            self.crosshair_v = None
