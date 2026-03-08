from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QSizeGrip

class DraggableImage(QLabel):

    def __init__(self, path, x, y, w, h, parent=None):
        super().__init__(parent)
        self.image_path = path
        self.drag = False
        self.offset = QPoint(0, 0)
        self.min_size = 20

        self.setGeometry(x, y, w, h)
        self.load_pixmap()
        self.handle = QLabel(self)
        self.handle.setFixedSize(12, 12)
        self.handle.setStyleSheet("background-color: #028090; border: 1px solid white;")
        self.handle.drag = False
        self.handle.offset = QPoint(0, 0)
        self.handle.mousePressEvent = self.handle_press
        self.handle.mouseMoveEvent = self.handle_move
        self.handle.mouseReleaseEvent = self.handle_release
        self.place()

        self.setStyleSheet("border: 1px dashed #028090;")
        self.show()

    def load_pixmap(self):
        pix = QPixmap(self.image_path)
        if not pix.isNull():
            self.setPixmap(pix.scaled(self.width(), self.height(), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def place(self):
        self.handle.move(self.width() - 12, self.height() - 12)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.load_pixmap()
        self.place()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag = True
            self.offset = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drag:
            self.move(self.mapToParent(event.pos() - self.offset))
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.drag = False
        super().mouseReleaseEvent(event)

    def handle_press(self, event):
        if event.button() == Qt.LeftButton:
            self.handle.drag = True
            self.handle.offset = self.mapToParent(self.handle.mapToParent(event.pos()))
            self._start_size = (self.width(), self.height())

    def handle_move(self, event):
        if self.handle.drag:
            cur = self.mapToParent(self.handle.mapToParent(event.pos()))
            dx = cur.x() - self.handle.offset.x()
            dy = cur.y() - self.handle.offset.y()
            new_w = max(self.min_size, self._start_size[0] + dx)
            new_h = max(self.min_size, self._start_size[1] + dy)
            self.resize(int(new_w), int(new_h))

    def handle_release(self, event):
        self.handle.drag = False