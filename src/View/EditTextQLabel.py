from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QFontMetrics, QFont
from PySide6.QtWidgets import QLabel

from src.View.DraggableLineEdit import DraggableLineEdit


class EditTextQLabel(QLabel):
    coords = Signal(int, int, tuple) # x,y
    def __init__(self,text_data,width,height,bbox, parent=None):
        super().__init__(parent)
        self.drag = False
        self.edit_text = None
        self.offset = QPoint(0, 0)
        self.text_data = text_data
        self.setFixedSize(width, height)
        self.bbox = bbox
        self.setStyleSheet("border: 2px solid gray; background: transparent;")
        self.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag = True
            self.offset = event.pos() # event.pos -> position relative to the widget that was clicked
            self.setStyleSheet("border: 2px solid gray; background-color: rgba(137, 207, 240, 100);")
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
        self.setStyleSheet("border: 2px solid gray; background: transparent;")
        self.coords.emit(self.x(), self.y(), self.bbox)
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            label = self.parent()
            self.edit_text = DraggableLineEdit(label)
            self.edit_text.move(self.x(), self.y())
            self.hide()
            self.edit_text.show()
            self.edit_text.setFocus()
            self.edit_text.setText(self.text_data.text)
            font_map = {
                "Helvetica": "helv",
                "Times New Roman": "tiro",
                "Courier New": "cour"
            }
            self.edit_text.apply_change(
                font_map[self.text_data.font],
                self.text_data.size,
                self.text_data.color
            )
            self.edit_text.returnPressed.connect(self.finished)
        super().mouseDoubleClickEvent(event)

    def finished(self):
        new_text = self.edit_text.text()
        self.text_data.text = new_text
        self.update_visual_size()
        self.coords.emit(self.x(), self.y(), self.bbox)
        self.edit_text.deleteLater()
        self.show()

    def update_visual_size(self):
        font_map = {
            "helv": "Helvetica",
            "tiro": "Times New Roman",
            "cour": "Courier New"
        }
        qt_font = QFont(font_map.get(self.text_data.font, "Helvetica"), self.text_data.size)
        metrics = QFontMetrics(qt_font)

        width = metrics.horizontalAdvance(self.text_data.text)
        height = metrics.height()
        padding = 5
        self.setFixedSize(width + padding, height + padding)