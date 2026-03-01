from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QStyle

from src.View.DraggableLineEdit import DraggableLineEdit
from src.View.EditTextQLabel import EditTextQLabel
from src.View.TextData import TextData
from src.View.utils import *

class TextTool:
    def __init__(self, viewmodel, pages_QWidget, page_manager):
        self.viewmodel = viewmodel
        self.pages_QWidget = pages_QWidget
        self.page_manager = page_manager
        self.add_text = None
        self.edit_labels: dict[int, list] = {}

    def clear_edit_labels(self):
        for labels in self.edit_labels.values():
            for label in labels:
                label.deleteLater()
        self.edit_labels.clear()

    def add_text_func(self, x, y, page_index):
        label = self.pages_QWidget[page_index]
        x_offset = calculate_x_offset(label)
        if self.add_text != None:
            self.add_text.deleteLater()
            self.add_text = None
        scale_x, scale_y = self._get_scale(page_index, label)
        self.add_text = DraggableLineEdit(self.viewmodel, label)
        self.add_text.scale_y = scale_y
        self.add_text.move(x + x_offset, y - self.add_text.height() / 2)
        self.add_text.show()
        self.add_text.setFocus()
        self.add_text.returnPressed.connect(
            lambda: self.save_text(x, y, page_index))
        # without offset because pymupdf works with the coordinates of the file
        self.add_text.apply_change(
            self.viewmodel.current_font,
            self.viewmodel.current_fontsize,
            self.viewmodel.current_color
        )

    def clear(self):
        if self.add_text:
            self.add_text.deleteLater()
            self.add_text = None

    def _collect_current_pdf_spans(self, page_index):
        if page_index not in self.edit_labels:
            return []
        label = self.pages_QWidget[page_index]
        x_offset = calculate_x_offset(label)
        scale_x, scale_y = self._get_scale(page_index, label)
        padding = 5
        result = []
        for lbl in self.edit_labels[page_index]:
            text_data = lbl.text_data
            original_screen_x = int(int(lbl.bbox[0] * scale_x) + x_offset - padding)
            original_screen_y = int((text_data.origin[1] - text_data.size) * scale_y)
            delta_x = lbl.x() - original_screen_x
            delta_y = lbl.y() - original_screen_y
            pdf_x = text_data.origin[0] + delta_x / scale_x
            pdf_y = text_data.origin[1] + delta_y / scale_y
            color = text_data.color
            pdf_color = (color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0)
            result.append((pdf_x, pdf_y, text_data.text, text_data.font, text_data.size, pdf_color))
        return result

    def save_text(self, x, y, page_index):
        text = self.add_text.text()
        if text != "":
            label = self.pages_QWidget[page_index]
            x_offset = calculate_x_offset(label)
            scale_x, scale_y = self._get_scale(page_index, label)
            metrics = QFontMetrics(self.add_text.font())
            frame = self.add_text.style().pixelMetric(QStyle.PixelMetric.PM_DefaultFrameWidth)
            pdf_x = (self.add_text.x() + frame - x_offset) / scale_x
            pdf_y = (self.add_text.y() + metrics.ascent() - frame) / scale_y
            self.viewmodel.add_text(text, pdf_x, pdf_y, page_index)
        self.add_text.deleteLater()
        self.add_text = None
        self.page_manager.rerender_page(page_index)

    def _get_scale(self, page_index, label):
        page_rect = self.viewmodel.Model.file[page_index].rect
        pixmap = label.pixmap()
        scale_x = pixmap.width() / page_rect.width
        scale_y = pixmap.height() / page_rect.height
        return scale_x, scale_y

    def move_text(self, page_index):
        override_spans = self._collect_current_pdf_spans(page_index)
        self.page_manager.rerender_page(page_index, override_spans)

    def get_override_spans_for_save(self):
        result = {}
        for page_index in self.edit_labels:
            spans = self._collect_current_pdf_spans(page_index)
            if spans:
                result[page_index] = spans
        if result != {}:
            return result
        return None

    def prepare_edit_mode_i(self, page_index):
        if page_index in self.edit_labels:
            return
        if page_index >= len(self.pages_QWidget):
            return
        label = self.pages_QWidget[page_index]
        padding = 5
        spans = self.viewmodel.get_spans_i(page_index)
        x_offset = calculate_x_offset(label)
        page_labels = []
        scale_x, scale_y = self._get_scale(page_index, label)
        for size,font,color,text,bbox,origin in spans:
            text_data = TextData(text,font,size,color,origin)
            top = int((origin[1] - size) * scale_y)
            left = int(bbox[0] * scale_x)
            width = int((bbox[2] - bbox[0]) * scale_x)
            height = int(size * 1.3 * scale_y)+ padding
            edit_text = EditTextQLabel(text_data, width + 2*padding, height + padding,bbox,self.viewmodel, label)
            edit_text.scale_x = scale_x
            edit_text.scale_y = scale_y
            edit_text.move(left + x_offset - padding, top)
            edit_text.coords.connect(self.move_text)
            edit_text.selected.connect(lambda l=edit_text: self._on_label_selected(l))
            page_labels.append(edit_text)
        self.edit_labels[page_index] = page_labels

    def prepare_edit_mode(self):
        self.clear_edit_labels()
        for i in range(len(self.pages_QWidget)):
            self.prepare_edit_mode_i(i)

    def _on_label_selected(self, label):
        self.add_text = label
