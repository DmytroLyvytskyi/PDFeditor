import pymupdf
from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QFontMetrics, QFont
from PySide6.QtWidgets import QLabel

from src.View.DraggableLineEdit import DraggableLineEdit
from src.View.utils import resolve_font


class EditTextQLabel(QLabel):
    coords = Signal(int, int, tuple) # x,y
    selected = Signal(object)
    def __init__(self,text_data,width,height,bbox,viewmodel, parent=None):
        super().__init__(parent)
        self.drag = False
        self._moved = False
        self.edit_text = None
        self.offset = QPoint(0, 0)
        self.text_data = text_data
        self.setFixedSize(width, height)
        self.bbox = bbox
        self.viewmodel = viewmodel
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.setStyleSheet("border: 2px solid gray; background: transparent;")
        self.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag = True
            self._moved = False
            self.offset = event.pos() # event.pos -> position relative to the widget that was clicked
            self.setStyleSheet("border: 2px solid gray; background-color: rgba(137, 207, 240, 100);")
            self.selected.emit(self)
            super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)



    def mouseMoveEvent(self, event):
        if self.drag:
            self._moved = True
            self.move(self.mapToParent(event.pos() - self.offset))
            # mapToParent -> position relative to the parent widget
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.drag = False
        self.setStyleSheet("border: 2px solid gray; background: transparent;")
        if self._moved:
            self.coords.emit(self.x(), self.y(), self.bbox)
        self._moved = False
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            label = self.parent()
            self.edit_text = DraggableLineEdit(self.viewmodel, label)
            self.edit_text.xref = self.text_data.xref
            self.edit_text.scale_y = self.scale_y
            self.edit_text.move(self.x(), self.y())
            self.hide()
            self.edit_text.show()
            self.edit_text.setFocus()
            self.edit_text.setText(self.text_data.text)
            self.edit_text.apply_change(
                self.text_data.font,
                self.text_data.size,
                self.text_data.color
            )
            self.edit_text.returnPressed.connect(self.finished)
            self.edit_text.font_fallback_applied.connect(self._on_inline_fallback)
        super().mouseDoubleClickEvent(event)

    def _on_inline_fallback(self, font_name, fontsize, color):
        self.text_data.font = font_name
        self.text_data.size = fontsize
        self.text_data.xref = 0
        if self.edit_text:
            self.edit_text.xref = 0
        self.selected.emit(self)

    def apply_change(self, font, fontsize, color):
        self.text_data.font = font
        self.text_data.size = fontsize
        self.text_data.color = color
        self.update_visual_size()
        if self.edit_text is not None:
            self.edit_text.xref = self.text_data.xref
            try:
                self.edit_text.apply_change(font, fontsize, color)
            except RuntimeError:
                self.edit_text = None
        self.coords.emit(self.x(), self.y(), self.bbox)

    def commit(self):
        self.coords.emit(self.x(), self.y(), self.bbox)

    def finished(self):
        new_text = self.edit_text.text()
        self.text_data.text = new_text
        self.text_data.xref = self.edit_text.xref
        self.drag = False
        self.setStyleSheet("border: 2px solid gray; background: transparent;")
        self.move(self.edit_text.pos())
        padding = 5
        tmp_path, fontname = resolve_font(self.viewmodel.Model.font_cache, self.text_data.xref, new_text,
                                          font_name=self.text_data.font)
        if tmp_path != None:
            f = pymupdf.Font(fontfile=tmp_path)
        else:
            f = pymupdf.Font(fontname=fontname)
        width = int(f.text_length(new_text, fontsize=self.text_data.size) * self.scale_x)
        height = int(self.text_data.size * 1.3 * self.scale_y)
        self.setFixedSize(width + 2 * padding, height + 2 * padding)
        self.edit_text.deleteLater()
        self.edit_text = None
        self.show()
        self.coords.emit(self.x(), self.y(), self.bbox)

    def update_visual_size(self):
        padding = 5
        size = self.text_data.size
        metrics = QFontMetrics(QFont(self.text_data.font, int(size)))
        width = int(metrics.horizontalAdvance(self.text_data.text) * self.scale_x)
        height = int(size * 1.3 * self.scale_y) + padding
        self.setFixedSize(width + 2 * padding, height + padding)