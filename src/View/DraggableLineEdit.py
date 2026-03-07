from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtGui import QFont, QFontMetrics, QFontDatabase
from PySide6.QtWidgets import QWidget, QLineEdit, QMessageBox, QApplication


class DraggableLineEdit(QLineEdit):

    def __init__(self,viewmodel, parent=None):
        super().__init__(parent)
        self.drag = False
        self.offset = QPoint(0, 0)
        self.viewmodel = viewmodel
        self.scale_y = 1.0
        self.xref = 0
        self.textChanged.connect(self.adjust_size)
        self._current_color = None

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
        self._current_color = color
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
                if self.viewmodel.has_char_in_bundled(self.xref, char):
                    def show_dialog(c=char, e=event):
                        msg = QMessageBox(QApplication.activeWindow())
                        msg.setWindowTitle("Character not in original font")
                        msg.setText(
                            f"The symbol '{c}' is not available in the original font.\n"
                            "A similar font can be used instead."
                        )
                        msg.setIcon(QMessageBox.Icon.Question)
                        use_btn = msg.addButton("Use similar font", QMessageBox.ButtonRole.AcceptRole)
                        msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
                        msg.exec()
                        if msg.clickedButton() == use_btn:
                            color = self._current_color if self._current_color else self.viewmodel.current_color
                            fontsize = int(self.font().pixelSize() / self.scale_y)
                            self.apply_change("tiro", fontsize, color)
                            self.insert(c)
                    QTimer.singleShot(0, show_dialog)
                else:
                    def show_warning(c=char):
                        msg = QMessageBox(QApplication.activeWindow())
                        msg.setWindowTitle("Unavailable character")
                        msg.setText(f"The symbol '{c}' is not available in any font.")
                        msg.setIcon(QMessageBox.Icon.Warning)
                        msg.exec()
                    QTimer.singleShot(0, show_warning)
                return
        super().keyPressEvent(event)

