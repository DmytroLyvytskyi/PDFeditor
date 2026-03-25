import atexit
import hashlib
import os
import shutil
import tempfile
import pymupdf
from PySide6.QtGui import QColor
from src.View.utils import classify_font, resolve_font

class PdfModel:
    def __init__(self):
        self.file = None
        self.total = None
        self.font_cache = {}
        self._page_spans_cache = {}
        self._image_originals = {}
        self._fontname_info = {}
        self._undo_stack = []
        self._redo_stack = []
        atexit.register(self.cleanup)

    def save_snapshot(self, page_index):
        try:
            tmp = pymupdf.open()
            tmp.insert_pdf(self.file, from_page=page_index, to_page=page_index)
            data = tmp.tobytes(garbage=4, deflate=True)
            tmp.close()
            self._undo_stack.append({'page': page_index, 'data': data})
            self._redo_stack.clear()
            if len(self._undo_stack) > 20:
                self._undo_stack.pop(0)
        except Exception:
            pass

    def open_file(self, path):
        if self.file is not None:
            self.file.close()
            self.file = None
            self.total = None
        self.cleanup()
        self.file = pymupdf.open(path)
        self._undo_stack.clear()
        self._redo_stack.clear()
        self.font_cache = {}
        self._page_spans_cache = {}
        self._fontname_info = {}
        self._extract_all_fonts()
        self.total = len(self.file)

    def _extract_all_fonts(self):
        os.makedirs("fonts", exist_ok=True)
        visited = set()
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
                    self.font_cache[xref] = {
                        'codepoints': set(), 'tmp_path': tmp_path,
                        'name': name, 'category': classify_font(f),
                        'font_obj': f
                    }
                except Exception:
                    continue

            page_font_xref_map = {}
            for font in self.file[page_index].get_fonts(full=True):
                xref = font[0]
                subset = font[3]
                base = subset.split('+')[-1] if '+' in subset else subset
                page_font_xref_map[base] = xref

            for block in self.file[page_index].get_text("dict")["blocks"]:
                if 'lines' not in block:
                    continue
                for line in block['lines']:
                    for span in line['spans']:
                        span_base = span['font'].split('+')[-1] if '+' in span['font'] else span['font']
                        xref = page_font_xref_map.get(span_base)
                        if xref is not None and xref in self.font_cache:
                            data = self.font_cache[xref]
                            for ch in span['text']:
                                data['codepoints'].add(ord(ch))

        name_to_xrefs = {}
        for xref, data in self.font_cache.items():
            name = data['name']
            if name not in name_to_xrefs:
                name_to_xrefs[name] = []
            name_to_xrefs[name].append(xref)

        for name, xrefs in name_to_xrefs.items():
            if len(xrefs) <= 1:
                continue
            all_codepoints = set()
            for x in xrefs:
                all_codepoints.update(self.font_cache[x]['codepoints'])
            for x in xrefs:
                self.font_cache[x]['codepoints'] = all_codepoints

    def _full_redraw(self, page, override_spans):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if 'lines' in block:
                page.add_redact_annot(block['bbox'])
        page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
        for x, y, text, font, fontsize, pdf_color, xref in override_spans:
            if text.strip():
                tmp_path, fontname = resolve_font(self.font_cache, xref, text, font_name=font)
                self._fontname_info[fontname] = (xref, font)
                if xref in self.font_cache:
                    real_name = self.font_cache[xref]['name']
                    existing = self._fontname_info.get(real_name)
                    if existing is None or existing[0] == 0:
                        self._fontname_info[real_name] = (xref, font)
                if tmp_path:
                    page.insert_text((x, y), text, fontsize=fontsize, fontfile=tmp_path, fontname=fontname, color=pdf_color)
                else:
                    page.insert_text((x, y), text, fontsize=fontsize, fontname=fontname, color=pdf_color)
        self._page_spans_cache.pop(page.number, None)

    def render_page(self, num, override_spans=None, zoom=1.0):
        page = self.file[num]
        if override_spans is not None:
            self._full_redraw(page, override_spans)
        matrix = pymupdf.Matrix(zoom, zoom)
        return page.get_pixmap(matrix=matrix)

    def save_file(self, path, override_spans_pages=None, override_images_pages=None):
        if override_spans_pages:
            for page_index, spans in override_spans_pages.items():
                self._full_redraw(self.file[page_index], spans)
        if override_images_pages:
            for page_index, images in override_images_pages.items():
                self.full_redraw_images(self.file[page_index], images)

        if os.path.abspath(path) == os.path.abspath(self.file.name):
            fd, tmp_path = tempfile.mkstemp(suffix='.pdf')
            os.close(fd)
            try:
                self.file.save(tmp_path, garbage=4, deflate=True, encryption=pymupdf.PDF_ENCRYPT_KEEP)
                self.file.close()
                shutil.move(tmp_path, path)
            except Exception:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                raise
            self.file = pymupdf.open(path)
            self._undo_stack.clear()
            self._redo_stack.clear()
            self._page_spans_cache.clear()
            self._fontname_info.clear()
            self.font_cache = {}
            self._extract_all_fonts()
        else:
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
        tmp_path, fontname = resolve_font(self.font_cache, xref, text, font_name=font)
        self._fontname_info[fontname] = (xref, font)
        if xref in self.font_cache:
            real_name = self.font_cache[xref]['name']
            existing = self._fontname_info.get(real_name)
            if existing is None or existing[0] == 0:
                self._fontname_info[real_name] = (xref, font)
        self.save_snapshot(page_index)
        if tmp_path:
            page.insert_text((x, y), text, fontsize=fontsize, fontfile=tmp_path, fontname=fontname, color=pdf_color)
        else:
            page.insert_text((x, y), text, fontsize=fontsize, fontname=fontname, color=pdf_color)
        self._page_spans_cache.pop(page_index, None)


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
            new_xref = font[0]
            subset = font[3]
            base = subset.split('+')[-1] if '+' in subset else subset
            if base in self._fontname_info:
                original_xref, original_font_name = self._fontname_info[base]
                font_xref_map[base] = original_xref
                font_xref_map[original_font_name] = original_xref
                if original_xref in self.font_cache:
                    font_xref_map[self.font_cache[original_xref]['name']] = original_xref
            elif base not in font_xref_map:
                font_xref_map[base] = new_xref
            else:
                existing_cp = len(self.font_cache.get(font_xref_map[base], {}).get('codepoints', set()))
                new_cp = len(self.font_cache.get(new_xref, {}).get('codepoints', set()))
                if new_cp > existing_cp:
                    font_xref_map[base] = new_xref

        blocks = self.get_text_blocks_i(page_index)
        result = []

        for block in blocks:
            if 'lines' not in block:
                continue
            for line in block['lines']:
                groups = []
                for span in line['spans']:
                    color_int = span['color']
                    r = (color_int >> 16) & 255
                    g = (color_int >> 8) & 255
                    b = color_int & 255
                    font_base = span['font'].split('+')[-1] if '+' in span['font'] else span['font']
                    xref = font_xref_map.get(font_base, 0)
                    key = (round(span['size'], 1), font_base, r, g, b, xref)
                    if groups and groups[-1][0] == key:
                        groups[-1][1].append(span)
                    else:
                        groups.append((key, [span]))
                for key, spans_list in groups:
                    size_val, font_base, r, g, b, xref = key
                    merged_text = ''.join(s['text'] for s in spans_list)
                    if not merged_text.strip():
                        continue
                    qcolor = QColor(r, g, b)
                    first = spans_list[0]
                    last = spans_list[-1]
                    merged_bbox = (
                        first['bbox'][0], first['bbox'][1],
                        last['bbox'][2], last['bbox'][3]
                    )
                    raw_font = first['font']
                    clean_font = raw_font.split('+')[-1] if '+' in raw_font else raw_font
                    if clean_font in self._fontname_info:
                        orig_xref, orig_font = self._fontname_info[clean_font]
                        if orig_xref in self.font_cache:
                            clean_font = self.font_cache[orig_xref]['name']
                        else:
                            clean_font = orig_font
                    result.append([
                        first['size'],
                        clean_font,
                        qcolor,
                        merged_text,
                        merged_bbox,
                        first['origin'],
                        xref
                    ])

        return result

    def insert_images(self, page, images):
        for img in images:
            self._insert_single_image(page, img)

    def get_images_i(self, page_index):
        page = self.file[page_index]
        result = []
        os.makedirs("fonts", exist_ok=True)
        os.makedirs("fonts/originals", exist_ok=True)
        for info in page.get_image_info(xrefs=True):
            bbox = info['bbox']
            xref = info.get('xref', 0)
            try:
                orig_bytes = None
                if xref and xref > 0:
                    img_data = self.file.extract_image(xref)
                    smask = img_data.get("smask", 0)
                    if smask and smask > 0:
                        base_pix = pymupdf.Pixmap(self.file, xref)
                        mask_pix = pymupdf.Pixmap(self.file, smask)
                        pix = pymupdf.Pixmap(base_pix, mask_pix)
                        orig_bytes = pix.tobytes("png")
                    else:
                        orig_bytes = img_data['image']
                    orig_key = f"fonts/originals/img_{xref}.png"
                else:
                    clip = pymupdf.Rect(bbox)
                    pix = page.get_pixmap(matrix=pymupdf.Matrix(1, 1), clip=clip, alpha=True)
                    orig_bytes = pix.tobytes("png")
                    h = hashlib.md5(orig_bytes).hexdigest()[:12]
                    orig_key = f"fonts/originals/img_inline_{h}.png"

                if orig_bytes and not os.path.exists(orig_key):
                    with open(orig_key, 'wb') as fp:
                        fp.write(orig_bytes)

                tmp_path = orig_key

                result.append({
                    'path': tmp_path,
                    'original_path': orig_key,
                    'x': bbox[0], 'y': bbox[1],
                    'w': bbox[2] - bbox[0], 'h': bbox[3] - bbox[1],
                })
            except Exception:
                continue
        return result

    def full_redraw_images(self, page, images, text_spans=None):
        self.save_snapshot(page.number)
        spans = text_spans if text_spans is not None else self.get_original_spans(page.number)
        for info in page.get_image_info():
            page.add_redact_annot(info['bbox'])
        for block in page.get_text("dict")["blocks"]:
            if 'lines' in block:
                page.add_redact_annot(block['bbox'])
        page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_REMOVE)
        self._full_redraw(page, spans)
        self._page_spans_cache[page.number] = spans
        self.insert_images(page, images)
        self._cleanup_rotated_temps()

    def _cleanup_rotated_temps(self):
        if not os.path.exists("fonts"):
            return
        for f in os.listdir("fonts"):
            if f.startswith("rotated_"):
                try:
                    os.remove(os.path.join("fonts", f))
                except Exception:
                    pass

    def insert_image_at(self, page_index, img_data):
        self.save_snapshot(page_index)
        self._insert_single_image(self.file[page_index], img_data)

    def get_original_spans(self, page_index):
        if page_index not in self._page_spans_cache:
            converted = []
            for size, font, qcolor, text, bbox, origin, xref in self.get_spans_i(page_index):
                x, y = origin
                pdf_color = (qcolor.red() / 255.0, qcolor.green() / 255.0, qcolor.blue() / 255.0)
                converted.append((x, y, text, font, size, pdf_color, xref))
            self._page_spans_cache[page_index] = converted
        return self._page_spans_cache[page_index]

    def cleanup(self):
        self._image_originals.clear()
        if not os.path.exists("fonts"):
            return
        for f in os.listdir("fonts"):
            path = os.path.join("fonts", f)
            if os.path.isfile(path):
                os.remove(path)

    def _get_rotated_image_path(self, img_path, rotation):
        if rotation % 360 == 0:
            return img_path
        try:
            from PIL import Image
            img = Image.open(img_path).convert("RGBA")
            rotated = img.rotate(-rotation, expand=True, resample=Image.BICUBIC)
            tmp_path = f"fonts/rotated_{int(rotation % 360)}_{os.path.basename(img_path)}.png"
            rotated.save(tmp_path)
            return tmp_path
        except Exception:
            return img_path

    def _insert_single_image(self, page, img):
        rect = pymupdf.Rect(img.x, img.y, img.x + img.width, img.y + img.height)
        path = self._get_rotated_image_path(img.original_path, img.rotation)
        page.insert_image(rect, filename=path, overlay=img.overlay, keep_proportion=False)

    def _apply_history_entry(self, entry, target_stack):
        pi = entry['page']
        tmp = pymupdf.open()
        tmp.insert_pdf(self.file, from_page=pi, to_page=pi)
        target_stack.append({'page': pi, 'data': tmp.tobytes(garbage=4, deflate=True)})
        tmp.close()
        restored = pymupdf.open("pdf", entry['data'])
        self.file.delete_page(pi)
        self.file.insert_pdf(restored, from_page=0, to_page=0, start_at=pi)
        restored.close()
        self._page_spans_cache.pop(pi, None)
        self._fontname_info.clear()
        return pi

    def undo(self):
        if not self.file or not self._undo_stack:
            return -1
        return self._apply_history_entry(self._undo_stack.pop(), self._redo_stack)

    def redo(self):
        if not self.file or not self._redo_stack:
            return -1
        return self._apply_history_entry(self._redo_stack.pop(), self._undo_stack)

    def can_undo(self):
        return bool(self.file and self._undo_stack)

    def can_redo(self):
        return bool(self.file and self._redo_stack)
    
    def close_file(self):
        self.file.close() if self.file else None
        self.file = None
        self.total = None
        self.font_cache = {}
        self._page_spans_cache = {}
        self._undo_stack.clear() 
        self._redo_stack.clear()

