import math

from PySide6.QtGui import QImageReader
from PySide6.QtWidgets import QFileDialog

from src.View.DraggableImage import DraggableImage
from src.View.ImageData import ImageData
from src.View.utils import calculate_x_offset, get_scale


class ImageTool:
    def __init__(self, viewmodel, pages_QWidget, page_manager):
        self.viewmodel = viewmodel
        self.pages_QWidget = pages_QWidget
        self.page_manager = page_manager
        self.drag_images: dict[int, list] = {}
        self.committed_images: dict[int, list] = {}
        self.edit_images: dict[int, list] = {}
        self.overlay = True

    def add_image_func(self, page_index):
        path, _ = QFileDialog.getOpenFileName(
            None, "Open Image", "",
            "Images (*.png *.jpg *.jpeg)"
        )
        if path == "":
            return False
        label = self.pages_QWidget[page_index]
        x_offset = calculate_x_offset(label)
        scale_x, scale_y = get_scale(self.viewmodel, page_index, label)
        reader = QImageReader(path)
        img_size = reader.size()
        aspect = (img_size.width() / img_size.height() if img_size.isValid() and img_size.height() > 0 else 1.0)
        screen_w = int(150 * scale_x)
        screen_h = int(screen_w / aspect)
        screen_x = int(50 * scale_x + x_offset)
        screen_y = int(50 * scale_y)
        if page_index not in self.drag_images:
            self.drag_images[page_index] = []
        collection = self.drag_images[page_index]
        widget = DraggableImage(
            path, screen_x, screen_y, screen_w, screen_h,
            overlay=self.overlay,
            on_delete=lambda w: collection.remove(w) if w in collection else None,
            parent=label
        )
        widget.raise_()
        collection.append(widget)
        return True

    def commit_page(self, page_index):
        widgets = self.drag_images.get(page_index, [])
        if not widgets:
            return
        label = self.pages_QWidget[page_index]
        x_offset = calculate_x_offset(label)
        scale_x, scale_y = get_scale(self.viewmodel, page_index, label)
        for w in widgets:
            pdf_x = (w.x() - x_offset) / scale_x
            pdf_y = w.y() / scale_y
            pdf_w = w.width() / scale_x
            pdf_h = w.height() / scale_y
            img_data = ImageData(w.image_path, pdf_x, pdf_y, pdf_w, pdf_h, w.overlay)
            self.viewmodel.insert_image(page_index, img_data)
            if page_index not in self.committed_images:
                self.committed_images[page_index] = []
            self.committed_images[page_index].append(img_data)
            w.hide()
            w.deleteLater()
        self.drag_images.pop(page_index)
        self.page_manager.rerender_page(page_index)

    def prepare_edit_mode_i(self, page_index):
        if page_index in self.edit_images:
            return
        if page_index >= len(self.pages_QWidget):
            return
        label = self.pages_QWidget[page_index]
        x_offset = calculate_x_offset(label)
        scale_x, scale_y = get_scale(self.viewmodel, page_index, label)
        images = self.viewmodel.get_images_i(page_index)
        self.edit_images[page_index] = []
        collection = self.edit_images[page_index]
        for img in images:
            screen_x = int(img['x'] * scale_x + x_offset)
            screen_y = int(img['y'] * scale_y)
            screen_w = math.ceil(img['w'] * scale_x)
            screen_h = math.ceil(img['h'] * scale_y)
            widget = DraggableImage(
                img['path'], screen_x, screen_y, screen_w, screen_h,
                overlay=self.overlay,
                on_delete=lambda w, c=collection: c.remove(w) if w in c else None,
                parent=label
            )
            widget.raise_()
            collection.append(widget)

    def prepare_edit_mode(self):
        self.clear_edit_images()
        for i in range(len(self.pages_QWidget)):
            self.prepare_edit_mode_i(i)

    def clear_edit_images(self):
        self.commit_edit_images()

    def commit_edit_images(self):
        for page_index, widgets in list(self.edit_images.items()):
            if not widgets:
                continue
            label = self.pages_QWidget[page_index]
            x_offset = calculate_x_offset(label)
            scale_x, scale_y = get_scale(self.viewmodel, page_index, label)
            page_images = []
            for w in widgets:
                pdf_x = (w.x() - x_offset) / scale_x
                pdf_y = w.y() / scale_y
                pdf_w = w.width() / scale_x
                pdf_h = w.height() / scale_y
                page_images.append(ImageData(w.image_path, pdf_x, pdf_y, pdf_w, pdf_h, w.overlay))
            self.viewmodel.commit_image_edit(page_index, page_images)
            for w in widgets:
                try:
                    w.deleteLater()
                except RuntimeError:
                    pass
            self.page_manager.rerender_page(page_index)
        self.edit_images.clear()


    def clear(self):
        for widgets in self.drag_images.values():
            for w in widgets:
                try:
                    w.deleteLater()
                except RuntimeError:
                    pass
        self.drag_images.clear()
        self.committed_images.clear()
        self.clear_edit_images()

    def commit_all(self):
        for page_index in list(self.drag_images.keys()):
            self.commit_page(page_index)