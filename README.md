# EditorPDF

A free, open-source desktop PDF editor built with PyMuPDF, and PySide6.

> Developed as a bachelor's thesis at Comenius University in Bratislava (FMFI UK), 2026.

---

## Features

**Text**
- Edit existing text blocks directly in the original PDF font
- Change text content, font, size, and color
- Add new text
- Move text blocks by dragging
- Automatic font detection - uses the font embedded in the PDF, falls back to a matching system font, then to a bundled fallback

**Images**
- Add new images
- Move, resize, and rotate existing images
- Place images in front of or behind text
- Delete images

**Document**
- Zoom from 25% to 400% (`Ctrl+Scroll`, `Ctrl+ +/-`, `Ctrl+0` to reset)
- Undo / Redo
- Delete pages
- Merge multiple PDF files into one

---

## Installation

### Windows

Download the installer from the [Releases](../../releases) page and run `EditorPDF-Setup.exe`.

The installer registers `.pdf` files to open with EditorPDF and creates optional Start Menu / desktop shortcuts.

### Linux

Download the AppImage from the [Releases](../../releases) page:

```bash
chmod +x EditorPDF.AppImage
./EditorPDF.AppImage
```

### From source

**Requirements:** Python 3.10+

```bash
git clone https://github.com/DmytroLyvytskyi/PDFeditor.git
cd PDFeditor
pip install -r requirements.txt
python -m src.main
```

---

## Keyboard shortcuts

| Action | Shortcut |
|---|---|
| Zoom in / out | `Ctrl++` / `Ctrl+-` |
| Reset zoom | `Ctrl+0` |
| Zoom with scroll | `Ctrl+Scroll` |
| Undo | `Ctrl+Z` |
| Redo | `Ctrl+Y` |
| Save text block (Add Text mode) | `Enter` or click on PDF |
| Edit text block (Edit Text mode) | Double-click block → `Enter` |
| Delete selected block | `Del` or `Backspace` |

---

## Known limitations

- **Mathematical symbols** - some characters (e.g. large brackets in formulas) may not render correctly after editing. This is partly a known limitation of PyMuPDF with certain font subsets.
- **Hyperlinks** - links may sometimes disappear.
- **Word-exported PDFs** - PDFs exported from the online version of Word may work incorrectly; use the desktop version of Word.


---

## License

GNU Affero General Public License v3.0 — see [LICENSE](LICENSE) for details.

