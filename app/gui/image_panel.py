from PyQt5.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsPolygonItem,
    QPushButton,
)
from PyQt5.QtGui import QPixmap, QPen, QBrush, QPolygonF, QColor
from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSignal
from app.items.annotator_items import RectItem, PolygonItem
from typing import Optional, Callable, List, Tuple


# --- ImagePanel: main annotation canvas ---
class ImagePanel(QGraphicsView):
    """Interactive image view for drawing and editing annotations."""

    labelAdded = pyqtSignal(str, int, str, list)  # file, class_id, type, coords
    labelRemoved = pyqtSignal(str, int)  # file, label_id
    labelChanged = pyqtSignal(str, int, list)  # file, label_id, coords
    rectangleDrawRequested = pyqtSignal()

    def __init__(self, color_callback: Callable[[int], QColor]):
        super().__init__()
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self.get_class_color: Callable[[int], QColor] = color_callback
        self.pixmap_item: Optional[QGraphicsPixmapItem] = None

        # --- Interaction state ---
        self.current_zoom: float = 1.0
        self.is_drawing: bool = False
        self.label_type: Optional[str] = None
        self.selected_class: Optional[int] = None
        self.current_file: str
        self.current_point: Optional[Tuple[float, float]] = None
        self.current_point_end: Optional[Tuple[float, float]] = None
        self.polygon_points: List[QPointF] = []
        self.img_rect: QRectF
        self.temp_rect: Optional[QGraphicsRectItem] = None
        self.temp_polygon: Optional[QGraphicsPolygonItem] = None

        # --- Crosshair lines ---
        self.crosshair_h: Optional[QGraphicsRectItem] = None
        self.crosshair_v: Optional[QGraphicsRectItem] = None

        self.setMouseTracking(True)
        self.delete_button = QPushButton("×", self.viewport())
        self.delete_button.setFixedSize(26, 26)
        self.delete_button.setToolTip("Remove this label")
        self.delete_button.setStyleSheet(
            "background: #b3261e; color: white; font-size: 20px; font-weight: bold;"
        )
        self.delete_button.hide()
        self.delete_button.clicked.connect(self.delete_selected_items)
        self._scene.selectionChanged.connect(self.update_delete_button)
        self.horizontalScrollBar().valueChanged.connect(self.update_delete_button)
        self.verticalScrollBar().valueChanged.connect(self.update_delete_button)
        # self.setDragMode(QGraphicsView.ScrollHandDrag)

    # --- Image loading ---
    def load_image(self, file_path: str) -> None:
        """Load and display image on scene."""
        pixmap = QPixmap(file_path)
        self._scene.clear()
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self._scene.addItem(self.pixmap_item)
        self.setSceneRect(QRectF(pixmap.rect()))
        self.current_file = file_path
        self.img_rect = QRectF(0, 0, pixmap.width(), pixmap.height())
        self.reset_drawing_state()

        # --- Fit image to window ---
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.current_zoom = 1.0

        # --- Zoom handling ---

    def wheelEvent(self, event):
        """Zoom in/out with mouse wheel."""
        if event.angleDelta().y() > 0:
            self.zoom(1.25)
        else:
            self.zoom(0.8)

    def zoom(self, factor: float) -> None:
        """Apply zoom with scaling limit."""
        new_zoom = self.current_zoom * factor
        if 0.1 <= new_zoom <= 10:
            self.scale(factor, factor)
            self.current_zoom = new_zoom
            self.update_delete_button()

    def reset_zoom(self) -> None:
        """Reset zoom to fit image."""
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.current_zoom = 1.0
        self.update_delete_button()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_delete_button()

    def selected_annotations(self):
        annotations = []
        for item in self._scene.selectedItems():
            while item is not None and not isinstance(item, (RectItem, PolygonItem)):
                item = item.parentItem()
            if item is not None and item not in annotations:
                annotations.append(item)
        return annotations

    def update_delete_button(self):
        annotations = self.selected_annotations()
        if len(annotations) != 1:
            self.delete_button.hide()
            return
        corner = self.mapFromScene(annotations[0].sceneBoundingRect().topRight())
        self.delete_button.move(
            max(
                0, min(corner.x(), self.viewport().width() - self.delete_button.width())
            ),
            max(
                0,
                min(
                    corner.y() - self.delete_button.height(),
                    self.viewport().height() - self.delete_button.height(),
                ),
            ),
        )
        self.delete_button.show()
        self.delete_button.raise_()

    # --- State reset ---
    def reset_drawing_state(self) -> None:
        """Clear temporary shapes and drawing state."""
        if self.temp_rect:
            try:
                self._scene.removeItem(self.temp_rect)
            except RuntimeError:
                pass
            self.temp_rect = None

        if self.temp_polygon:
            try:
                self._scene.removeItem(self.temp_polygon)
            except RuntimeError:
                pass
            self.temp_polygon = None

        self.polygon_points.clear()
        self.current_point = None
        self.current_point_end = None
        self.is_drawing = False

    # --- Drawing setup ---
    def draw_label(
        self, label_type: Optional[str], selected_class: Optional[int]
    ) -> None:
        """Prepare to draw a new annotation."""
        self.is_drawing = True
        self.label_type = label_type
        self.selected_class = selected_class

    # --- Mouse events ---
    def mouseDoubleClickEvent(self, event):
        if not self.is_drawing and event.button() == Qt.LeftButton:
            item = self.itemAt(event.pos())
            while item is not None and not isinstance(item, (RectItem, PolygonItem)):
                item = item.parentItem()
            if item is not None:
                file_path, label_id = item.file_path, item.label_id
                self._scene.removeItem(item)
                self.labelRemoved.emit(file_path, label_id)
                event.accept()
                return
            if self.pixmap_item is not None and self.img_rect.contains(
                self.mapToScene(event.pos())
            ):
                self.rectangleDrawRequested.emit()
                event.accept()
                return
        super().mouseDoubleClickEvent(event)

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
            self._scene.addItem(self.temp_rect)

        # --- Draw polygon ---
        elif self.label_type == "polygon":
            if event.button() == Qt.LeftButton:
                self.polygon_points.append(pos)
                if len(self.polygon_points) == 1:
                    self.temp_polygon = QGraphicsPolygonItem()
                    self.temp_polygon.setPen(QPen(Qt.red, 2))
                    self.temp_polygon.setBrush(QBrush(QColor(255, 0, 0, 50)))
                    self._scene.addItem(self.temp_polygon)
                else:
                    polygon = QPolygonF(self.polygon_points)
                    self.temp_polygon.setPolygon(polygon)
            elif event.button() == Qt.RightButton and self.temp_polygon:
                if len(self.polygon_points) > 2:
                    coords = [(p.x(), p.y()) for p in self.polygon_points]
                    self.labelAdded.emit(
                        self.current_file, self.selected_class, self.label_type, coords
                    )
                self._scene.removeItem(self.temp_polygon)
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
                self.crosshair_h = self._scene.addLine(0, pos.y(), 99999, pos.y(), pen)
                self.crosshair_v = self._scene.addLine(pos.x(), 0, pos.x(), 99999, pen)
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
            and self.temp_rect is not None
        ):
            if event.button() == Qt.LeftButton:
                pos = self.mapToScene(event.pos())
                self.current_point_end = (pos.x(), pos.y())
                coords = [self.current_point, self.current_point_end]
                self.labelAdded.emit(
                    self.current_file, self.selected_class, self.label_type, coords
                )
                self._scene.removeItem(self.temp_rect)
                self.temp_rect = None
                self.is_drawing = False
                self.clear_crosshair()
        else:
            super().mouseReleaseEvent(event)

    # --- Label management ---
    def on_label_change(self, file_path, label_id, coords):
        self.labelChanged.emit(file_path, label_id, coords)

    def update_labels(self, labels: List[dict]) -> None:
        """Redraw all annotation items for current image."""
        for item in self._scene.items():
            if isinstance(item, (RectItem, PolygonItem)):
                self._scene.removeItem(item)

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
                self._scene.addItem(rect)
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
                self._scene.addItem(poly)

    def delete_selected_items(self):
        """Delete selected annotations from scene."""
        annotations = self.selected_annotations()
        targets = [(item.file_path, item.label_id) for item in annotations]
        for item in annotations:
            self._scene.removeItem(item)
        for file_path, label_id in targets:
            self.labelRemoved.emit(file_path, label_id)

    # --- Crosshair helper ---
    def clear_crosshair(self):
        """Remove crosshair lines."""
        if self.crosshair_h:
            self._scene.removeItem(self.crosshair_h)
            self.crosshair_h = None
        if self.crosshair_v:
            self._scene.removeItem(self.crosshair_v)
            self.crosshair_v = None
