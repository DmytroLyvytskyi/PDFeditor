from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QFileDialog, QLabel, QHBoxLayout, \
    QLineEdit
from PySide6.QtCore import Qt

class PdfView(QMainWindow):
    def __init__(self,viewmodel):
        super().__init__()
        self.viewmodel = viewmodel
        self.viewmodel.page_changed.connect(self.show_page)


        self.setWindowTitle("PdfEditor")


        self.open_btn = QPushButton("Open Pdf")
        self.open_btn.clicked.connect(self._open_file)
        self.prev_btn = QPushButton("<-")
        self.prev_btn.clicked.connect(self._prev_page)
        self.next_btn = QPushButton("->")
        self.next_btn.clicked.connect(self._next_page)
        self.page_selector = QLineEdit()
        self.page_selector.returnPressed.connect(self._selector_pressed)
        self.total = QLabel("/")


        self.page_selector.setFixedWidth(30)



        self.label = QLabel("No PDF loaded")
        self.label.setAlignment(Qt.AlignCenter)

        top = QHBoxLayout()
        top.addWidget(self.prev_btn)
        top.addStretch()
        top.addWidget(self.page_selector)
        top.addWidget(self.total)
        top.addStretch()
        top.addWidget(self.next_btn)

        bottom = QHBoxLayout()
        bottom.addWidget(self.open_btn)

        layout = QVBoxLayout()
        layout.addLayout(top)
        layout.addWidget(self.label)
        layout.addLayout(bottom)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)






    def _open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(None, "Open PDF", "", "Pdf Files (*.pdf)")
        if file_path != "":
            self.viewmodel.open_file(file_path)
            self.total.setText(f"/{self.viewmodel.get_total()}")


    def show_page(self, image):
        if image is not None:
            pixmap = QPixmap.fromImage(image)
            self.label.setPixmap(pixmap)
            self.page_selector.setText(str(self.viewmodel.get_current_page_number()))



    def _prev_page(self):
        self.viewmodel.prev_page()

    def _next_page(self):
        self.viewmodel.next_page()


    def _selector_pressed(self):
        self.viewmodel.set_current_page_number(min(int(self.page_selector.text()),self.viewmodel.get_total()))
