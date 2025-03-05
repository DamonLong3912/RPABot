import os
import cv2
from paddleocr import PaddleOCR

class OCR:
    def __init__(self, image_path):
        self.image_path = image_path
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        self.ocr_model = PaddleOCR(use_angle_cls=True, lang='ch')

    def ocr(self):
        return self.ocr_model.ocr(self.image_path, cls=True)

    def text_rect(self, text):
        result = self.ocr()
        for res in result:
            for r in res:
                rect = r[0]
                text_with_score = r[1]
                if text in text_with_score[0]:
                    return rect
        return None

    # 根据位置，返回top, center, bottom, left, right的位置
    # [[27.0, 15.0], [233.0, 15.0], [233.0, 88.0], [27.0, 88.0]]
    def position(self, rect, name):
        # 返回方形区域的上方中心点
        center = (rect[0][0] + rect[2][0]) / 2, (rect[0][1] + rect[2][1]) / 2
        # 上方中心点到中心点一半的距离
        top = center[0], center[1] - (center[1] - rect[1][1]) / 2
        left = center[0] - (center[0] - rect[0][0]) / 2, center[1]
        right = center[0] + (rect[2][0] - center[0]) / 2, center[1]
        bottom = center[0], center[1] + (rect[3][1] - center[1]) / 2
        if name == 'top':
            return top
        elif name == 'left':
            return left
        elif name == 'right':
            return right
        elif name == 'bottom':
            return bottom
        else:
            return None


    def text_list(self):
        result = self.ocr()
        text = []
        for res in result:
            for r in res:
                text.append(r[1][0])
        return text

    def text(self):
        text_list = self.text_list()
        return "".join(text_list)


if __name__ == "__main__":
    ocr = OCR("test/images/ocr.png")
    print(ocr.ocr())
    print(ocr.text_rect('电影'))
    print(ocr.position(ocr.text_rect('电影'), 'top'))
