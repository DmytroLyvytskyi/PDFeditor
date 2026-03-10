from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage, QColor

from src.View.utils import has_char_in_fallback
from src.ViewModel.EditorMode import EditorMode


class PdfViewModel(QObject):

    page_number_changed = Signal()
    mode_changed = Signal(EditorMode)

    def __init__(self, Model):
        super().__init__()
        self.Model = Model
        self.current_page = 0  # current page for pc
        self.loaded_count = 0
        self.mode = EditorMode.VIEW
        self.current_font = "helv"
        self.current_fontsize = 12
        self.current_color = QColor(0, 0, 0)
        self.current_path = None
        self.current_font_xref = 0



    def get_spans_i(self, page_index):
        return self.Model.get_spans_i(page_index)

    def get_pdf_fonts(self):
        result = []
        for xref, data in self.Model.font_cache.items():
            result.append((data['name'], xref))
        return result

    def font_pymupdf_to_pyside6(self, font_pymupdf):
        font_map = {
            "helv": "Helvetica",
            "tiro": "Times New Roman",
            "cour": "Courier New"
        }
        return font_map[font_pymupdf]

    def has_char_in_bundled(self, xref, char):
        return has_char_in_fallback(self.Model.font_cache, xref, char)

    def font_pyside6_to_pymupdf(self, font_pyside6):
        font_map = {
            "Helvetica": "helv",
            "Times New Roman": "tiro",
            "Courier New": "cour",
            "Courier": "cour"
        }
        return font_map[font_pyside6]

    def is_char_valid(self, xref, char):
        if xref == 0:
            return True
        data = self.Model.font_cache.get(xref)
        if data is None:
            return True
        return ord(char) in data['codepoints']

    def save_file(self, path, override_spans_pages=None, override_images_pages=None):
        self.Model.save_file(path, override_spans_pages, override_images_pages)

    def save_file_as(self, path, override_spans_pages=None, override_images_pages=None):
        self.current_path = path
        self.Model.save_file(path, override_spans_pages, override_images_pages)

    def set_current_font(self, font_name):
        self.current_font = font_name

    def set_current_size(self, size):
        self.current_fontsize = size

    def set_current_color(self, color):
        self.current_color = color


    def set_mode(self, mode):
        self.mode = mode
        self.mode_changed.emit(mode)

    def open_file(self, path):
        self.current_path = path
        self.Model.open_file(path)
        self.current_page = 0
        self.loaded_count = 0
        self.page_number_changed.emit()

    def next_page(self):
        if (self.current_page + 1) < self.Model.total:
            self.current_page += 1
            self.page_number_changed.emit()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.page_number_changed.emit()

    def get_current_page_number(self):
        return self.current_page + 1


    def set_current_page_number(self, page):
        self.current_page = page - 1
        self.page_number_changed.emit()

    def get_page_i(self, i, override_spans=None):
        pix = self.Model.render_page(i, override_spans)
        image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
        return image

    def insert_image(self, page_index, img_data):
        self.Model.insert_image_at(page_index, img_data)

    def get_total(self):
        return self.Model.total


    def get_next_pages(self, count):
        result = []
        for i in range(self.loaded_count, min(self.loaded_count+count, self.Model.total)):
            result.append(self.get_page_i(i))
            self.loaded_count+=1
        return result

    def add_text(self, text, x, y, page_index, xref=0):
        self.Model.add_text(text, x, y, page_index, self.current_font, self.current_fontsize, self.current_color, xref)

    def get_images_i(self, page_index):
        return self.Model.get_images_i(page_index)

    def commit_image_edit(self, page_index, images):
        self.Model.full_redraw_images(self.Model.file[page_index], images)


