# OCRHelper API

## 类定义

### OCRHelper
```python
class OCRHelper:
    def __init__(self, lang='ch'):
        """初始化PaddleOCR
        
        Args:
            lang: 识别语言,'ch'(中文),'en'(英文)等
        """
```

## 主要方法

### extract_text
```python
def extract_text(self, image_path: str, keywords: List[str] = None) -> List[Dict[str, Any]]:
    """识别图片中的文字
    
    Args:
        image_path: 图片路径
        keywords: 需要匹配的关键词列表
            
    Returns:
        List[Dict[str, Any]]: 包含识别结果的列表,每项包含:
            - box: 文字框坐标
            - text: 识别的文字
            - confidence: 置信度
    """
```

## 返回值格式

### OCR结果示例
```python
[
    {
        'box': [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],  # 文字框四个角的坐标
        'text': "识别的文字",
        'confidence': 0.95  # 置信度
    }
]
```

## 性能优化

- 使用PaddleOCR的高性能模型
- 支持关键词过滤减少计算量
- 图像预处理优化识别效果
- 多进程支持提升性能
  - cls_batch_num=1
  - rec_batch_num=1
  - det_db_score_mode='fast'
  - use_mp=True
  - total_process_num=2

## 使用示例

```python
# 初始化
ocr_helper = OCRHelper(lang='ch')

# 识别文字
results = ocr_helper.extract_text(
    image_path="screenshot.png",
    keywords=["目标文字"]
)

# 处理结果
for result in results:
    text = result['text']
    confidence = result['confidence']
    box = result['box']
    print(f"识别文字: {text}, 置信度: {confidence}")
```
