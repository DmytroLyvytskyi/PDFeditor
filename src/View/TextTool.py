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

    def add_text_func(self, x, y, page_index):
        label = self.pages_QWidget[page_index]
        x_offset = calculate_x_offset(label)
        if self.add_text != None:
            self.add_text.deleteLater()
            self.add_text = None

        self.add_text = DraggableLineEdit(self.viewmodel, label)
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

    def save_text(self, x, y, page_index):
        text = self.add_text.text()
        if text != "":
            label = self.pages_QWidget[page_index]
            x_offset = calculate_x_offset(label)
            x = self.add_text.x() - x_offset
            y = self.add_text.y() + self.add_text.height()
            self.viewmodel.add_text(text, x, y, page_index)
        self.add_text.deleteLater()
        self.add_text = None
        self.page_manager.rerender_page(page_index)


    def move_text(self,sender_widget,x,y,bbox):
        text_data = sender_widget.text_data
        label = sender_widget.parent()
        x_offset = calculate_x_offset(label)
        y_offset = sender_widget.height() * 0.66
        self.viewmodel.move_text(x - x_offset, y + y_offset, text_data, bbox)
        self.page_manager.rerender_page(self.viewmodel.current_page)
        new_bbox = (sender_widget.x()-x_offset, sender_widget.y(), sender_widget.x()-x_offset+sender_widget.width(),sender_widget.y() + sender_widget.height())
        sender_widget.bbox = new_bbox


    def prepare_edit_mode(self, page_index):
        label = self.pages_QWidget[page_index]
        padding = 5
        spans = self.viewmodel.get_spans_i(page_index)
        for size,font,color,text,bbox in spans:
            text_data = TextData(text,font,size,color)
            x = int(bbox[0])
            y = int(bbox[1])
            width = int(bbox[2] - bbox[0])
            height = int(bbox[3] - bbox[1])
            edit_text = EditTextQLabel(text_data, width + padding, height + padding,bbox,self.viewmodel, label)
            x_offset = calculate_x_offset(label)
            edit_text.move(x + x_offset - padding, y)
            edit_text.coords.connect(lambda x,y,bbox, w=edit_text: self.move_text(w,x,y,bbox))
