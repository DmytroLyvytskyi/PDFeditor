from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel


class PageQLabel(QLabel):
    coords = Signal(int, int, int) # x, y relative to pixmap(left top corner), page_index(id)

    def __init__(self, pixmap=None, id=None, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setPixmap(pixmap)
        self.id = id

    def mousePressEvent(self, event):
        label_width = self.width()
        label_height = self.height()
        pixmap_width = self.pixmap().width()
        pixmap_height = self.pixmap().height()
        center_x = label_width / 2
        center_y = label_height / 2
        page_start_x = center_x - pixmap_width / 2
        page_start_y = center_y - pixmap_height / 2
        x = event.x() - page_start_x
        y = event.y() - page_start_y
        if 0 <= x <= pixmap_width and 0 <= y <= pixmap_height:
            self.coords.emit(int(x), int(y), self.id)
        super().mousePressEvent(event)