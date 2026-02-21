import pymupdf
from PySide6.QtGui import QColor


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


    def add_text(self, text, x, y, page_index, font, fontsize, color:QColor):
        """
        Adds text to a new position

        Args:
            text: text to add
            x (int): x position
            y (int): y position
            page_index (int): index of page
            font (str): font name (PyMuPDF)
            fontsize (int): font size
            color (QColor): color (PySide6)

        Returns:
            None
        """
        page = self.file[page_index]
        if fontsize<17:
            y = y - fontsize / 2
        pdf_color = (color.red() / 255.0,color.green() / 255.0,color.blue() / 255.0)
        page.insert_text((x,y), text, fontsize = fontsize, fontname = font, color = pdf_color)


    def get_text_blocks_i(self,page_index):
        """
        Get text blocks from a PDF page.

        Args:
            page_index (int): index of page

        Returns:
            list: A list of text block dictionaries, each having the structure:

            {
                "type": int,
                "bbox": (float, float, float, float),  # bounding box
                "lines": [
                    {
                        "wmode": int,
                        "dir": (float, float),
                        "bbox": (float, float, float, float),
                        "spans": [
                            {
                                "size": float,
                                "flags": int,
                                "font": str,
                                "color": int,
                                "origin": (float, float),
                                "text": str,
                                "bbox": (float, float, float, float)
                            }
                        ]
                    }
                ]
            }
        """
        page = self.file[page_index]
        blocks = page.get_text("dict")["blocks"]
        return blocks

    def get_spans_i(self, page_index):
        """
        Get text data from PDF

        Args:
            page_index (int): index of page

        Returns:
            list: A list of elements:
            [
                font_size (float),
                font_name (PyMuPDF),
                color (QColor),
                text (str),
                bbox (tuple)
            ]
        """
        blocks = self.get_text_blocks_i(page_index)
        result = []
        for block in blocks:
            for i in block['lines']:
                for j in i['spans']:
                    color_int = j['color']
                    r = (color_int >> 16) & 255
                    g = (color_int >> 8) & 255
                    b = color_int & 255
                    qcolor = QColor(r, g, b)
                    result.append([j['size'], j['font'], qcolor, j['text'], j['bbox']])
        return result

    def move_text(self,x,y,text_data,bbox,page_index):
        """
        Moves text in PDF

        Args:
            x (int): x position
            y (int): y position
            text_data (TextData): text data
            bbox (tuple): bbox
            page_index (int): index of page

        Returns:
            None
        """
        page = self.file[page_index]
        page.add_redact_annot(bbox)
        page.apply_redactions()
        self.add_text(text_data.text, x, y, page_index, text_data.font, text_data.size, text_data.color)


