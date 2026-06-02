from PIL import ImageOps, ImageFilter


def preprocess_frame(frame):
    """Convert the captured ROI into a high-contrast grayscale image for OCR."""
    if frame is None:
        return None

    processed = frame.convert('L')
    processed = ImageOps.autocontrast(processed)
    processed = processed.resize((processed.width * 2, processed.height * 2))
    processed = processed.filter(ImageFilter.SHARPEN)
    processed = processed.point(lambda pixel: 255 if pixel > 160 else 0)
    return processed
