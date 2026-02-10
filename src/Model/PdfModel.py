import pymupdf
class PdfModel:
    def __init__(self):
        self.file = None
        self.total = None

    def open_file(self, path):
        self.file = pymupdf.open(path)
        self.total = len(self.file)

    def render_page(self, num):
        page = self.file[num]
        return page.get_pixmap()

    def save_file(self, path):
        self.file.save(path)


    def add_text(self, text, x, y, page_index):
        page = self.file[page_index]
        page.insert_text((x,y), text)


