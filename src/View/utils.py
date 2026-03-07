import os
import sys

import pymupdf


def calculate_x_offset(label):
    return label.width() / 2 - label.pixmap().width() / 2


pymupdf_fonts = {
    "serif":             "tiro",
    "serif_bold":        "tibo",
    "serif_italic":      "tiit",
    "serif_bold_italic": "tibi",
    "sans":              "helv",
    "mono":              "cour",
}


def classify_font(f):
    if f.is_monospaced:
        return "mono"
    if f.is_bold and f.is_italic:
        return "serif_bold_italic"
    if f.is_bold:
        return "serif_bold"
    if f.is_italic:
        return "serif_italic"
    if f.is_serif:
        return "serif"
    return "sans"


def find_system_font(name):
    name_lower = name.lower().replace(" ", "")
    if sys.platform == "win32":
        dirs = [r"C:\Windows\Fonts"]
    else:  # Linux
        dirs = [
            "/usr/share/fonts",
            os.path.expanduser("~/.fonts"),
            os.path.expanduser("~/.local/share/fonts")
        ]
    for d in dirs:
        if not os.path.exists(d):
            continue
        for root, _, files in os.walk(d):
            for fname in files:
                if fname.lower().endswith(('.ttf', '.otf')):
                    if name_lower in fname.lower().replace(" ", ""):
                        return os.path.join(root, fname)
    return None


def get_bundled_font(category):
    fonts = {
        "serif": "lmroman10-regular.otf",
        "serif_bold": "lmroman10-bold.otf",
        "serif_italic": "lmroman10-italic.otf",
        "serif_bold_italic": "lmroman10-bold.otf",
    }
    filename = fonts.get(category)
    if filename is None:
        return None
    dir = os.path.join(os.path.dirname(__file__), "..", "..", "fonts", "bundled")
    path = os.path.join(dir, filename)
    return path if os.path.exists(path) else None

def resolve_font(font_cache, xref, text):
    data = font_cache.get(xref)
    if data is not None:
        chars = [ch for ch in text if ch.strip()]
        if chars and all(ord(ch) in data['codepoints'] for ch in chars):
            return data['tmp_path'], f"F{xref}"
    if data is not None:
        system_path = find_system_font(data['name'])
        if system_path:
            return system_path, f"Fs{xref}"
    category = data.get('category', 'serif') if data else 'serif'
    bundled_path = get_bundled_font(category)
    if bundled_path:
        return bundled_path, f"Fb{xref}"
    return None, pymupdf_fonts.get(category, "tiro")


def has_char_in_fallback(font_cache, xref, char):
    data = font_cache.get(xref)
    category = data.get('category', 'serif') if data else 'serif'
    bundled_path = get_bundled_font(category)
    if bundled_path:
        try:
            f = pymupdf.Font(fontfile=bundled_path)
            return f.has_glyph(ord(char)) > 0
        except Exception:
            pass
    try:
        f = pymupdf.Font(fontname=pymupdf_fonts.get(category, "tiro"))
        return f.has_glyph(ord(char)) > 0
    except Exception:
        pass
    return False