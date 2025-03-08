from rapidocr_onnxruntime import RapidOCR
from lib.text_matcher import TextMatcher

class Ocr:
    def __init__(self, image_path):
        self.image_path = image_path

    @property
    def ocr(self):
        return RapidOCR()

    def text_rect_and_text(self, **kwargs):
        result, elapse = self.ocr(self.image_path)
        for el in result:
          rect, rect_text, score = el
          if TextMatcher(rect_text).match(**kwargs):
            return rect, rect_text
        return None

    def info(self, **args):
        result = self.text_rect_and_text(**args)
        if result is None:
            return None
        rect, text = result
        height = rect[2][1] - rect[0][1]
        width = rect[2][0] - rect[0][0]
        point1, point2, point3, point4 = rect
        x, y = ((point1[0] + point2[0]) / 2, (point1[1] + point4[1]) / 2)
        return {
            'height': height,
            'width': width,
            'rect': rect,
            'text': text,
            'x': x,
            'y': y,
        }

    def text_rect(self, **kwargs):
        result = self.text_rect_and_text(**kwargs)
        if result is None:
            return None
        return result[0]

    def text(self, **kwargs):
        result = self.text_rect_and_text(**kwargs)
        if result is None:
            return None
        return result[1]

    def text_exists(self, **kwargs):
        return self.text(**kwargs) is not None

    def result(self):
        return self.ocr(self.image_path)

    def text_position(self, position = 'center', **kwargs):
        r = self.info(**kwargs)
        if r is None:
            return None
        return r['x'], r['y']

if __name__ == "__main__":
    image_path = "screenshots/test.png"
    ocr = Ocr(image_path)
    result, elapse = ocr.result()
    print(result)
    print(ocr.text_rect("首页"))
    print(ocr.text_position("首页"))

    from PIL import Image
    image = Image.open(image_path)
    ocr = Ocr(image)
    print(ocr.result())
