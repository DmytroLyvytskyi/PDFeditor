class ImageData:
    def __init__(self, path, x, y, width, height, overlay=True):
        self.path = path
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.overlay = overlay