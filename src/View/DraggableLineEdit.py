from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QFont, QFontMetrics
from PySide6.QtWidgets import QWidget, QLineEdit


class DraggableLineEdit(QLineEdit):

    def __init__(self,viewmodel, parent=None):
        super().__init__(parent)
        self.drag = False
        self.offset = QPoint(0, 0)
        self.viewmodel = viewmodel
        self.textChanged.connect(self.adjust_size)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag = True
            self.offset = event.pos() # event.pos -> position relative to the widget that was clicked
            super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def adjust_size(self):
        metrics = QFontMetrics(self.font())
        text = self.text()
        width = metrics.horizontalAdvance(text)
        height = metrics.height()
        padding = 10
        self.resize(width + padding, height + padding)

    def mouseMoveEvent(self, event):
        if self.drag:
            self.move(self.mapToParent(event.pos() - self.offset))
            # mapToParent -> position relative to the parent widget
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.drag = False
        super().mouseReleaseEvent(event)

    def apply_change(self,font, fontsize, color):
        qt_font = QFont(self.viewmodel.font_pymupdf_to_pyside6(font),fontsize)
        self.setFont(qt_font)
        self.setStyleSheet(
            f"color: rgb({color.red()}, {color.green()}, {color.blue()});"
            "background: transparent;"
            "border: 1px dashed gray;"
        )
        self.adjust_size()

