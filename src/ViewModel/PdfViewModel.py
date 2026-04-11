import os

import pymupdf
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage, QColor

from src.View.utils import has_char_in_fallback
from src.ViewModel.EditorMode import EditorMode


class PdfViewModel(QObject):

    page_number_changed = Signal()
    mode_changed = Signal(EditorMode)
    zoom_changed = Signal(float)
    history_changed = Signal()

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
        self.zoom = 1.0
        self._pending_text_spans = {}

    def set_zoom(self, zoom):
        self.zoom = max(0.25, min(4.0, round(zoom, 2)))
        self.zoom_changed.emit(self.zoom)


    def get_spans_i(self, page_index):
        return self.Model.get_spans_i(page_index)

    def get_pdf_fonts(self):
        best = {}
        for xref, data in self.Model.font_cache.items():
            name = data['name']
            cp_count = len(data.get('codepoints', set()))
            if name not in best or cp_count > best[name][1]:
                best[name] = (xref, cp_count)
        return sorted([(name, xref) for name, (xref, _) in best.items()], key=lambda pair: pair[0].lower(),)

    def font_pymupdf_to_pyside6(self, font_pymupdf):
        font_map = {
            "helv": "Helvetica",
            "tiro": "Times New Roman",
            "tibo": "Times New Roman",
            "tiit": "Times New Roman",
            "tibi": "Times New Roman",
            "cour": "Courier New",
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
        self.history_changed.emit()

    def save_file_as(self, path, override_spans_pages=None, override_images_pages=None):
        self.current_path = path
        self.Model.save_file(path, override_spans_pages, override_images_pages)
        self.history_changed.emit()

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
        self.history_changed.emit()

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
        pix = self.Model.render_page(i, override_spans, self.zoom)
        image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
        return image

    def insert_image(self, page_index, img_data):
        self.Model.insert_image_at(page_index, img_data)
        self.history_changed.emit()

    def get_total(self):
        return self.Model.total


    def get_next_pages(self, count):
        result = []
        for i in range(self.loaded_count, min(self.loaded_count+count, self.Model.total)):
            result.append(self.get_page_i(i))
            self.loaded_count+=1
        return result

    def add_text(self, text, x, y, page_index, xref=0):
        self.Model.add_text(text, x, y, page_index, self.current_font,
                            self.current_fontsize, self.current_color, xref)
        self.history_changed.emit()

    def get_images_i(self, page_index):
        return self.Model.get_images_i(page_index)

    def commit_image_edit(self, page_index, images):
        text_spans = self._pending_text_spans.get(page_index)
        self.Model.full_redraw_images(self.Model.file[page_index], images, text_spans)
        self.history_changed.emit()

    def close_file(self):
        self.current_path = None
        self.current_page = 0
        self.loaded_count = 0
        self.zoom = 1.0
        self.history_changed.emit()
        self.page_number_changed.emit()
        self.Model.close_file()

    def get_missing_chars(self, xref, font_pymupdf_name, text):
        chars = [ch for ch in text if ch.strip()]
        if not chars:
            return []
        if xref != 0:
            data = self.Model.font_cache.get(xref)
            if data:
                return [ch for ch in chars if ord(ch) not in data['codepoints']]
        try:
            if os.path.isfile(font_pymupdf_name):
                f = pymupdf.Font(fontfile=font_pymupdf_name)
            else:
                f = pymupdf.Font(fontname=font_pymupdf_name)
            return [ch for ch in chars if f.has_glyph(ord(ch)) == 0]
        except Exception:
            return []

    def set_pending_text_spans(self, spans_dict):
        self._pending_text_spans = spans_dict or {}

    def undo(self):
        result = self.Model.undo()
        if result >= 0:
            self.history_changed.emit()
        return result

    def redo(self):
        result = self.Model.redo()
        if result >= 0:
            self.history_changed.emit()
        return result

    def can_undo(self):
        return self.Model.can_undo()

    def can_redo(self):
        return self.Model.can_redo()

    def commit_text_moves(self, page_index, spans):
        self.Model._full_redraw(self.Model.file[page_index], spans)
        self.Model._page_spans_cache.pop(page_index, None)

    def save_snapshot(self, page_index=None):
        if page_index is None:
            page_index = self.current_page
        self.Model.save_snapshot(page_index)
        self.history_changed.emit()