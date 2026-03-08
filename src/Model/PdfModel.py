import os

import pymupdf
from PySide6.QtGui import QColor

from src.View.utils import classify_font, resolve_font


class PdfModel:
    def __init__(self):
        self.file = None
        self.total = None
        self.font_cache = {}

    def open_file(self, path):
        if self.file != None:
            self.file.close()
            self.file = None
            self.total = None
        self.file = pymupdf.open(path)
        self.font_cache = {}
        self._extract_all_fonts()
        self.total = len(self.file)

    def _extract_all_fonts(self):
        os.makedirs("fonts", exist_ok=True)
        visited = set()
        name_to_xref = {}
        for page_index in range(len(self.file)):
            for font in self.file[page_index].get_fonts(full=True):
                xref = font[0]
                if xref in visited:
                    continue
                visited.add(xref)
                try:
                    font_bytes = self.file.extract_font(xref)[3]
                    if not font_bytes:
                        continue
                    subset = font[3]
                    name = subset.split('+')[-1] if '+' in subset else subset
                    tmp_path = f"fonts/pdf_font_{xref}.bin"
                    with open(tmp_path, 'wb') as fp:
                        fp.write(font_bytes)
                    f = pymupdf.Font(fontbuffer=font_bytes)
                    self.font_cache[xref] = {'codepoints': set(),'tmp_path': tmp_path,'name': name,'category': classify_font(f)}
                    name_to_xref[name] = xref
                except Exception:
                    continue
            for block in self.file[page_index].get_text("dict")["blocks"]:
                if 'lines' not in block:
                    continue
                for line in block['lines']:
                    for span in line['spans']:
                        span_base = span['font'].split('+')[-1] if '+' in span['font'] else span['font']
                        xref = name_to_xref.get(span_base)
                        if xref is not None:
                            data = self.font_cache[xref]
                            for ch in span['text']:
                                data['codepoints'].add(ord(ch))

    def _full_redraw(self, page, override_spans):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if 'lines' in block:
                page.add_redact_annot(block['bbox'])
        page.apply_redactions()

        for x, y, text, font, fontsize, pdf_color, xref in override_spans:
            if text.strip():
                tmp_path, fontname = resolve_font(self.font_cache, xref, text)
                if tmp_path:
                    page.insert_text((x, y), text,fontsize=fontsize,fontfile=tmp_path,fontname=fontname,color=pdf_color)
                else:
                    page.insert_text((x, y), text,fontsize=fontsize,fontname=fontname,color=pdf_color)

    def render_page(self, num, override_spans=None):
        page = self.file[num]
        if override_spans is not None:
            self._full_redraw(page, override_spans)
        return page.get_pixmap()

    def save_file(self, path, override_spans_pages=None, override_images_pages=None):
        if override_spans_pages:
            for page_index, spans in override_spans_pages.items():
                self._full_redraw(self.file[page_index], spans)
        if override_images_pages:
            for page_index, images in override_images_pages.items():
                self.insert_images(self.file[page_index], images)
        try:
            self.file.save(path, incremental=True, encryption=pymupdf.PDF_ENCRYPT_KEEP)
        except Exception:
            self.file.save(path, garbage=4, deflate=True, encryption=pymupdf.PDF_ENCRYPT_KEEP)

    def add_text(self, text, x, y, page_index, font, fontsize, color:QColor, xref):
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
        pdf_color = (color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0)
        tmp_path, fontname = resolve_font(self.font_cache, xref, text)
        if tmp_path:
            page.insert_text((x, y), text, fontsize=fontsize, fontfile=tmp_path, fontname=fontname, color=pdf_color)
        else:
            page.insert_text((x, y), text, fontsize=fontsize, fontname=fontname, color=pdf_color)


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
        font_xref_map = {}
        for font in self.file[page_index].get_fonts(full=True):
            xref = font[0]
            subset = font[3]
            if '+' in subset:
                base = subset.split('+')[-1]
            else:
                base = subset
            font_xref_map[base] = xref
        blocks = self.get_text_blocks_i(page_index)
        result = []
        for block in blocks:
            if 'lines' not in block:
                continue
            for line in block['lines']:
                spans = line['spans']
                if not spans:
                    continue
                merged_text = ''.join(s['text'] for s in spans)
                if not merged_text.strip():
                    continue
                first = spans[0]
                last = spans[-1]
                color_int = first['color']
                r = (color_int >> 16) & 255
                g = (color_int >> 8) & 255
                b = color_int & 255
                qcolor = QColor(r, g, b)
                merged_bbox = (first['bbox'][0],first['bbox'][1],last['bbox'][2],last['bbox'][3],)
                xref = font_xref_map.get(first['font'], 0)
                result.append([first['size'], first['font'], qcolor, merged_text, merged_bbox, first['origin'], xref])
        return result

    def insert_images(self, page, images):
        for img in images:
            rect = pymupdf.Rect(img.x, img.y, img.x + img.width, img.y + img.height)
            page.insert_image(rect, filename=img.path, overlay=img.overlay)

