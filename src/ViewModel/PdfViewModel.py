from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage

class PdfViewModel(QObject):

    def __init__(self, Model):
        super().__init__()
        self.Model = Model
        self.current_page = 0  # current page for pc
        self.loaded_count = 0



    def open_file(self, path):
        self.Model.open_file(path)
        self.current_page = 0


    def next_page(self):
        if (self.current_page + 1) < self.Model.total:
            self.current_page += 1

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1



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


    def get_next_pages(self, count):
        result = []
        for i in range(self.loaded_count, min(self.loaded_count+count, self.Model.total)):
            result.append(self.get_page_i(i))
            self.loaded_count+=1
        return result


