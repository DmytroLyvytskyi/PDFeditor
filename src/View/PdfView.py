import os

from PySide6.QtGui import QPixmap, QActionGroup, QColor, QPainter, QIcon, QAction, QPen, QFont
from PySide6.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QFileDialog, QLabel, QHBoxLayout, \
    QLineEdit, QComboBox, QSpinBox, QColorDialog, QToolButton, QMenu, QApplication, QSizePolicy, QMessageBox
from PySide6.QtCore import Qt, QTimer, QEvent

from src.View.DraggableLineEdit import DraggableLineEdit
from src.View.EditTextQLabel import EditTextQLabel
from src.View.ImageTool import ImageTool
from src.View.PageManager import PageManager
from src.View.TextTool import TextTool
from src.ViewModel.EditorMode import EditorMode
from untitled import Ui_MainWindow
_HELP_TEXTS = {
    EditorMode.VIEW: (
        "<b>Shortcuts</b><br>"
        "• Undo: <i>Ctrl+Z</i> &nbsp; Redo: <i>Ctrl+Y</i><br>"
        "• Zoom: <i>Ctrl+Scroll</i> or <i>Ctrl+±</i><br>"
        "<b>Add Text</b><br>"
        "• Save: <i>Enter</i> or click on PDF<br>"
        "• Move: drag with left button<br>"
        "<b>Edit Text</b><br>"
        "• See font: click block<br>"
        "• Edit: double-click → <i>Enter</i><br>"
        "• Delete block: <i>Del or Backspace</i><br>"
        "<b>Add / Edit Image</b><br>"
        "• Layer: right-click → Before/Behind text<br>"
        "• Rotate: ↻ ↺ in toolbar or scroll wheel<br>"
        "• Resize: drag corner handle<br>"
        "• Delete: <i>Del</i><br>"
    ),
    EditorMode.ADD_TEXT: (
        "<b>Add Text</b><br>"
        "• Save: <i>Enter</i> or click on PDF<br>"
        "• Move: drag with left button<br>"
        "• Undo: <i>Ctrl+Z</i>"
    ),
    EditorMode.EDIT_TEXT: (
        "<b>Edit Text</b><br>"
        "• See font: click block<br>"
        "• Edit: double-click → <i>Enter</i><br>"
        "• Delete block: <i>Del or Backspace</i><br>"
        "• Undo / Redo: <i>Ctrl+Z</i> / <i>Ctrl+Y</i>"
    ),
    EditorMode.ADD_IMAGE: (
        "<b>Add Image</b><br>"
        "• Layer: right-click → Before/Behind text<br>"
        "• Rotate: ↻ ↺ in toolbar or scroll wheel<br>"
        "• Save: <i>Enter</i> or click on PDF"
    ),
    EditorMode.EDIT_IMAGE: (
        "<b>Edit Image</b><br>"
        "• Layer: right-click → Before/Behind text<br>"
        "• Rotate: ↻ ↺ in toolbar or scroll wheel<br>"
        "• Resize: drag corner handle<br>"
        "• Delete: <i>Del</i><br>"
        "• Undo / Redo: <i>Ctrl+Z</i> / <i>Ctrl+Y</i>"
    ),
}
class PdfView(QMainWindow):

    def __init__(self,viewmodel):
        super().__init__()

        self.size_choose = None
        self.font_choose = None
        self.current_color = None
        self._dirty = False
        self.viewmodel = viewmodel
        self.pages_QWidget = []
        self._zoom_timer = QTimer()
        self._zoom_timer.setSingleShot(True)
        self._zoom_timer.timeout.connect(self._apply_zoom)
        self._resize_timer = QTimer()
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._apply_resize)

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
            self.page_manager,
            self._mark_dirty,
            self._on_edit_label_selected
        )
        self.image_tool = ImageTool(
            self.viewmodel,
            self.pages_QWidget,
            self.page_manager,
            self._mark_dirty
        )
        self.setup_toolbar()
        self.ui.toolBar_2.hide()

        self.mode_group = QActionGroup(self)
        self.mode_group.addAction(self.ui.actionView)
        self.mode_group.addAction(self.ui.actionAdd_Text)
        self.mode_group.addAction(self.ui.actionEdit_Text)
        self.mode_group.addAction(self.ui.actionEdit_Image)
        self.mode_group.setExclusive(True)


        self.ui.actionView.setChecked(True)
        self.viewmodel.set_mode(EditorMode.VIEW)

        self.setup_connections()
        self.setup_file_menu()
        self._setup_event_filter()
        self._setup_help()
        self.setWindowTitle("PdfEditor")
        self.setWindowIcon(QIcon("icon.ico"))

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
        self.file_menu.addAction("Close", self._close_file)
        self.file_btn.setMenu(self.file_menu)
        self.ui.toolBar.insertWidget(self.ui.actionView, self.file_btn)
        self.ui.toolBar.insertSeparator(self.ui.actionView)


    def setup_connections(self):
        self.ui.actionView.triggered.connect(lambda: self.viewmodel.set_mode(EditorMode.VIEW))
        self.ui.actionAdd_Text.triggered.connect(lambda: self.viewmodel.set_mode(EditorMode.ADD_TEXT))
        self.ui.actionEdit_Text.triggered.connect(lambda: self.viewmodel.set_mode(EditorMode.EDIT_TEXT))
        self.ui.actionEdit_Image.triggered.connect(lambda: self.viewmodel.set_mode(EditorMode.EDIT_IMAGE))
        self.ui.actionAdd_Image.triggered.connect(self._on_add_image_clicked)
        self.viewmodel.history_changed.connect(self._on_history_changed)

        self.viewmodel.zoom_changed.connect(self._on_zoom_changed)
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
        self.font_choose.insertSeparator(3)
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

        self.rotate_cw_btn = QAction("↻", self)
        self.rotate_ccw_btn = QAction("↺", self)
        self.ui.toolBar.addSeparator()
        self.ui.toolBar.addAction(self.rotate_cw_btn)
        self.ui.toolBar.addAction(self.rotate_ccw_btn)
        self.rotate_cw_btn.setVisible(False)
        self.rotate_ccw_btn.setVisible(False)
        self.rotate_cw_btn.triggered.connect(
            lambda: self.image_tool.selected_image.rotate_cw()
            if self.image_tool.selected_image else None)
        self.rotate_ccw_btn.triggered.connect(
            lambda: self.image_tool.selected_image.rotate_ccw()
            if self.image_tool.selected_image else None)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.ui.toolBar.addWidget(spacer)

        self.undo_action = QAction("↩ Undo", self)
        self.redo_action = QAction("↪ Redo", self)
        self.undo_action.setShortcut("Ctrl+Z")
        self.redo_action.setShortcut("Ctrl+Y")
        self.undo_action.setEnabled(False)
        self.redo_action.setEnabled(False)
        self.undo_action.triggered.connect(self._do_undo)
        self.redo_action.triggered.connect(self._do_redo)
        self.ui.toolBar.addSeparator()
        self.ui.toolBar.addAction(self.undo_action)
        self.ui.toolBar.addAction(self.redo_action)
        self.ui.toolBar.addSeparator()

        zoom_out_btn = QAction("🔍−", self)
        zoom_out_btn.setToolTip("Zoom Out (Ctrl+-)")
        zoom_out_btn.triggered.connect(self._zoom_out)
        self.ui.toolBar.addAction(zoom_out_btn)

        self.zoom_label = QLabel("100%")
        self.zoom_label.setFixedWidth(45)
        self.zoom_label.setAlignment(Qt.AlignCenter)
        self.ui.toolBar.addWidget(self.zoom_label)

        zoom_in_btn = QAction("🔍+", self)
        zoom_in_btn.setToolTip("Zoom In (Ctrl++)")
        zoom_in_btn.triggered.connect(self._zoom_in)
        self.ui.toolBar.addAction(zoom_in_btn)

        zoom_reset_btn = QAction("100%", self)
        zoom_reset_btn.setToolTip("Reset Zoom (Ctrl+0)")
        zoom_reset_btn.triggered.connect(self._zoom_reset)
        self.ui.toolBar.addAction(zoom_reset_btn)

        self.ui.toolBar.setStyleSheet("""
            QToolButton:checked {
                background-color: rgba(100, 100, 100, 180);
                color: white;
                border-radius: 4px;
            }
            QToolButton:hover {
                background-color: rgba(0, 0, 0, 30);
                border-radius: 4px;
            }
        """)



    def _setup_help(self):
        self._help_visible = False

        self._help_btn = QPushButton("?", self)
        self._help_btn.setFixedSize(24, 24)
        self._help_btn.setCheckable(True)
        self._help_btn.setToolTip("Show hints")
        self._help_btn.setStyleSheet("""
            QPushButton {
                border-radius: 12px;
                background: #5a9fd4;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: none;
            }
            QPushButton:checked { background: #3a7fb5; }
            QPushButton:hover   { background: #4a8fc4; }
        """)
        self._help_btn.clicked.connect(self._toggle_help)

        self.ui.horizontalLayout.addWidget(self._help_btn)

        self._help_panel = QLabel(self)
        self._help_panel.setVisible(False)
        self._help_panel.setWordWrap(True)
        self._help_panel.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._help_panel.setStyleSheet("""
            QLabel {
                background: #f0f7ff;
                border: 1px solid #5a9fd4;
                border-radius: 6px;
                padding: 8px 10px;
                font-size: 12px;
                color: #1a1a2e;
            }
        """)
        self._help_panel.setFixedWidth(220)
        self._position_help_panel()

    def _position_help_panel(self):
        if not hasattr(self, '_help_panel'):
            return
        sa = self.ui.scrollArea
        panel_h = self._help_panel.sizeHint().height() or 80
        x = sa.x() + sa.width() - 230
        y = sa.y() + sa.height() - panel_h - 10
        self._help_panel.move(x, y)
        self._help_panel.raise_()

    def _toggle_help(self, checked):
        self._help_panel.setVisible(checked)
        if checked:
            self._position_help_panel()
            self._help_panel.raise_()

    def _update_help_text(self, mode):
        if not hasattr(self, '_help_panel'):
            return
        text = _HELP_TEXTS.get(mode, "")
        self._help_panel.setText(text)
        self._help_panel.adjustSize()
        self._help_panel.setFixedWidth(220)
        self._position_help_panel()


    def _setup_event_filter(self):
        QApplication.instance().installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            modifiers = event.modifiers()
            if modifiers == Qt.KeyboardModifier.ControlModifier:
                if key in (Qt.Key.Key_Equal, Qt.Key.Key_Plus):
                    self._zoom_in()
                    return True
                if key == Qt.Key.Key_Minus:
                    self._zoom_out()
                    return True
                if key == Qt.Key.Key_0:
                    self._zoom_reset()
                    return True

            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if self.viewmodel.mode == EditorMode.EDIT_TEXT:
                    if not isinstance(QApplication.focusWidget(), QLineEdit):
                        self.text_tool.commit_selected()
                        return True
            if self.viewmodel.mode == EditorMode.ADD_IMAGE:
                self.image_tool.commit_all()
                self.ui.actionView.setChecked(True)
                self.viewmodel.set_mode(EditorMode.VIEW)
                return True
            if self.viewmodel.mode == EditorMode.EDIT_IMAGE:
                self.image_tool.commit_edit_images()
                self.ui.actionView.setChecked(True)
                self.viewmodel.set_mode(EditorMode.VIEW)
                return True

            if key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
                focused = QApplication.focusWidget()
                if isinstance(focused, QLineEdit):
                    return super().eventFilter(obj, event)
                if self.viewmodel.mode == EditorMode.EDIT_TEXT:
                    self.text_tool.delete_selected()
                    return True
                if self.viewmodel.mode in (EditorMode.ADD_IMAGE, EditorMode.EDIT_IMAGE):
                    self.image_tool.delete_selected()
                    return True

        if event.type() == QEvent.Type.Wheel:
            modifiers = event.modifiers()

            if modifiers == Qt.KeyboardModifier.ControlModifier:
                delta = event.angleDelta().y()
                if delta > 0:
                    self._zoom_in()
                else:
                    self._zoom_out()
                return True

            if self.viewmodel.mode in (EditorMode.ADD_IMAGE, EditorMode.EDIT_IMAGE):
                if self.image_tool.selected_image is not None:
                    try:
                        delta = event.angleDelta().y()
                        step = 5
                        img = self.image_tool.selected_image
                        if delta > 0:
                            img.rotation = (img.rotation - step) % 360
                        else:
                            img.rotation = (img.rotation + step) % 360
                        img._update_size_for_rotation()
                        img.update()
                    except RuntimeError:
                        self.image_tool.selected_image = None
                    return True

        return super().eventFilter(obj, event)

    def _on_pages_loaded(self, start, end):
        if self.viewmodel.mode in (EditorMode.EDIT_TEXT, EditorMode.EDIT_IMAGE):
            QTimer.singleShot(0, lambda: self._apply_edit_mode(start, end))

    def _apply_edit_mode(self, start, end):
        self.ui.scrollArea.widget().layout().activate()
        QApplication.processEvents()
        if self.viewmodel.mode == EditorMode.EDIT_TEXT:
            for i in range(start, end):
                self.text_tool.prepare_edit_mode_i(i)
        elif self.viewmodel.mode == EditorMode.EDIT_IMAGE:
            for i in range(start, end):
                self.image_tool.prepare_edit_mode_i(i)

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
            self.viewmodel.save_file(self.viewmodel.current_path, self._commit_and_get_override(), None)
            self._dirty = False

    def _save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save As", "", "Pdf Files (*.pdf)")
        if file_path:
            self.viewmodel.save_file_as(file_path, self._commit_and_get_override(), None)
            self._dirty = False

    def _commit_and_get_override(self):
        if self.viewmodel.mode == EditorMode.EDIT_IMAGE:
            self.image_tool.commit_edit_images()
        return self.text_tool.get_override_spans_for_save()



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
            self._dirty = False
            self.viewmodel.set_current_font("helv")
            self.viewmodel.current_font_xref = 0
            self.font_choose.blockSignals(True)
            self.font_choose.setCurrentIndex(0)
            self.font_choose.blockSignals(False)

    def _update_font_list(self):
        from src.View.utils import get_system_font_families
        self.font_choose.blockSignals(True)
        self.font_choose.clear()
        self.font_choose.addItems(["Helvetica", "Times New Roman", "Courier New"])
        self.font_choose.insertSeparator(3)
        for display_name, xref in self.viewmodel.get_pdf_fonts():
            self.font_choose.addItem(display_name, xref)
        self.font_choose.insertSeparator(self.font_choose.count())
        for display_name, path in get_system_font_families():
            self.font_choose.addItem(display_name, path)
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
        old_font = self.viewmodel.current_font
        xref = self.font_choose.currentData()
        if isinstance(xref, str):
            self.viewmodel.set_current_font(xref)
            self.viewmodel.current_font_xref = 0
        elif xref is not None:
            self.viewmodel.set_current_font(text)
            self.viewmodel.current_font_xref = xref
        else:
            self.viewmodel.set_current_font(self.viewmodel.font_pyside6_to_pymupdf(text))
            self.viewmodel.current_font_xref = 0

        new_xref = self.viewmodel.current_font_xref
        new_font = self.viewmodel.current_font

        current = self.text_tool.add_text
        if current is not None:
            if isinstance(current, EditTextQLabel):
                check_text = current.text_data.text
                prev_xref = current.text_data.xref
                prev_font = current.text_data.font
            elif isinstance(current, DraggableLineEdit):
                check_text = current.text()
                prev_xref = current.xref
                prev_font = old_font
            else:
                check_text = ""

            if check_text.strip():
                missing = self.viewmodel.get_missing_chars(new_xref, new_font, check_text)
                if missing:
                    unique = ''.join(dict.fromkeys(missing))
                    msg = QMessageBox(self)
                    msg.setWindowTitle("Incompatible font")
                    msg.setText(
                        f"Font \"{text}\" does not contain: {unique}\n"
                        "A similar font can be used instead."
                    )
                    msg.setIcon(QMessageBox.Icon.Warning)
                    similar_btn = msg.addButton("Use similar font", QMessageBox.ButtonRole.AcceptRole)
                    msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
                    msg.exec()

                    if msg.clickedButton() != similar_btn:
                        self._restore_font_combo(prev_xref, prev_font)
                        return

                    from src.View.utils import pymupdf_fonts, category_from_font_name

                    new_data = self.viewmodel.Model.font_cache.get(new_xref)
                    if new_data:
                        category = new_data.get('category', 'serif')
                    else:
                        category = category_from_font_name(new_font)

                    from src.View.utils import find_system_font_by_category
                    similar_font_path = find_system_font_by_category(category, original_name=text)
                    if similar_font_path:
                        similar_font = similar_font_path
                    else:
                        similar_font = pymupdf_fonts.get(category, "tiro")

                    new_font = similar_font
                    new_xref = 0
                    self.viewmodel.set_current_font(new_font)
                    self.viewmodel.current_font_xref = 0
                    xref_for_combo = similar_font if os.path.isfile(similar_font) else 0
                    self._restore_font_combo(xref_for_combo, similar_font)

                    if isinstance(current, EditTextQLabel):
                        current.text_data.xref = 0
                        current.text_data.font = similar_font
                        if current.edit_text:
                            current.edit_text.xref = 0
                    elif isinstance(current, DraggableLineEdit):
                        current.xref = 0

        self.text_tool.apply_style_to_selected(
            new_font, self.viewmodel.current_fontsize,
            self.viewmodel.current_color, xref=new_xref
        )

    def change_size(self, value):
        self.viewmodel.set_current_size(value)
        self.text_tool.apply_style_to_selected(
            self.viewmodel.current_font,
            self.viewmodel.current_fontsize,
            self.viewmodel.current_color
        )

    def update_toolbar_visibility(self, mode):
        is_text = mode in (EditorMode.ADD_TEXT, EditorMode.EDIT_TEXT)
        is_image = mode in (EditorMode.ADD_IMAGE, EditorMode.EDIT_IMAGE)
        self.ui.toolBar_2.setVisible(is_text)
        self.rotate_cw_btn.setVisible(is_image)
        self.rotate_ccw_btn.setVisible(is_image)

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
            self.text_tool.apply_style_to_selected(
                self.viewmodel.current_font,
                self.viewmodel.current_fontsize,
                self.viewmodel.current_color
            )

    def mode_changed(self, mode):
        if (self.text_tool.add_text is not None
                and isinstance(self.text_tool.add_text, DraggableLineEdit)
                and self.text_tool.add_text_page_index is not None):
            try:
                self.text_tool.save_text(0, 0, self.text_tool.add_text_page_index)
            except RuntimeError:
                self.text_tool.add_text = None

        self.update_toolbar_visibility(mode)
        self.update_toolbar_visibility(mode)
        if mode != EditorMode.ADD_IMAGE:
            self.image_tool.commit_all()

        self.viewmodel.set_pending_text_spans(
            self.text_tool.get_override_spans_for_save() or {}
        )
        if mode == EditorMode.EDIT_IMAGE:
            self.image_tool.prepare_edit_mode()
        else:
            self.image_tool.commit_edit_images()

        if mode == EditorMode.EDIT_TEXT:
            self.text_tool.prepare_edit_mode()
        else:
            self.text_tool.clear_edit_labels()

        self._update_help_text(mode)

    def page_clicked(self, x, y, page_index):
        if self.viewmodel.mode == EditorMode.VIEW:
            return
        if self.viewmodel.mode == EditorMode.ADD_TEXT:
            self.text_tool.add_text_func(x, y, page_index)
        elif self.viewmodel.mode == EditorMode.ADD_IMAGE:
            self.image_tool.commit_all()
            self.ui.actionView.setChecked(True)
            self.viewmodel.set_mode(EditorMode.VIEW)

    def _on_add_image_clicked(self):
        if self.image_tool.add_image_func(self.viewmodel.current_page):
            self.viewmodel.set_mode(EditorMode.ADD_IMAGE)

    def _mark_dirty(self):
        self._dirty = True

    def _prompt_save_if_needed(self):
        if not self._dirty or self.viewmodel.current_path is None:
            return True
        from PySide6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setWindowTitle("Unsaved changes")
        msg.setText("You have unsaved changes. Do you want to save them?")
        msg.setIcon(QMessageBox.Icon.Question)
        save_btn = msg.addButton("Save", QMessageBox.ButtonRole.AcceptRole)
        discard_btn = msg.addButton("Don't Save", QMessageBox.ButtonRole.DestructiveRole)
        cancel_btn = msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        msg.exec()
        clicked = msg.clickedButton()
        if clicked == save_btn:
            self._save_file()
            return True
        elif clicked == discard_btn:
            return True
        else:
            return False

    def _close_file(self):
        if not self._prompt_save_if_needed():
            return
        self.text_tool.clear()
        self.image_tool.clear()
        self.page_manager.clear_pages()
        self.viewmodel.close_file()
        self.ui.total.setText("/")
        self.ui.page_selector.setText("")
        self._dirty = False

    def closeEvent(self, event):
        if self._prompt_save_if_needed():
            event.accept()
        else:
            event.ignore()

    def _zoom_in(self):
        self.viewmodel.set_zoom(self.viewmodel.zoom + 0.1)

    def _zoom_out(self):
        self.viewmodel.set_zoom(self.viewmodel.zoom - 0.1)

    def _zoom_reset(self):
        self.viewmodel.set_zoom(1.0)

    def _on_edit_label_selected(self, label):
        from src.View.DraggableLineEdit import DraggableLineEdit as DLE
        if isinstance(label, DLE):
            font_name = self.viewmodel.current_font
            self._update_toolbar_font(font_name, self.viewmodel.current_font_xref)
            return
        td = label.text_data
        self.viewmodel.set_current_font(td.font)
        self.viewmodel.current_font_xref = td.xref
        self.viewmodel.set_current_size(int(td.size))
        self.viewmodel.set_current_color(td.color)
        self.current_color = td.color
        self.update_color_action_icon()
        self.size_choose.blockSignals(True)
        self.size_choose.setValue(int(td.size))
        self.size_choose.blockSignals(False)
        self._update_toolbar_font(td.font, td.xref)

    def _restore_font_combo(self, prev_xref, prev_font):
        self.viewmodel.set_current_font(prev_font)
        self.viewmodel.current_font_xref = prev_xref if isinstance(prev_xref, int) else 0
        self._update_toolbar_font(prev_font, prev_xref)

    def _on_zoom_changed(self, zoom):
        self.zoom_label.setText(f"{int(zoom * 100)}%")
        if not self.pages_QWidget:
            return
        self._zoom_timer.start(120)

    def _apply_zoom(self):
        if not self.pages_QWidget:
            return
        current_page = self.page_manager.calculate_page()

        if self.viewmodel.mode == EditorMode.EDIT_IMAGE:
            self.image_tool.commit_edit_images()
        if self.viewmodel.mode == EditorMode.EDIT_TEXT:
            self.text_tool.clear_edit_labels()

        vis_start, vis_end = self._get_visible_page_range()
        for i in range(vis_start, vis_end):
            self.page_manager.rerender_page(i)

        def rerender_rest():
            for i in range(len(self.pages_QWidget)):
                if i < vis_start or i >= vis_end:
                    self.page_manager.rerender_page(i)
            if self.viewmodel.mode == EditorMode.EDIT_TEXT:
                for i in range(len(self.pages_QWidget)):
                    self.text_tool.prepare_edit_mode_i(i)
            elif self.viewmodel.mode == EditorMode.EDIT_IMAGE:
                for i in range(len(self.pages_QWidget)):
                    self.image_tool.prepare_edit_mode_i(i)

        if self.viewmodel.mode == EditorMode.EDIT_TEXT:
            for i in range(vis_start, vis_end):
                self.text_tool.prepare_edit_mode_i(i)
        elif self.viewmodel.mode == EditorMode.EDIT_IMAGE:
            for i in range(vis_start, vis_end):
                self.image_tool.prepare_edit_mode_i(i)

        QTimer.singleShot(0, rerender_rest)
        self.ui.scrollArea.widget().layout().activate()
        QTimer.singleShot(0, lambda: self.page_manager.scroll_to(current_page))

    def _get_visible_page_range(self):
        if not self.pages_QWidget:
            return 0, 0
        scroll_y = self.ui.scrollArea.verticalScrollBar().value()
        viewport_h = self.ui.scrollArea.viewport().height()
        start, end = len(self.pages_QWidget), 0
        for i, w in enumerate(self.pages_QWidget):
            top = w.y()
            bottom = top + w.height()
            if bottom >= scroll_y and top <= scroll_y + viewport_h:
                start = min(start, i)
                end = max(end, i + 1)
        if start > end:
            return 0, min(3, len(self.pages_QWidget))
        return start, end

    def _update_toolbar_font(self, font_name, xref):
        cb = self.font_choose
        cb.blockSignals(True)

        found_idx = -1

        if isinstance(xref, int) and xref > 0:
            for i in range(cb.count()):
                d = cb.itemData(i)
                if isinstance(d, int) and d == xref:
                    found_idx = i
                    break

        if found_idx == -1 and isinstance(xref, str):
            for i in range(cb.count()):
                d = cb.itemData(i)
                if isinstance(d, str) and d == xref:
                    found_idx = i
                    break

        if found_idx == -1:
            from src.View.utils import find_system_font
            path = find_system_font(font_name)
            if path:
                for i in range(cb.count()):
                    d = cb.itemData(i)
                    if isinstance(d, str) and d.lower() == path.lower():
                        found_idx = i
                        break

        if found_idx == -1:
            fn_lower = font_name.lower()
            for i in range(cb.count()):
                if cb.itemText(i).lower() == fn_lower:
                    found_idx = i
                    break

        if found_idx != -1:
            cb.setCurrentIndex(found_idx)

        cb.blockSignals(False)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_help_panel()
        if self.pages_QWidget:
            self._resize_timer.start(100)

    def _apply_resize(self):
        if not self.pages_QWidget:
            return

        vis_start, vis_end = self._get_visible_page_range()
        for i in range(vis_start, vis_end):
            self.page_manager.rerender_page(i)

        def rerender_rest():
            for i in range(len(self.pages_QWidget)):
                if i < vis_start or i >= vis_end:
                    self.page_manager.rerender_page(i)

        QTimer.singleShot(0, rerender_rest)

        if self.viewmodel.mode == EditorMode.EDIT_TEXT:
            for page_index, labels in list(self.text_tool.edit_labels.items()):
                self.text_tool._saved_text_data[page_index] = [
                    lbl.text_data for lbl in labels
                ]
                for lbl in labels:
                    if lbl.edit_text is not None:
                        try:
                            lbl.edit_text.deleteLater()
                        except RuntimeError:
                            pass
                        lbl.edit_text = None
                    lbl.deleteLater()
            self.text_tool.edit_labels.clear()

            def rebuild_text():
                for i in range(len(self.pages_QWidget)):
                    self.text_tool.prepare_edit_mode_i(i)

            QTimer.singleShot(50, rebuild_text)


        elif self.viewmodel.mode == EditorMode.EDIT_IMAGE:

            for page_index, widgets in list(self.image_tool.edit_images.items()):

                for w in widgets:

                    try:

                        w.deleteLater()

                    except RuntimeError:

                        pass

            self.image_tool.edit_images.clear()

            def rebuild_images():

                for i in range(len(self.pages_QWidget)):
                    self.image_tool.prepare_edit_mode_i(i)

            QTimer.singleShot(50, rebuild_images)

    def _do_undo(self):
        if self.viewmodel.mode == EditorMode.EDIT_TEXT:
            self.text_tool.clear_edit_labels()
        if self.viewmodel.mode == EditorMode.EDIT_IMAGE:
            self.image_tool.commit_edit_images()

        actual_page = self.viewmodel.undo()
        if actual_page >= 0:
            self.page_manager.rerender_page(actual_page)
            if self.viewmodel.mode == EditorMode.EDIT_TEXT:
                self.text_tool.prepare_edit_mode_i(actual_page)
            elif self.viewmodel.mode == EditorMode.EDIT_IMAGE:
                self.image_tool.prepare_edit_mode_i(actual_page)

    def _do_redo(self):
        if self.viewmodel.mode == EditorMode.EDIT_TEXT:
            self.text_tool.clear_edit_labels()
        if self.viewmodel.mode == EditorMode.EDIT_IMAGE:
            self.image_tool.commit_edit_images()

        actual_page = self.viewmodel.redo()
        if actual_page >= 0:
            self.page_manager.rerender_page(actual_page)
            if self.viewmodel.mode == EditorMode.EDIT_TEXT:
                self.text_tool.prepare_edit_mode_i(actual_page)
            elif self.viewmodel.mode == EditorMode.EDIT_IMAGE:
                self.image_tool.prepare_edit_mode_i(actual_page)

    def _on_history_changed(self):
        self.undo_action.setEnabled(self.viewmodel.can_undo())
        self.redo_action.setEnabled(self.viewmodel.can_redo())