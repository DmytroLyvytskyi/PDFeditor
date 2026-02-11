from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import QWidget, QLineEdit


class DraggableLineEdit(QLineEdit):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.drag = False
        self.offset = QPoint(0, 0)


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag = True
            self.offset = event.pos() # event.pos -> position relative to the widget that was clicked
            super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)


    def mouseMoveEvent(self, event):
        if self.drag:
            self.move(self.mapToParent(event.pos() - self.offset))
            # mapToParent -> position relative to the parent widget
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.drag = False
        super().mouseReleaseEvent(event)