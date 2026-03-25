from PySide6.QtGui import QPixmap, QPainter, QColor

from src.View.PageQLabel import PageQLabel


class PageManager:
    def __init__(self, viewmodel, scrollArea, layout, pages_QWidget, page_clicked, on_pages_loaded=None):
        self.viewmodel = viewmodel
        self.scrollArea = scrollArea
        self.layout = layout
        self.pages_QWidget = pages_QWidget
        self.page_clicked = page_clicked
        self.on_pages_loaded = on_pages_loaded

    def clear_pages(self):
        while self.layout.count() != 0:
            item = self.layout.takeAt(0)
            item.widget().deleteLater()
        self.pages_QWidget.clear()

    def scroll_to(self, num):
        self.scrollArea.ensureWidgetVisible(self.pages_QWidget[num])

    def calculate_page(self):
        cur_height = self.scrollArea.verticalScrollBar().value()
        left = 0
        right = len(self.pages_QWidget)-1
        while left <= right: #binary search
            mid = (left+right)//2
            if self.pages_QWidget[mid].y()< cur_height:
                left = mid+1
            else:
                right = mid-1
        distance_left = abs(self.pages_QWidget[left].y() - cur_height)
        distance_right = abs(self.pages_QWidget[right].y() - cur_height)
        if (distance_right < distance_left):
            return right
        else:
            return left


    def load_group(self):
        pages = self.viewmodel.get_next_pages(5)
        start_index = len(self.pages_QWidget)
        for index, i in enumerate(pages):
            image = i
            pixmap = QPixmap.fromImage(image)
            page_label = PageQLabel(pixmap,index + start_index)
            page_label.coords.connect(self.page_clicked)
            self.layout.addWidget(page_label)
            self.pages_QWidget.append(page_label)
        if self.on_pages_loaded:
            self.on_pages_loaded(start_index, start_index + len(pages))

    def rerender_page(self, page_index, override_spans=None, blank_rects=None, composite_images=None):
        new = self.viewmodel.get_page_i(page_index, override_spans)
        pixmap = QPixmap.fromImage(new)
        if blank_rects != None or composite_images  != None:
            painter = QPainter(pixmap)
            if blank_rects:
                for x, y, w, h in blank_rects:
                    painter.fillRect(x, y, w, h, QColor(255, 255, 255))
            if composite_images  != None:
                for path, x, y, w, h in composite_images:
                    src = QPixmap(path)
                    if not src.isNull():
                        painter.drawPixmap(x, y, w, h, src)
            painter.end()
        self.pages_QWidget[page_index].setPixmap(pixmap)