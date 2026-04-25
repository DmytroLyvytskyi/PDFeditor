import math
import os
from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import QPixmap, QPainter, QTransform
from PySide6.QtWidgets import QLabel, QMenu


class DraggableImage(QLabel):
    selected = Signal(object)
    moved = Signal(object)

    def __init__(self, path, x, y, w, h, overlay=True, on_delete=None, parent=None):
        super().__init__(parent)
        self.image_path = path
        self._original_path = path
        self.overlay = overlay
        self.on_delete = on_delete
        self.rotation = 0

        self._base_w = w
        self._base_h = h
        self._aspect = w / h if h > 0 else 1.0
        self._pixmap_original = QPixmap(path)
        self._updating = False

        self._drag = False
        self._resize = False
        self._drag_offset = QPoint(0, 0)
        self._resize_start = QPoint(0, 0)
        self._resize_start_w = w
        self._resize_start_h = h

        self.setMouseTracking(True)
        self.setAutoFillBackground(False)
        self.move(x, y)
        self.resize(w, h)
        self.show()

    def _update_size_for_rotation(self):
        if self._updating:
            return
        self._updating = True
        angle_rad = math.radians(self.rotation)
        cos_a = abs(math.cos(angle_rad))
        sin_a = abs(math.sin(angle_rad))
        new_w = int(self._base_w * cos_a + self._base_h * sin_a)
        new_h = int(self._base_w * sin_a + self._base_h * cos_a)
        cx = self.x() + self.width() // 2
        cy = self.y() + self.height() // 2
        self.resize(new_w, new_h)
        self.move(cx - new_w // 2, cy - new_h // 2)
        self._updating = False

    def rotate_cw(self):
        self.rotation = (self.rotation + 15) % 360
        self._update_size_for_rotation()
        self.update()

    def rotate_ccw(self):
        self.rotation = (self.rotation - 15) % 360
        self._update_size_for_rotation()
        self.update()

    def deselect(self):
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        pix = self._pixmap_original.scaled(
            self._base_w, self._base_h,
            Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

        if self.rotation % 360 == 0:
            painter.drawPixmap(0, 0, pix)
        else:
            t = QTransform()
            t.translate(self.width() / 2, self.height() / 2)
            t.rotate(self.rotation)
            t.translate(-self._base_w / 2, -self._base_h / 2)
            painter.setTransform(t)
            painter.drawPixmap(0, 0, pix)
            painter.resetTransform()

        painter.setPen(Qt.darkGray)
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)
        painter.fillRect(self.width() - 12, self.height() - 12, 12, 12, Qt.darkGray)
        painter.end()

    def _in_handle(self, pos):
        return self.width() - 14 <= pos.x() and self.height() - 14 <= pos.y()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._in_handle(event.pos()):
                self._resize = True
                self._resize_start = event.globalPosition().toPoint()
                self._resize_start_w = self._base_w
                self._resize_start_h = self._base_h
                self._aspect = self._base_w / self._base_h if self._base_h > 0 else 1.0
            else:
                self._drag = True
                self._drag_offset = event.pos()
            self.selected.emit(self)
            event.accept()
            return
        if event.button() == Qt.RightButton:
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag:
            self.move(self.mapToParent(event.pos() - self._drag_offset))
            event.accept()
            return
        if self._resize:
            delta = event.globalPosition().toPoint() - self._resize_start
            d = max(delta.x(), delta.y())
            new_base_w = max(20, self._resize_start_w + d)
            new_base_h = max(20, int(new_base_w / self._aspect))
            self._base_w = new_base_w
            self._base_h = new_base_h
            self._update_size_for_rotation()
            self.update()
            event.accept()
            return
        if self._in_handle(event.pos()):
            self.setCursor(Qt.SizeFDiagCursor)
        else:
            self.setCursor(Qt.SizeAllCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        was_active = self._drag or self._resize
        self._drag = False
        self._resize = False
        self.setCursor(Qt.SizeAllCursor)
        if was_active:
            self.moved.emit(self)
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        before_action = menu.addAction("Before text")
        behind_action = menu.addAction("Behind text")
        menu.addSeparator()
        delete_action = menu.addAction("Delete")
        before_action.setCheckable(True)
        behind_action.setCheckable(True)
        before_action.setChecked(self.overlay)
        behind_action.setChecked(not self.overlay)
        action = menu.exec(event.globalPos())
        if action == before_action:
            self.overlay = True
        elif action == behind_action:
            self.overlay = False
        elif action == delete_action:
            if self.on_delete:
                self.on_delete(self)
            self.deleteLater()