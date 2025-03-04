from typing import List, Tuple, Dict, Any
from paddleocr import PaddleOCR
from loguru import logger
from lib.text_matcher import TextMatcher

class OCRHelper:
    def __init__(self, lang='ch'):
        """
        初始化PaddleOCR

        Args:
            lang: 识别语言,'ch'(中文),'en'(英文)等
        """
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang=lang,
            show_log=False,  # 关闭PaddleOCR的调试日志
            cls_batch_num=1,  # 减小批处理大小
            rec_batch_num=1,
            det_db_score_mode='fast',  # 使用快速模式
            use_mp=True,  # 启用多进程
            total_process_num=2  # 使用2个进程
        )
        self.logger = logger

    def extract_text(self, image_path: str, keywords: List[str] = None,
                    region: List[int] = None) -> List[Dict[str, Any]]:
        """
        识别图片中的文字

        Args:
            image_path: 图片路径
            keywords: 需要匹配的关键词列表
            region: 识别区域 [x1, y1, x2, y2]

        Returns:
            包含识别结果的列表,每项包含:
            - box: 文字框坐标
            - text: 识别的文字
            - confidence: 置信度
        """
        try:
            # 执行OCR识别
            result = self.ocr.ocr(image_path, cls=True)

            if not result or not result[0]:
                return []

            # 处理识别结果
            ocr_results = []
            for line in result[0]:
                box = line[0]
                text = line[1][0]
                confidence = line[1][1]

                # 如果指定了region,检查是否在区域内
                if region:
                    x1, y1, x2, y2 = region
                    box_x1, box_y1 = box[0]
                    if not (x1 <= box_x1 <= x2 and y1 <= box_y1 <= y2):
                        continue

                # 如果指定了keywords,检查是否包含关键词
                if keywords:
                    if not any(k in text for k in keywords):
                        continue

                ocr_results.append({
                    'box': box,
                    'text': text,
                    'confidence': confidence
                })

            return ocr_results

        except Exception as e:
            self.logger.error(f"OCR识别失败: {str(e)}")
            return []



    def find(self, image_path: str, text: str = None, textContains: str = None, textMatch: str = None,
                    region: List[int] = None) -> List[Dict[str, Any]]:
        """
        识别图片中的文字

        Args:
            image_path: 图片路径
            keywords: 需要匹配的关键词列表
            region: 识别区域 [x1, y1, x2, y2]

        Returns:
            包含识别结果的列表,每项包含:
            - box: 文字框坐标
            - text: 识别的文字
            - confidence: 置信度
        """
        try:
            # 执行OCR识别
            result = self.ocr.ocr(image_path, cls=True)

            if not result or not result[0]:
                return []

            # 处理识别结果
            ocr_results = []
            for line in result[0]:
                box = line[0]
                text = line[1][0]
                confidence = line[1][1]

                # 如果指定了region,检查是否在区域内
                if region:
                    x1, y1, x2, y2 = region
                    box_x1, box_y1 = box[0]
                    if not (x1 <= box_x1 <= x2 and y1 <= box_y1 <= y2):
                        continue

                # 如果指定了keywords,检查是否包含关键词
                if not TextMatcher(text).match(text=text, textContains=textContains, textMatches=textMatches):
                    continue

                ocr_results.append({
                    'box': box,
                    'text': text,
                    'confidence': confidence
                })

            return ocr_results

        except Exception as e:
            self.logger.error(f"OCR识别失败: {str(e)}")
            return []