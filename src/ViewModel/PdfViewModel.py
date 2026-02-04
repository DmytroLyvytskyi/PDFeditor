from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage

class PdfViewModel(QObject):
    page_changed = Signal(QImage)

    def __init__(self, Model):
        super().__init__()
        self.Model = Model
        self.current_page = 0  # starts from 0



    def open_file(self, path):
        self.Model.open_file(path)
        self.current_page = 0
        self._update_page()


    def next_page(self):
        if (self.current_page + 1) < self.Model.total:
            self.current_page += 1
            self._update_page()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._update_page()


    def _update_page(self):
        pix = self.Model.render_page(self.current_page)
        image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
        self.page_changed.emit(image)

    def get_page_i(self, i):
        pix = self.Model.render_page(i)
        image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
        return image



    def get_total(self):
        return self.Model.total

    def get_current_page_number(self):
        return self.current_page + 1


    def set_current_page_number(self, page):
        self.current_page = page - 1
        self._update_page()

