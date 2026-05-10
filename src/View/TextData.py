from PySide6.QtGui import QFont, QColor


class TextData:
    def __init__(self, text, font, size, color, origin, xref, rotation=0):
        self.text = text
        self.font = font
        self.size = size
        self.color = color
        self.origin = origin
        self.xref = xref
        self.rotation = rotation