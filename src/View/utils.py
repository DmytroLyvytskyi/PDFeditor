import os
import sys
import re
import pymupdf
from difflib import SequenceMatcher
_font_index = None

_STYLE_WORDS = [
    'bolditalic', 'boldobl', 'bold', 'italic', 'oblique',
    'regular', 'medium', 'light', 'thin', 'black', 'heavy',
    'semibold', 'demibold', 'condensed', 'narrow', 'roman', 'book',
    'psmt', 'mt', 'ps', 'std', 'pro', 'lt', 'ot',
]
_PYMUPDF_BUILTINS = {
    'helv', 'hebo', 'heit', 'hebi',
    'tiro', 'tibo', 'tiit', 'tibi',
    'cour', 'cobo', 'coit', 'cobi',
    'symb', 'zadb',
}


_ALIASES = {
    'msshelldlg2': 'arial',
    'msshelldlg':  'arial',
    'mssansserif': 'arial',
    'msserif':     'timesnewroman',
    'system':      'arial',
    'fixedsys':    'couriernew',
}

pymupdf_fonts = {
    'serif':             'tiro',
    'serif_bold':        'tibo',
    'serif_italic':      'tiit',
    'serif_bold_italic': 'tibi',
    'sans':              'helv',
    'mono':              'cour',
}

_CATEGORY_PREFERRED = {
    'sans': ['Arial', 'DejaVu Sans'],
    'serif': ['Times New Roman', 'DejaVu Serif'],
    'mono': ['Courier New', 'DejaVu Sans Mono'],
    'serif_bold': ['Times New Roman Bold'],
    'serif_italic': ['Times New Roman Italic'],
    'serif_bold_italic': ['Times New Roman Bold Italic'],
    'symbol': ['Segoe UI Symbol'],
}

def _clean(name):
    name = re.sub(r'^[A-Za-z]{6}\+', '', name)
    return re.sub(r'[-_\s]', '', name).lower()



def _parse_font_name(name):
    n = _clean(name)
    is_bold = bool(re.search(r'bold|heavy|black|semibold', n))
    is_italic = bool(re.search(r'italic|oblique', n))
    is_mono = bool(re.search(r'mono|courier|consol|typewriter|inconsolata', n))
    result = n
    changed = True
    while changed:
        changed = False
        for word in _STYLE_WORDS:
            if result.endswith(word) and len(result) > len(word):
                result = result[:-len(word)]
                changed = True
    family = result or n
    return family, is_bold, is_italic, is_mono


def _build_font_index():
    global _font_index
    if _font_index is not None:
        return _font_index

    if sys.platform == "win32":
        dirs = [r"C:\Windows\Fonts"]
    else:
        dirs = [
            "/usr/share/fonts",
            os.path.expanduser("~/.fonts"),
            os.path.expanduser("~/.local/share/fonts"),
        ]

    index = []
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for root, _, files in os.walk(d):
            for fname in files:
                if not fname.lower().endswith(('.ttf', '.otf')):
                    continue
                path = os.path.join(root, fname)
                try:
                    f = pymupdf.Font(fontfile=path)
                    family, _, _, _ = _parse_font_name(f.name)
                    index.append({
                        'path':      path,
                        'name':      f.name,
                        'family':    family,
                        'is_bold':   f.is_bold,
                        'is_italic': f.is_italic,
                        'is_mono':   f.is_monospaced,
                        'is_serif':  f.is_serif,
                    })
                except Exception:
                    continue

    _font_index = index

    return index

def find_system_font(name):
    index = _build_font_index()
    if not index:
        return None
    alias = _ALIASES.get(_clean(name))
    if alias:
        name = alias
    family, is_bold, is_italic, is_mono = _parse_font_name(name)
    candidates = [c for c in index if c['is_mono'] == is_mono] or index

    def _score(c):
        s = SequenceMatcher(None, family, c['family']).ratio() * 70
        s += 15 if is_bold == c['is_bold'] else -15
        s += 15 if is_italic == c['is_italic'] else -15
        return max(s, 0.0)

    best = max(candidates, key=_score)
    return best['path'] if _score(best) >= 25 else None


def find_system_font_by_category(category):
    for preferred in _CATEGORY_PREFERRED.get(category, []):
        path = find_system_font(preferred)
        if path:
            return path

    index = _build_font_index()
    is_bold = 'bold' in category
    is_italic = 'italic' in category
    is_mono = category == 'mono'

    for c in index:
        if c['is_mono'] != is_mono:
            continue
        if is_bold and not c['is_bold']:
            continue
        if is_italic and not c['is_italic']:
            continue
        return c['path']

    return None


def find_system_font_for_pdf_font(font_cache_entry):
    if not font_cache_entry:
        return None
    path = find_system_font(font_cache_entry['name'])
    if path:
        return path
    return find_system_font_by_category(font_cache_entry.get('category', 'serif'))


def get_system_font_families():
    index = _build_font_index()
    seen = {}
    for entry in index:
        if entry['is_bold'] or entry['is_italic']:
            continue
        fam = entry['family']
        if fam not in seen:
            seen[fam] = (entry['name'], entry['path'])
    return sorted([(name, path) for _, (name, path) in seen.items()], key=lambda x: x[0].lower())


def classify_font(f):
    name_low = (f.name or '').lower().replace('-', '').replace(' ', '')
    if any(s in name_low for s in ('symbol', 'wingdings', 'webdings', 'dingbat', 'marlett')):
        return 'symbol'
    if f.is_monospaced:
        return 'mono'
    if f.is_bold and f.is_italic:
        return 'serif_bold_italic'
    if f.is_bold:
        return 'serif_bold'
    if f.is_italic:
        return 'serif_italic'
    if f.is_serif:
        return 'serif'
    return 'sans'


def category_from_font_name(font_name):
    n = font_name.lower().replace('-', '').replace(' ', '')
    if any(x in n for x in ['mono', 'cour', 'typewriter', 'consol', 'inconsolata']):
        return 'mono'
    is_bold = any(x in n for x in ['bold', 'heavy', 'black', 'semibold'])
    is_italic = any(x in n for x in ['italic', 'oblique'])
    if is_bold and is_italic:
        return 'serif_bold_italic'
    if is_bold:
        return 'serif_bold'
    if is_italic:
        return 'serif_italic'
    if any(x in n for x in ['sans', 'helv', 'arial', 'gothic', 'grotesk']):
        return 'sans'
    return 'serif'

def get_font_category(font_name):
    try:
        if os.path.isfile(font_name):
            f = pymupdf.Font(fontfile=font_name)
        elif font_name in _PYMUPDF_BUILTINS:
            f = pymupdf.Font(fontname=font_name)
        else:
            return category_from_font_name(font_name)
        return classify_font(f)
    except Exception:
        print(Exception)
        return category_from_font_name(font_name)

def get_bundled_font(category):
    fonts = {
        'serif':             'lmroman10-regular.otf',
        'serif_bold':        'lmroman10-bold.otf',
        'serif_italic':      'lmroman10-italic.otf',
        'serif_bold_italic': 'lmroman10-bold.otf',
    }
    filename = fonts.get(category)
    if not filename:
        return None
    directory = os.path.join(os.path.dirname(__file__), '..', '..', 'fonts', 'bundled')
    path = os.path.join(directory, filename)
    return path if os.path.exists(path) else None




def resolve_font(font_cache, xref, text, font_name=None):
    data = font_cache.get(xref)
    chars = [ch for ch in text if ch.strip() and ch != '\x00']

    if data is None and font_name and font_name in _PYMUPDF_BUILTINS:
        return None, font_name

    if data is not None:
        category = data.get('category', 'serif')
    elif font_name:
        category = get_font_category(font_name)
    else:
        category = 'serif'
    if data is not None:
        font_obj = data.get('font_obj')
        tmp_path = data.get('tmp_path')
        if font_obj and tmp_path and os.path.isfile(tmp_path):
            if '_pdf_usable' not in data:
                data['_pdf_usable'] = font_obj.has_glyph(ord('a')) > 0
            if data['_pdf_usable']:
                if not chars or all(font_obj.has_glyph(ord(ch)) > 0 for ch in chars):
                    return tmp_path, f"Fp{xref}"
    if data is not None:
        if '_sys_path' not in data:
            sp = find_system_font_for_pdf_font(data)
            data['_sys_path'] = sp
            if sp:
                try:
                    data['_sys_font'] = pymupdf.Font(fontfile=sp)
                except Exception:
                    data['_sys_path'] = None
                    data['_sys_font'] = None
            else:
                data['_sys_font'] = None
        system_path = data['_sys_path']
        sys_font = data.get('_sys_font')
        if system_path and sys_font:
            if not chars or all(sys_font.has_glyph(ord(ch)) > 0 for ch in chars):
                return system_path, f"Fs{xref}"
    if data is None and font_name:
        if os.path.isfile(font_name):
            return font_name, "Fpath"
        system_path = find_system_font(font_name)
        if system_path:
            try:
                f = pymupdf.Font(fontfile=system_path)
                if not chars or all(f.has_glyph(ord(ch)) > 0 for ch in chars):
                    return system_path, "Fsn"
            except Exception:
                pass
    bundled_path = get_bundled_font(category)
    if bundled_path:
        try:
            f = pymupdf.Font(fontfile=bundled_path)
            if not chars or all(f.has_glyph(ord(ch)) > 0 for ch in chars):
                return bundled_path, f"Fb{xref}"
        except Exception:
            pass
    system_path = find_system_font_by_category(category)
    if system_path:
        return system_path, f"Fsc{xref}"
    fallback = pymupdf_fonts.get(category, 'tiro')
    return None, fallback


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
        f = pymupdf.Font(fontname=pymupdf_fonts.get(category, 'tiro'))
        return f.has_glyph(ord(char)) > 0
    except Exception:
        return False


def calculate_x_offset(label) -> float:
    return label.width() / 2 - label.pixmap().width() / 2

def calculate_y_offset(label) -> float:
    return max(0.0, label.height() / 2 - label.pixmap().height() / 2)


def get_scale(viewmodel, page_index, label):
    page_rect = viewmodel.Model.file[page_index].rect
    pixmap = label.pixmap()
    scale_x = pixmap.width() / page_rect.width
    scale_y = pixmap.height() / page_rect.height
    return scale_x, scale_y