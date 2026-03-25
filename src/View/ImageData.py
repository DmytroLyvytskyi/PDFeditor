class ImageData:
    def __init__(self, path, x, y, width, height, overlay=True, rotation=0, original_path=None):
        self.path = path
        self.original_path = original_path if original_path is not None else path
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.overlay = overlay
        self.rotation = rotation