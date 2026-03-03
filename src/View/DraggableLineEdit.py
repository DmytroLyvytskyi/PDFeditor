from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QFont, QFontMetrics, QFontDatabase
from PySide6.QtWidgets import QWidget, QLineEdit, QMessageBox


class DraggableLineEdit(QLineEdit):

    def __init__(self,viewmodel, parent=None):
        super().__init__(parent)
        self.drag = False
        self.offset = QPoint(0, 0)
        self.viewmodel = viewmodel
        self.scale_y = 1.0
        self.xref = 0
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
        try:
            display_name = self.viewmodel.font_pymupdf_to_pyside6(font)
        except KeyError:
            xref = self.xref
            data = self.viewmodel.Model.font_cache.get(xref)
            if data is not None and len(data) > 0:
                font_id = QFontDatabase.addApplicationFont(data['tmp_path'])
                families = QFontDatabase.applicationFontFamilies(font_id)
                display_name = families[0] if families else "Times New Roman"
            else:
                display_name = "Times New Roman"
        qt_font = QFont(display_name)
        qt_font.setPixelSize(int(fontsize * self.scale_y))
        self.setFont(qt_font)
        self.setStyleSheet(
            f"color: rgb({color.red()}, {color.green()}, {color.blue()});"
            "background: transparent;"
            "border: 1px dashed gray;"
        )
        self.adjust_size()

    def keyPressEvent(self, event):
        char = event.text()
        if char != "" and char != " " and self.xref != 0 and char.isprintable():
            if self.viewmodel.is_char_valid(self.xref, char) == False:
                msg = QMessageBox()
                msg.setWindowTitle("Unavailable сharacter ")
                msg.setText(f"The symbol '{char}' is not available in this font.")
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.exec()
                return
        super().keyPressEvent(event)

