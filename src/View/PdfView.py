from PySide6.QtGui import QPixmap, QActionGroup, QColor, QPainter, QIcon, QAction, QPen, QFont
from PySide6.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QFileDialog, QLabel, QHBoxLayout, \
    QLineEdit, QComboBox, QSpinBox, QColorDialog, QToolButton, QMenu, QApplication
from PySide6.QtCore import Qt, QTimer

from src.View.DraggableLineEdit import DraggableLineEdit
from src.View.EditTextQLabel import EditTextQLabel
from src.View.ImageTool import ImageTool
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
            self.page_clicked,
            self._on_pages_loaded
        )
        self.text_tool = TextTool(
            self.viewmodel,
            self.pages_QWidget,
            self.page_manager
        )
        self.image_tool = ImageTool(
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


        self.ui.actionView.setChecked(True)
        self.viewmodel.set_mode(EditorMode.VIEW)

        self.setup_connections()
        self.setup_file_menu()

    def setup_file_menu(self):
        self.file_btn = QToolButton(self.ui.toolBar)
        self.file_btn.setText("File")
        self.file_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.file_btn.setStyleSheet("""
            QToolButton::menu-indicator {
                image: none;
            }
            QToolButton:hover {
                background-color: rgba(0, 0, 0, 20);
            }
        """)
        self.file_menu = QMenu(self.file_btn)
        self.file_menu.addAction("Open PDF...", self._open_file)
        self.file_menu.addAction("Save", self._save_file)
        self.file_menu.addAction("Save As...", self._save_file_as)
        self.file_btn.setMenu(self.file_menu)
        self.ui.toolBar.insertWidget(self.ui.actionView, self.file_btn)
        self.ui.toolBar.insertSeparator(self.ui.actionView)


    def setup_connections(self):
        self.ui.actionView.triggered.connect(lambda: self.viewmodel.set_mode(EditorMode.VIEW))
        self.ui.actionAdd_Text.triggered.connect(lambda: self.viewmodel.set_mode(EditorMode.ADD_TEXT))
        self.ui.actionEdit_Text.triggered.connect(lambda: self.viewmodel.set_mode(EditorMode.EDIT_TEXT))
        self.ui.actionAdd_Image.triggered.connect(self._on_add_image_clicked)
        self.viewmodel.page_number_changed.connect(self.set_selector)
        self.viewmodel.mode_changed.connect(self.mode_changed)
        self.ui.prev_btn.clicked.connect(self._prev_page)
        self.ui.next_btn.clicked.connect(self._next_page)
        self.ui.page_selector.returnPressed.connect(self._selector_pressed)
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
        self.font_choose.addItems(["Helvetica", "Times New Roman", "Courier New"])
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

        self.overlay_btn = QPushButton("Before text")
        self.overlay_btn.setCheckable(True)
        self.overlay_btn.setChecked(True)
        self.overlay_btn.clicked.connect(self._toggle_overlay)
        self.ui.toolBar_2.addWidget(self.overlay_btn)

    def _toggle_overlay(self, checked):
        self.image_tool.overlay = checked
        self.overlay_btn.setText("Before text" if checked else "Behind text")

    def _on_pages_loaded(self, start: int, end: int):
        if self.viewmodel.mode == EditorMode.EDIT_TEXT:
            QTimer.singleShot(0, lambda: self._apply_edit_labels(start, end))

    def _apply_edit_labels(self, start: int, end: int):
        self.ui.scrollArea.widget().layout().activate()
        QApplication.processEvents()
        for i in range(start, end):
            self.text_tool.prepare_edit_mode_i(i)


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
        if self.viewmodel.current_path:
            override = self.text_tool.get_override_spans_for_save()
            images = self.image_tool.get_override_images_for_save()
            self.viewmodel.save_file(self.viewmodel.current_path, override, images)

    def _save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save As", "", "Pdf Files (*.pdf)")
        if file_path != "":
            override = self.text_tool.get_override_spans_for_save()
            images = self.image_tool.get_override_images_for_save()
            self.viewmodel.save_file_as(file_path, override, images)


    def _open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(None, "Open PDF", "", "Pdf Files (*.pdf)")
        if file_path != "":
            self.text_tool.clear()
            self.image_tool.clear()
            self.page_manager.clear_pages()
            self.viewmodel.open_file(file_path)
            self.ui.total.setText(f"/{self.viewmodel.get_total()}")
            self.ui.page_selector.setText("1")
            self.page_manager.load_group()
            self._update_font_list()
            self.ui.actionView.setChecked(True)
            self.viewmodel.set_mode(EditorMode.VIEW)

    def _update_font_list(self):
        self.font_choose.blockSignals(True)
        self.font_choose.clear()
        self.font_choose.addItems(["Helvetica", "Times New Roman", "Courier New"])
        for display_name, xref in self.viewmodel.get_pdf_fonts():
            self.font_choose.addItem(display_name, xref)
        self.font_choose.blockSignals(False)

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
        xref = self.font_choose.currentData()
        if xref is not None:
            self.viewmodel.set_current_font(text)
            self.viewmodel.current_font_xref = xref
        else:
            font = self.viewmodel.font_pyside6_to_pymupdf(text)
            self.viewmodel.set_current_font(font)
            self.viewmodel.current_font_xref = 0
        if self.text_tool.add_text != None:
            self.text_tool.add_text.xref = self.viewmodel.current_font_xref
            try:
                self.text_tool.add_text.apply_change(
                    self.viewmodel.current_font,
                    self.viewmodel.current_fontsize,
                    self.viewmodel.current_color
                )
            except RuntimeError:
                self.text_tool.add_text = None

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
            self.text_tool.prepare_edit_mode()
        else:
            self.text_tool.clear_edit_labels()

    def page_clicked(self, x, y, page_index):
        if self.viewmodel.mode == EditorMode.VIEW:
            return

        if self.viewmodel.mode == EditorMode.ADD_TEXT:
            self.text_tool.add_text_func(x, y, page_index)

        if self.viewmodel.mode == EditorMode.ADD_IMAGE:
            self.image_tool.add_image_func(page_index)

    def _on_add_image_clicked(self):
        self.image_tool.add_image_func(self.viewmodel.current_page)