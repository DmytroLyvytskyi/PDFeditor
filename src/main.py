from PySide6 import QtWidgets
import sys

from src.Model.PdfModel import PdfModel
from src.View.PdfView import PdfView
from src.ViewModel.PdfViewModel import PdfViewModel

if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    model = PdfModel()
    viewmodel = PdfViewModel(model)
    window = PdfView(viewmodel)
    window.showMaximized()
    sys.exit(app.exec())

