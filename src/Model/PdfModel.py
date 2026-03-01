import pymupdf
from PySide6.QtGui import QColor


class PdfModel:
    def __init__(self):
        self.file = None
        self.total = None

    def open_file(self, path):
        if self.file != None:
            self.file.close()
            self.file = None
            self.total = None
        self.file = pymupdf.open(path)
        self.total = len(self.file)

    def _full_redraw(self, page, override_spans):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if 'lines' in block:
                page.add_redact_annot(block['bbox'])
        page.apply_redactions()

        for x, y, text, font, fontsize, pdf_color in override_spans:
            if text.strip():
                page.insert_text((x, y), text, fontsize=fontsize, fontname=font, color=pdf_color)

    def render_page(self, num, override_spans=None):
        page = self.file[num]
        if override_spans is not None:
            self._full_redraw(page, override_spans)
        return page.get_pixmap()

    def save_file(self, path, override_spans_pages=None):
        if override_spans_pages:
            for page_index, spans in override_spans_pages.items():
                self._full_redraw(self.file[page_index], spans)
        try:
            self.file.save(path, incremental=True, encryption=pymupdf.PDF_ENCRYPT_KEEP)
        except Exception:
            self.file.save(path, garbage=4, deflate=True, encryption=pymupdf.PDF_ENCRYPT_KEEP)

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
            if 'lines' not in block:
                continue
            for i in block['lines']:
                for j in i['spans']:
                    color_int = j['color']
                    r = (color_int >> 16) & 255
                    g = (color_int >> 8) & 255
                    b = color_int & 255
                    qcolor = QColor(r, g, b)
                    result.append([j['size'], j['font'], qcolor, j['text'], j['bbox'], j['origin']])
        return result


