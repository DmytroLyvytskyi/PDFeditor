# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'untitled.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMenuBar, QPushButton, QScrollArea,
    QSizePolicy, QSpacerItem, QStatusBar, QToolBar,
    QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(997, 808)
        self.actionView = QAction(MainWindow)
        self.actionView.setObjectName(u"actionView")
        self.actionView.setCheckable(True)
        self.actionView.setMenuRole(QAction.MenuRole.NoRole)
        self.actionAdd_Text = QAction(MainWindow)
        self.actionAdd_Text.setObjectName(u"actionAdd_Text")
        self.actionAdd_Text.setCheckable(True)
        self.actionAdd_Text.setMenuRole(QAction.MenuRole.NoRole)
        self.actionEdit_Text = QAction(MainWindow)
        self.actionEdit_Text.setObjectName(u"actionEdit_Text")
        self.actionEdit_Text.setCheckable(True)
        self.actionEdit_Text.setMenuRole(QAction.MenuRole.NoRole)
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName(u"actionOpen")
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName(u"actionSave")
        self.actionSaveAs = QAction(MainWindow)
        self.actionSaveAs.setObjectName(u"actionSaveAs")
        self.actionAdd_Image = QAction(MainWindow)
        self.actionAdd_Image.setObjectName(u"actionAdd_Image")
        self.actionAdd_Image.setMenuRole(QAction.MenuRole.NoRole)
        self.actionEdit_Image = QAction(MainWindow)
        self.actionEdit_Image.setObjectName(u"actionEdit_Image")
        self.actionEdit_Image.setCheckable(True)
        self.actionEdit_Image.setMenuRole(QAction.MenuRole.NoRole)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.prev_btn = QPushButton(self.centralwidget)
        self.prev_btn.setObjectName(u"prev_btn")

        self.horizontalLayout.addWidget(self.prev_btn)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.page_selector = QLineEdit(self.centralwidget)
        self.page_selector.setObjectName(u"page_selector")
        self.page_selector.setMaximumSize(QSize(30, 16777215))

        self.horizontalLayout.addWidget(self.page_selector)

        self.total = QLabel(self.centralwidget)
        self.total.setObjectName(u"total")

        self.horizontalLayout.addWidget(self.total)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.next_btn = QPushButton(self.centralwidget)
        self.next_btn.setObjectName(u"next_btn")

        self.horizontalLayout.addWidget(self.next_btn)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.scrollArea = QScrollArea(self.centralwidget)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scrollAreaWidgetContents_5 = QWidget()
        self.scrollAreaWidgetContents_5.setObjectName(u"scrollAreaWidgetContents_5")
        self.scrollAreaWidgetContents_5.setGeometry(QRect(0, 0, 975, 660))
        self.page_scroll = QVBoxLayout(self.scrollAreaWidgetContents_5)
        self.page_scroll.setObjectName(u"page_scroll")
        self.scrollArea.setWidget(self.scrollAreaWidgetContents_5)

        self.verticalLayout.addWidget(self.scrollArea)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 997, 33))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QToolBar(MainWindow)
        self.toolBar.setObjectName(u"toolBar")
        MainWindow.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolBar)
        self.toolBar_2 = QToolBar(MainWindow)
        self.toolBar_2.setObjectName(u"toolBar_2")
        MainWindow.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolBar_2)
        MainWindow.insertToolBarBreak(self.toolBar_2)

        self.toolBar.addAction(self.actionView)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionAdd_Text)
        self.toolBar.addAction(self.actionEdit_Text)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionAdd_Image)
        self.toolBar.addAction(self.actionEdit_Image)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actionView.setText(QCoreApplication.translate("MainWindow", u"View", None))
        self.actionAdd_Text.setText(QCoreApplication.translate("MainWindow", u"Add Text", None))
        self.actionEdit_Text.setText(QCoreApplication.translate("MainWindow", u"Edit Text", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", u"Open PDF", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.actionSaveAs.setText(QCoreApplication.translate("MainWindow", u"Save As...", None))
        self.actionAdd_Image.setText(QCoreApplication.translate("MainWindow", u"Add Image", None))
        self.actionEdit_Image.setText(QCoreApplication.translate("MainWindow", u"Edit Image", None))
        self.prev_btn.setText(QCoreApplication.translate("MainWindow", u"<-", None))
        self.total.setText(QCoreApplication.translate("MainWindow", u"/", None))
        self.next_btn.setText(QCoreApplication.translate("MainWindow", u"->", None))
        self.toolBar.setWindowTitle(QCoreApplication.translate("MainWindow", u"toolBar", None))
        self.toolBar_2.setWindowTitle(QCoreApplication.translate("MainWindow", u"toolBar_2", None))
    # retranslateUi

