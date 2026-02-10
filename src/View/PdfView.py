from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QFileDialog, QLabel, QHBoxLayout, \
    QLineEdit
from PySide6.QtCore import Qt, QTimer

from src.View.PageQLabel import PageQLabel
from untitled import Ui_MainWindow
class PdfView(QMainWindow):
    def __init__(self,viewmodel):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.viewmodel = viewmodel
        self.viewmodel.page_number_changed.connect(self.set_selector)

        self.ui.open_btn.clicked.connect(self._open_file)
        self.ui.prev_btn.clicked.connect(self._prev_page)
        self.ui.next_btn.clicked.connect(self._next_page)
        self.ui.page_selector.returnPressed.connect(self._selector_pressed)
        self.ui.save_btn.clicked.connect(self._save_file)


        self.ui.scrollArea.verticalScrollBar().valueChanged.connect(self._scrolled)

        self.pages_QWidget = []

    def _save_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save", "", "Pdf Files (*.pdf)")
        if file_path != "":
            self.viewmodel.save_file(file_path)

    def _open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(None, "Open PDF", "", "Pdf Files (*.pdf)")
        if file_path != "":
            self.viewmodel.open_file(file_path)
            self.ui.total.setText(f"/{self.viewmodel.get_total()}")
            self.load_group()


    def _scrolled(self):
        # 1 page ≈ 850
        #print(self.ui.scrollArea.verticalScrollBar().sliderPosition(), self.ui.scrollArea.verticalScrollBar().maximum())
        # print(self.ui.page_scroll.count())

        max_height = self.ui.scrollArea.verticalScrollBar().maximum()
        cur_height = self.ui.scrollArea.verticalScrollBar().value()
        #print(max_height,cur_height)
        if ((max_height - cur_height < 850*4) and self.ui.page_scroll.count() < self.viewmodel.get_total()):
            self.load_group()
        self.viewmodel.set_current_page_number(self.calculate_page()+1)#page number "for pc"


    def load_group(self):
        layout = self.ui.page_scroll
        pages = self.viewmodel.get_next_pages(5)
        start_index = len(self.pages_QWidget)
        for index, i in enumerate(pages):
            image = i
            pixmap = QPixmap.fromImage(image)
            page_label = PageQLabel(pixmap,index + start_index)
            #page_label.setAlignment(Qt.AlignCenter)
            #page_label.setPixmap(pixmap)
            page_label.coords.connect(self.page_clicked)
            layout.addWidget(page_label)
            self.pages_QWidget.append(page_label)

    def rerender_page(self, page_index):
        new = self.viewmodel.get_page_i(page_index)
        self.pages_QWidget[page_index].setPixmap(QPixmap.fromImage(new))

    def page_clicked(self, x, y, page_index):
        label = self.pages_QWidget[page_index]
        pixmap = label.pixmap()
        x_offset = label.width()/2 - pixmap.width()/2
        self.add_text = QLineEdit(label)
        self.add_text.move(x+x_offset,y)
        self.add_text.show()
        self.add_text.setFocus()
        self.add_text.returnPressed.connect(lambda: self.save_text(x,y+self.add_text.height(),page_index))#left bottom and left top
        #without offset because pymupdf works with the coordinates of the file


    def save_text(self, x, y, page_index):
        text = self.add_text.text()
        if text != "":
            self.viewmodel.add_text(text, x, y, page_index)
        self.add_text.deleteLater()
        self.add_text = None
        self.rerender_page(page_index)




    def scroll_to(self, num):
        self.ui.scrollArea.ensureWidgetVisible(self.pages_QWidget[num])



    def _prev_page(self):
        self.viewmodel.prev_page()
        self.scroll_to(self.viewmodel.current_page)

    def _next_page(self):
        self.viewmodel.next_page()
        self.scroll_to(self.viewmodel.current_page)


    def _selector_pressed(self):
        num = min(int(self.ui.page_selector.text()),self.viewmodel.get_total())
        self.viewmodel.set_current_page_number(num) # page number for human
        while len(self.pages_QWidget) < num:
            self.load_group()
        self.ui.scrollArea.widget().layout().activate()
        QTimer.singleShot(0, lambda: self.scroll_to(self.viewmodel.current_page))


    def calculate_page(self):
        cur_height = self.ui.scrollArea.verticalScrollBar().value()
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


    def set_selector(self):
        self.ui.page_selector.setText(str(self.viewmodel.get_current_page_number()))

