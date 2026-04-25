import math

from PySide6.QtGui import QImageReader
from PySide6.QtWidgets import QFileDialog

from src.View.DraggableImage import DraggableImage
from src.View.ImageData import ImageData
from src.View.utils import calculate_x_offset, get_scale


class ImageTool:
    def __init__(self, viewmodel, pages_QWidget, page_manager, on_dirty=None):
        self.viewmodel = viewmodel
        self.pages_QWidget = pages_QWidget
        self.page_manager = page_manager
        self.drag_images = {}
        self.committed_images = {}
        self.edit_images = {}
        self._dirty_pages = set()
        self.overlay = True
        self.selected_image = None
        self.on_dirty = on_dirty

    def add_image_func(self, page_index):
        path, _ = QFileDialog.getOpenFileName(
            None, "Open Image", "",
            "Images (*.png *.jpg *.jpeg *.jfif *.gif)"
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
        widget.selected.connect(self._on_image_selected)
        widget.raise_()
        collection.append(widget)
        self._on_image_selected(widget)
        return True

    def commit_page(self, page_index):
        widgets = self.drag_images.get(page_index, [])
        if not widgets:
            return

        if page_index not in self.committed_images:
            existing = [
                ImageData(
                    img['path'], img['x'], img['y'], img['w'], img['h'],
                    img.get('overlay', True), img.get('rotation', 0),img.get('original_path', img['path']))
                for img in self.viewmodel.get_images_i(page_index)]
        else:
            existing = self.committed_images[page_index]

        new_images = []
        for w in widgets:
            img_data = self._widget_to_image_data(w, page_index)
            self.viewmodel.insert_image(page_index, img_data)
            new_images.append(img_data)
            w.hide()
            w.deleteLater()
        self.drag_images.pop(page_index)

        self.committed_images[page_index] = existing + new_images

        self.page_manager.rerender_page(page_index)
        if self.on_dirty:
            self.on_dirty()

    def prepare_edit_mode_i(self, page_index):
        if page_index in self.edit_images:
            return
        if page_index >= len(self.pages_QWidget):
            return
        label = self.pages_QWidget[page_index]
        x_offset = calculate_x_offset(label)
        scale_x, scale_y = get_scale(self.viewmodel, page_index, label)
        self.edit_images[page_index] = []
        collection = self.edit_images[page_index]

        if page_index in self.committed_images:
            source_list = [
                {'path': d.path, 'original_path': d.original_path,
                 'x': d.x, 'y': d.y, 'w': d.width, 'h': d.height,
                 'rotation': d.rotation, 'overlay': d.overlay}
                for d in self.committed_images[page_index]
            ]
        else:
            source_list = self.viewmodel.get_images_i(page_index)

        for img in source_list:
            screen_x = round(img['x'] * scale_x + x_offset)
            screen_y = round(img['y'] * scale_y)
            screen_w = round(img['w'] * scale_x)
            screen_h = round(img['h'] * scale_y)
            on_delete = self._make_edit_delete_callback(collection, page_index)
            widget = DraggableImage(
                img['path'], screen_x, screen_y, screen_w, screen_h,
                overlay=img.get('overlay', self.overlay),
                on_delete=on_delete,
                parent=label
            )
            widget._original_path = img.get('original_path', img['path'])
            widget.rotation = img.get('rotation', 0)

            self._setup_widget_base_size(widget, screen_w, screen_h)
            widget.selected.connect(self._on_image_selected)
            widget.moved.connect(lambda w, pi=page_index: self._dirty_pages.add(pi))
            widget.raise_()
            collection.append(widget)

        blank_rects = []
        for img in source_list:
            bx = round(img['x'] * scale_x)
            by = round(img['y'] * scale_y)
            bw = round(img['w'] * scale_x)
            bh = round(img['h'] * scale_y)
            blank_rects.append((bx, by, bw, bh))
        if blank_rects:
            self.page_manager.rerender_page(page_index, blank_rects=blank_rects)

    def _make_edit_delete_callback(self, collection, page_index):
        def on_delete(w):
            if w in collection:
                collection.remove(w)
            if w is self.selected_image:
                self.selected_image = None
            self._recommit_page_to_pdf(page_index)

        return on_delete


    def prepare_edit_mode(self):
        self.commit_edit_images()
        for i in range(len(self.pages_QWidget)):
            self.prepare_edit_mode_i(i)



    def commit_edit_images(self):
        for page_index, widgets in list(self.edit_images.items()):
            if not widgets:
                continue
            page_images = [self._widget_to_image_data(w, page_index) for w in widgets]
            if page_index in self._dirty_pages:
                self.viewmodel.save_snapshot(page_index)
            self.viewmodel.commit_image_edit(page_index, page_images)
            self.committed_images[page_index] = page_images
            for w in widgets:
                try:
                    w.deleteLater()
                except RuntimeError:
                    pass
            self.page_manager.rerender_page(page_index)
        self.edit_images.clear()
        self._dirty_pages.clear()
        if self.on_dirty:
            self.on_dirty()

    def clear(self):
        for widgets in self.drag_images.values():
            for w in widgets:
                try:
                    w.deleteLater()
                except RuntimeError:
                    pass
        self.drag_images.clear()
        self.commit_edit_images()
        self.committed_images.clear()



    def commit_all(self):
        for page_index in list(self.drag_images.keys()):
            self.commit_page(page_index)

    def _on_image_selected(self, widget):
        if self.selected_image and self.selected_image is not widget:
            try:
                self.selected_image.deselect()
            except RuntimeError:
                pass
        self.selected_image = widget

    def delete_selected(self):
        if self.selected_image is None:
            return
        w = self.selected_image
        self.selected_image = None
        for page_index, lst in list(self.drag_images.items()):
            if w in lst:
                lst.remove(w)
                w.deleteLater()
                return
        for page_index, lst in list(self.edit_images.items()):
            if w in lst:
                lst.remove(w)
                w.deleteLater()
                self._recommit_page_to_pdf(page_index)
                return

    def _widget_to_image_data(self, w, page_index):
        label = self.pages_QWidget[page_index]
        x_offset = calculate_x_offset(label)
        scale_x, scale_y = get_scale(self.viewmodel, page_index, label)
        cx = w.x() + w.width() / 2
        cy = w.y() + w.height() / 2

        if w.rotation % 360 == 0:
            pdf_x = (cx - w._base_w / 2 - x_offset) / scale_x
            pdf_y = (cy - w._base_h / 2) / scale_y
            pdf_w = w._base_w / scale_x
            pdf_h = w._base_h / scale_y
        else:
            pdf_x = (w.x() - x_offset) / scale_x
            pdf_y = w.y() / scale_y
            pdf_w = w.width() / scale_x
            pdf_h = w.height() / scale_y

        return ImageData(w._original_path, pdf_x, pdf_y, pdf_w, pdf_h,w.overlay, w.rotation,w._original_path)



    def _recommit_page_to_pdf(self, page_index):
        widgets = self.edit_images.get(page_index, [])
        page_images = [self._widget_to_image_data(w, page_index) for w in widgets]
        self.viewmodel.save_snapshot(page_index)
        self.viewmodel.commit_image_edit(page_index, page_images)
        self.committed_images[page_index] = page_images
        self._dirty_pages.discard(page_index)
        self.page_manager.rerender_page(page_index)



    def _setup_widget_base_size(self, widget, screen_w, screen_h):
        reader = QImageReader(widget._original_path)
        orig_size = reader.size()
        if not orig_size.isValid() or orig_size.height() == 0:
            return
        orig_aspect = orig_size.width() / orig_size.height()
        widget._aspect = orig_aspect
        if widget.rotation % 360 != 0:
            angle_rad = math.radians(widget.rotation)
            cos_a = abs(math.cos(angle_rad))
            sin_a = abs(math.sin(angle_rad))
            base_w = screen_w / (cos_a + sin_a / orig_aspect)
            widget._base_w = int(base_w)
            widget._base_h = int(base_w / orig_aspect)
        else:
            widget._base_w = screen_w
            widget._base_h = screen_h