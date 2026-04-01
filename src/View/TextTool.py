from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QStyle

from src.View.DraggableLineEdit import DraggableLineEdit
from src.View.EditTextQLabel import EditTextQLabel
from src.View.TextData import TextData
from src.View.utils import calculate_x_offset, get_scale, calculate_y_offset


class TextTool:
    def __init__(self, viewmodel, pages_QWidget, page_manager, on_dirty=None, on_label_selected=None):
        self.viewmodel = viewmodel
        self.pages_QWidget = pages_QWidget
        self.page_manager = page_manager
        self.add_text = None
        self.edit_labels = {}
        self._pending_spans= {}
        self.add_text_page_index = None
        self.on_dirty = on_dirty
        self.on_label_selected = on_label_selected
        self._saved_text_data = {}

    def clear_edit_labels(self):
        pages_to_rerender = list(self.edit_labels.keys())

        for page_index, labels in self.edit_labels.items():
            spans = self._collect_current_pdf_spans(page_index)
            if spans:
                self._pending_spans[page_index] = spans
            self._saved_text_data[page_index] = [lbl.text_data for lbl in labels]
            for label in labels:
                if label.edit_text is not None:
                    try:
                        label.edit_text.deleteLater()
                    except RuntimeError:
                        pass
                    label.edit_text = None
                label.deleteLater()
        self.edit_labels.clear()

        for page_index in pages_to_rerender:
            self.page_manager.rerender_page(page_index)

    def add_text_func(self, x, y, page_index):
        label = self.pages_QWidget[page_index]
        if self.add_text is not None:
            try:
                self.save_text(0, 0, self.add_text_page_index)
            except RuntimeError:
                self.add_text = None
            return
        x_offset = calculate_x_offset(label)
        y_offset = calculate_y_offset(label)
        scale_x, scale_y = get_scale(self.viewmodel, page_index, label)
        self.add_text = DraggableLineEdit(self.viewmodel, label)
        self.add_text_page_index = page_index
        self.add_text.scale_y = scale_y
        self.add_text.xref = self.viewmodel.current_font_xref
        self.add_text.move(x + x_offset, y + y_offset - self.add_text.height() / 2)
        self.add_text.show()
        self.add_text.setFocus()
        self.add_text.returnPressed.connect(lambda: self.save_text(0, 0, self.add_text_page_index))
        self.add_text.apply_change(
            self.viewmodel.current_font,
            self.viewmodel.current_fontsize,
            self.viewmodel.current_color
        )
        self.add_text.font_fallback_applied.connect(self._on_add_text_fallback)

    def clear(self):
        if self.add_text and self.add_text_page_index is not None:
            try:
                self.save_text(0, 0, self.add_text_page_index)
            except RuntimeError:
                self.add_text = None
        for page_index, labels in self.edit_labels.items():
            for label in labels:
                if label.edit_text is not None:
                    try:
                        label.edit_text.deleteLater()
                    except RuntimeError:
                        pass
                    label.edit_text = None
                try:
                    label.deleteLater()
                except RuntimeError:
                    pass
        self.edit_labels.clear()
        self._pending_spans.clear()
        self._saved_text_data.clear()

    def _collect_current_pdf_spans(self, page_index):
        if page_index not in self.edit_labels:
            return []
        label = self.pages_QWidget[page_index]
        x_offset = calculate_x_offset(label)
        y_offset = calculate_y_offset(label)
        scale_x, scale_y = get_scale(self.viewmodel, page_index, label)
        padding = 5
        result = []
        for lbl in self.edit_labels[page_index]:
            text_data = lbl.text_data
            original_screen_x = int(int(lbl.bbox[0] * scale_x) + x_offset - padding)
            original_screen_y = int((text_data.origin[1] - text_data.size) * scale_y) + y_offset
            delta_x = lbl.x() - original_screen_x
            delta_y = lbl.y() - original_screen_y
            pdf_x = text_data.origin[0] + delta_x / scale_x
            pdf_y = text_data.origin[1] + delta_y / scale_y
            color = text_data.color
            pdf_color = (color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0)
            result.append((pdf_x, pdf_y, text_data.text, text_data.font, text_data.size, pdf_color, text_data.xref))
        return result

    def save_text(self, x, y, page_index):
        text = self.add_text.text()
        if text != "":
            label = self.pages_QWidget[page_index]
            x_offset = calculate_x_offset(label)
            y_offset = calculate_y_offset(label)
            scale_x, scale_y = get_scale(self.viewmodel, page_index, label)
            metrics = QFontMetrics(self.add_text.font())
            frame = self.add_text.style().pixelMetric(QStyle.PixelMetric.PM_DefaultFrameWidth)
            pdf_x = (self.add_text.x() + frame - x_offset) / scale_x
            text_top = (self.add_text.height() - metrics.height()) / 2
            pdf_y = (self.add_text.y() - y_offset + text_top + metrics.ascent()) / scale_y
            self.viewmodel.add_text(text, pdf_x, pdf_y, page_index, self.add_text.xref)
        self.add_text.deleteLater()
        self.add_text = None
        self.add_text_page_index = None
        self.page_manager.rerender_page(page_index)
        if self.on_dirty:
            self.on_dirty()

    def move_text(self, page_index):
        override_spans = self._collect_current_pdf_spans(page_index)
        self._pending_spans[page_index] = override_spans
        self.viewmodel.save_snapshot(page_index)
        self.page_manager.rerender_page(page_index, override_spans)
        if self.on_dirty:
            self.on_dirty()

    def get_override_spans_for_save(self):
        for page_index in self.edit_labels:
            spans = self._collect_current_pdf_spans(page_index)
            if spans:
                self._pending_spans[page_index] = spans
        result = {pi: spans for pi, spans in self._pending_spans.items() if spans}
        return result if result else None

    def prepare_edit_mode_i(self, page_index):
        if page_index in self.edit_labels:
            return
        if page_index >= len(self.pages_QWidget):
            return
        label = self.pages_QWidget[page_index]
        padding = 5
        spans = self.viewmodel.get_spans_i(page_index)
        x_offset = calculate_x_offset(label)
        y_offset = calculate_y_offset(label)
        page_labels = []
        scale_x, scale_y = get_scale(self.viewmodel, page_index, label)
        saved = self._saved_text_data.get(page_index, [])
        for i, (size, font, color, text, bbox, origin, xref) in enumerate(spans):
            if i < len(saved):
                text_data = saved[i]
                text_data.origin = origin
            else:
                text_data = TextData(text, font, size, color, origin, xref)
            top = int((origin[1] - text_data.size) * scale_y)
            left = int(bbox[0] * scale_x)
            width = int((bbox[2] - bbox[0]) * scale_x)
            height = int(text_data.size * 1.3 * scale_y) + padding
            edit_text = EditTextQLabel(text_data, width + 2 * padding, height + padding, bbox, self.viewmodel, label)
            edit_text.scale_x = scale_x
            edit_text.scale_y = scale_y
            edit_text.move(left + x_offset - padding, top + y_offset)
            edit_text.coords.connect(lambda x, y, bbox, pi=page_index: self.move_text(pi))
            edit_text.selected.connect(lambda l=edit_text: self._on_label_selected(l))
            page_labels.append(edit_text)
        self.edit_labels[page_index] = page_labels

    def prepare_edit_mode(self):
        self.clear_edit_labels()
        for i in range(len(self.pages_QWidget)):
            self.prepare_edit_mode_i(i)

    def _on_label_selected(self, label):
        if self.add_text is not None and isinstance(self.add_text, EditTextQLabel) and self.add_text is not label:
            page_index = self._find_label_page(self.add_text)
            if page_index is not None:
                self.move_text(page_index)
        self.add_text = label
        if self.on_label_selected:
            self.on_label_selected(label)

    def delete_selected(self):
        if self.add_text is None or not isinstance(self.add_text, EditTextQLabel):
            return
        lbl = self.add_text
        self.add_text = None
        for page_index, lst in self.edit_labels.items():
            if lbl in lst:
                lst.remove(lbl)
                lbl.deleteLater()
                self.move_text(page_index)
                return

    def apply_style_to_selected(self, font, fontsize, color, xref=None):
        if self.add_text is None:
            return
        if xref is not None:
            if isinstance(self.add_text, EditTextQLabel):
                self.add_text.text_data.xref = xref
            else:
                self.add_text.xref = xref
        try:
            self.add_text.apply_change(font, fontsize, color)
        except RuntimeError:
            self.add_text = None

    def commit_selected(self):
        if self.add_text and isinstance(self.add_text, EditTextQLabel):
            page_index = self._find_label_page(self.add_text)
            if page_index is not None:
                self.move_text(page_index)

    def _find_label_page(self, label):
        for page_index, labels in self.edit_labels.items():
            if label in labels:
                return page_index
        return None

    def _on_add_text_fallback(self, font_name, fontsize, color):
        self.viewmodel.set_current_font(font_name)
        self.viewmodel.current_font_xref = 0
        self.viewmodel.set_current_size(int(fontsize))
        if self.on_label_selected:
            self.on_label_selected(self.add_text)