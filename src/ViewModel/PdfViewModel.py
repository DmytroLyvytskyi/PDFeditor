from PySide6.QtCore import QObject
from PySide6.QtGui import QImage
class PdfViewModel(QObject):
    def __init__(self, Model):
        super().__init__()
        self.Model = Model
        self.current_page = 0  # starts from 0


    def open_file(self, path):
        self.Model.open_file(path)
        self.current_page = 0


    def next_page(self):
        if (self.current_page + 1) < self.Model.total:
            self.current_page += 1

    def prev_page(self):
        if (self.current_page - 1) > 0:
            self.current_page -= 1

    def get_page(self):
        page = self.Model.get_page(self.current_page)
        if page is None:
            return None

        pix = page.get_pixmap()
        return QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)

    def get_total(self):
        return self.Model.total

    def get_current_page_number(self):
        return self.current_page + 1


    def set_current_page_number(self, page):
        self.current_page = page - 1
