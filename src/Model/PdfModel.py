import pymupdf
class PdfModel:
    def __init__(self):
        self.file = None
        self.total = None

    def open_file(self, path):
        self.file = pymupdf.open(path)
        self.total = len(self.file)


    def get_page(self, num):
        return self.file[num]


