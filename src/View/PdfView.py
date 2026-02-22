from PySide6.QtGui import QPixmap, QActionGroup, QColor, QPainter, QIcon, QAction, QPen, QFont
from PySide6.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QFileDialog, QLabel, QHBoxLayout, \
    QLineEdit, QComboBox, QSpinBox, QColorDialog
from PySide6.QtCore import Qt, QTimer

from src.View.DraggableLineEdit import DraggableLineEdit
from src.View.EditTextQLabel import EditTextQLabel
from src.View.PageManager import PageManager
from src.View.PageQLabel import PageQLabel
from src.View.TextData import TextData
from src.View.TextTool import TextTool
from src.ViewModel.EditorMode import EditorMode
from untitled import Ui_MainWindow
class PdfView(QMainWindow):
    def __init__(self,viewmodel):
        super().__init__()

        self.size_choose = None
        self.font_choose = None
        self.current_color = None
        self.viewmodel = viewmodel
        self.pages_QWidget = []

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.page_manager = PageManager(
            self.viewmodel,
            self.ui.scrollArea,
            self.ui.page_scroll,
            self.pages_QWidget,
            self.page_clicked
        )
        self.text_tool = TextTool(
            self.viewmodel,
            self.pages_QWidget,
            self.page_manager
        )
        self.setup_toolbar()
        self.ui.toolBar_2.hide()

        self.mode_group = QActionGroup(self)
        self.mode_group.addAction(self.ui.actionView)
        self.mode_group.addAction(self.ui.actionAdd_Text)
        self.mode_group.addAction(self.ui.actionEdit_Text)
        self.mode_group.setExclusive(True)

        self.ui.actionAdd_Text.setChecked(True)
        self.viewmodel.set_mode(EditorMode.ADD_TEXT)

        self.setup_connections()

    def setup_connections(self):
        self.ui.actionView.triggered.connect(lambda: self.viewmodel.set_mode(EditorMode.VIEW))
        self.ui.actionAdd_Text.triggered.connect(lambda: self.viewmodel.set_mode(EditorMode.ADD_TEXT))
        self.ui.actionEdit_Text.triggered.connect(lambda: self.viewmodel.set_mode(EditorMode.EDIT_TEXT))
        self.viewmodel.page_number_changed.connect(self.set_selector)
        self.viewmodel.mode_changed.connect(self.mode_changed)
        self.ui.open_btn.clicked.connect(self._open_file)
        self.ui.prev_btn.clicked.connect(self._prev_page)
        self.ui.next_btn.clicked.connect(self._next_page)
        self.ui.page_selector.returnPressed.connect(self._selector_pressed)
        self.ui.save_btn.clicked.connect(self._save_file)
        self.ui.scrollArea.verticalScrollBar().valueChanged.connect(self._scrolled)

    def setup_toolbar(self):
        toolbar = self.ui.toolBar_2
        toolbar.addWidget(QLabel("Color: "))
        self.ui.color_choose = QAction("Choose Color", self)
        toolbar.addAction(self.ui.color_choose)

        self.ui.color_choose.triggered.connect(self.open_color_dialog)

        self.current_color = QColor(0, 0, 0)
        self.update_color_action_icon()

        toolbar.addWidget(QLabel("Font: "))
        self.font_choose = QComboBox()
        self.font_choose.addItems(["Helvetica", "Times New Roman", "Courier New"]) # add detection of fonts used in pdf !!
        self.font_choose.setFixedWidth(150)
        toolbar.addWidget(self.font_choose)

        toolbar.addWidget(QLabel("Size: "))
        self.size_choose = QSpinBox()
        self.size_choose.setRange(5, 80)
        self.size_choose.setValue(12)
        self.size_choose.setSuffix(" pt")
        toolbar.addWidget(self.size_choose)

        self.font_choose.currentTextChanged.connect(self.change_font)
        self.size_choose.valueChanged.connect(self.change_size)

    def _prev_page(self):
        self.viewmodel.prev_page()
        self.page_manager.scroll_to(self.viewmodel.current_page)

    def _next_page(self):
        self.viewmodel.next_page()
        self.page_manager.scroll_to(self.viewmodel.current_page)


    def _selector_pressed(self):
        num = min(int(self.ui.page_selector.text()),self.viewmodel.get_total())
        self.viewmodel.set_current_page_number(num) # page number for human
        while len(self.pages_QWidget) < num:
            self.page_manager.load_group()
        self.ui.scrollArea.widget().layout().activate()
        QTimer.singleShot(0, lambda: self.page_manager.scroll_to(self.viewmodel.current_page))

    def set_selector(self):
        self.ui.page_selector.setText(str(self.viewmodel.get_current_page_number()))


    def _save_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save", "", "Pdf Files (*.pdf)")
        if file_path != "":
            self.viewmodel.save_file(file_path)

    def _open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(None, "Open PDF", "", "Pdf Files (*.pdf)")
        if file_path != "":
            self.viewmodel.open_file(file_path)
            self.ui.total.setText(f"/{self.viewmodel.get_total()}")
            self.page_manager.load_group()


    def _scrolled(self):
        # 1 page ≈ 850
        #print(self.ui.scrollArea.verticalScrollBar().sliderPosition(), self.ui.scrollArea.verticalScrollBar().maximum())
        # print(self.ui.page_scroll.count())

        max_height = self.ui.scrollArea.verticalScrollBar().maximum()
        cur_height = self.ui.scrollArea.verticalScrollBar().value()
        #print(max_height,cur_height)
        if ((max_height - cur_height < 850*4) and self.ui.page_scroll.count() < self.viewmodel.get_total()):
            self.page_manager.load_group()
        self.viewmodel.set_current_page_number(self.page_manager.calculate_page()+1)#page number "for pc"

    def change_font(self, text):
        font = self.viewmodel.font_pyside6_to_pymupdf(text)
        self.viewmodel.set_current_font(font)
        if self.text_tool.add_text != None:
            self.text_tool.add_text.apply_change(
                self.viewmodel.current_font,
                self.viewmodel.current_fontsize,
                self.viewmodel.current_color
            )

    def change_size(self, value):
        self.viewmodel.set_current_size(value)
        if self.text_tool.add_text != None:
            self.text_tool.add_text.apply_change(
                self.viewmodel.current_font,
                self.viewmodel.current_fontsize,
                self.viewmodel.current_color
            )

    def update_toolbar_visibility(self, mode):
        if mode == EditorMode.VIEW:
            self.ui.toolBar_2.hide()
        else:
            self.ui.toolBar_2.show()

    def update_color_action_icon(self):
        pixmap = QPixmap(16, 16)
        pixmap.fill(self.current_color)
        self.ui.color_choose.setIcon(QIcon(pixmap))

    def open_color_dialog(self):
        color = QColorDialog.getColor(initial=self.current_color)
        if color.isValid():
            self.current_color = color
            self.update_color_action_icon()
            self.viewmodel.set_current_color(self.current_color)
            self.text_tool.add_text.apply_change(
                self.viewmodel.current_font,
                self.viewmodel.current_fontsize,
                self.viewmodel.current_color
            )

    def mode_changed(self,mode):
        self.update_toolbar_visibility(mode)
        if mode == EditorMode.EDIT_TEXT:
            self.text_tool.prepare_edit_mode(self.viewmodel.current_page)

    def page_clicked(self, x, y, page_index):
        if self.viewmodel.mode == EditorMode.VIEW:
            return

        if self.viewmodel.mode == EditorMode.ADD_TEXT:
            self.text_tool.add_text_func(x, y, page_index)
