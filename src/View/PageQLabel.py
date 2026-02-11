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
        pixmap_width = self.pixmap().width()
        center_x = label_width / 2
        page_start_x = center_x - pixmap_width / 2
        x = event.x() - page_start_x
        if (x >= 0 and x <= pixmap_width):
            self.coords.emit(int(x), event.y(), self.id)

        super().mousePressEvent(event)


