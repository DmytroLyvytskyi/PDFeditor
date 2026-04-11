import os

from PySide6.QtCore import Qt, QPoint, QTimer, Signal
from PySide6.QtGui import QFont, QFontMetrics, QFontDatabase
from PySide6.QtWidgets import QWidget, QLineEdit, QMessageBox, QApplication

from src.View.utils import find_system_font_by_category, find_system_font, pymupdf_fonts, \
    get_font_category


class DraggableLineEdit(QLineEdit):
    font_fallback_applied = Signal(str, float, object)  # font_name, size, color

    def __init__(self, viewmodel, parent=None):
        super().__init__(parent)
        self.drag = False
        self.offset = QPoint(0, 0)
        self.viewmodel = viewmodel
        self.scale_y = 1.0
        self.xref = 0
        self.textChanged.connect(self.adjust_size)
        self._current_color = None
        self._showing_dialog = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag = True
            self.offset = event.pos() # event.pos -> position relative to the widget that was clicked
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
                display_name = families[0] if families else "Arial"
            elif os.path.isfile(font):
                font_id = QFontDatabase.addApplicationFont(font)
                families = QFontDatabase.applicationFontFamilies(font_id)
                display_name = families[0] if families else "Arial"
            else:
                display_name = "Arial"
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
                if self._showing_dialog:
                    return
                if self.viewmodel.has_char_in_bundled(self.xref, char):
                    self._showing_dialog = True

                    def show_dialog(c=char):
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
                        self._showing_dialog = False
                        if msg.clickedButton() == use_btn:
                            color = self._current_color if self._current_color else self.viewmodel.current_color
                            fontsize = int(self.font().pixelSize() / self.scale_y)
                            data = self.viewmodel.Model.font_cache.get(self.xref)
                            if data:
                                fallback_path = find_system_font(data['name'])
                                category = data.get('category', 'serif')
                                if not fallback_path:
                                    fallback_path = find_system_font_by_category(category)
                            else:
                                cur_font = self.viewmodel.current_font
                                category = get_font_category(cur_font)
                                fallback_path = find_system_font(cur_font)
                                if not fallback_path:
                                    fallback_path = find_system_font_by_category(category)

                            fallback_font = fallback_path if fallback_path else pymupdf_fonts.get(category, "helv")

                            self.apply_change(fallback_font, fontsize, color)
                            self.xref = 0
                            self.font_fallback_applied.emit(fallback_font, fontsize, color)
                            self.insert(c)

                    QTimer.singleShot(0, show_dialog)
                else:
                    self._showing_dialog = True

                    def show_warning(c=char):
                        msg = QMessageBox(QApplication.activeWindow())
                        msg.setWindowTitle("Unavailable character")
                        msg.setText(f"The symbol '{c}' is not available in any font.")
                        msg.setIcon(QMessageBox.Icon.Warning)
                        msg.exec()
                        self._showing_dialog = False

                    QTimer.singleShot(0, show_warning)
                return
        super().keyPressEvent(event)

