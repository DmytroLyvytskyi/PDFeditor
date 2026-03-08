from PySide6.QtGui import QImageReader
from PySide6.QtWidgets import QFileDialog

from src.View.DraggableImage import DraggableImage
from src.View.ImageData import ImageData
from src.View.utils import calculate_x_offset


class ImageTool:
    def __init__(self, viewmodel, pages_QWidget, page_manager):
        self.viewmodel = viewmodel
        self.pages_QWidget = pages_QWidget
        self.page_manager = page_manager
        self.drag_images: dict[int, list] = {}
        self.overlay = True

    def add_image_func(self, page_index):
        path, _ = QFileDialog.getOpenFileName(None, "Open Image", "", "Images (*.png *.jpg *.jpeg)")
        if not path:
            return
        label = self.pages_QWidget[page_index]
        x_offset = calculate_x_offset(label)
        scale_x, scale_y = self._get_scale(page_index, label)
        reader = QImageReader(path)
        img_size = reader.size()
        if img_size.isValid() and img_size.height() > 0:
            aspect = img_size.width() / img_size.height()
        else:
            aspect = 1.0
        screen_w = int(150 * scale_x)
        screen_h = int(screen_w / aspect)
        screen_x = int(50 * scale_x + x_offset)
        screen_y = int(50 * scale_y)
        widget = DraggableImage(path, screen_x, screen_y, screen_w, screen_h, label)
        widget.raise_()
        if page_index not in self.drag_images:
            self.drag_images[page_index] = []
        self.drag_images[page_index].append(widget)

    def get_override_images_for_save(self):
        result = {}
        for page_index, widgets in self.drag_images.items():
            label = self.pages_QWidget[page_index]
            x_offset = calculate_x_offset(label)
            scale_x, scale_y = self._get_scale(page_index, label)
            page_images = []
            for w in widgets:
                pdf_x = (w.x() - x_offset) / scale_x
                pdf_y = w.y() / scale_y
                pdf_w = w.width() / scale_x
                pdf_h = w.height() / scale_y
                page_images.append(ImageData(w.image_path, pdf_x, pdf_y, pdf_w, pdf_h, self.overlay))
            if page_images != []:
                result[page_index] = page_images
        if result != {}:
            return result
        return None

    def clear(self):
        for widgets in self.drag_images.values():
            for w in widgets:
                try:
                    w.deleteLater()
                except RuntimeError:
                    pass
        self.drag_images.clear()

    def _get_scale(self, page_index, label):
        page_rect = self.viewmodel.Model.file[page_index].rect
        pixmap = label.pixmap()
        scale_x = pixmap.width() / page_rect.width
        scale_y = pixmap.height() / page_rect.height
        return scale_x, scale_y