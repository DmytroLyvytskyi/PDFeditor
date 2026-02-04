from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QFileDialog, QLabel, QHBoxLayout, \
    QLineEdit
from PySide6.QtCore import Qt
from untitled import Ui_MainWindow
class PdfView(QMainWindow):
    def __init__(self,viewmodel):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.viewmodel = viewmodel
        self.viewmodel.page_changed.connect(self.show_page)

        self.ui.open_btn.clicked.connect(self._open_file)
        self.ui.prev_btn.clicked.connect(self._prev_page)
        self.ui.next_btn.clicked.connect(self._next_page)
        self.ui.page_selector.returnPressed.connect(self._selector_pressed)



    def _open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(None, "Open PDF", "", "Pdf Files (*.pdf)")
        if file_path != "":
            self.viewmodel.open_file(file_path)
            self.ui.total.setText(f"/{self.viewmodel.get_total()}")


    def show_page(self, image):
        if image is not None:
            pixmap = QPixmap.fromImage(image)
            self.ui.label.setPixmap(pixmap)
            self.ui.page_selector.setText(str(self.viewmodel.get_current_page_number()))



    def _prev_page(self):
        self.viewmodel.prev_page()

    def _next_page(self):
        self.viewmodel.next_page()


    def _selector_pressed(self):
        self.viewmodel.set_current_page_number(min(int(self.ui.page_selector.text()),self.viewmodel.get_total()))
