# OCRHelper API

## 类定义
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
def extract_text(self, image_path: str, keywords: List[str] = None, 
                region: List[int] = None) -> List[Dict[str, Any]]:
    """识别图片中的文字
    
    Args:
        image_path: 图片路径
        keywords: 需要匹配的关键词列表
        region: 识别区域 [x1, y1, x2, y2]
            
    Returns:
        List[Dict[str, Any]]: 包含识别结果的列表,每项包含:
            - box: 文字框坐标
            - text: 识别的文字
            - confidence: 置信度
    """
```

## OCR结果格式

### 返回值示例
```python
[
    {
        'box': [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],  # 文字框四个角的坐标
        'text': "识别的文字",
        'confidence': 0.95  # 置信度
    },
    # ...
]
```

## 优化特性

### 文字过滤
- 支持关键词列表过滤
- 区域限制过滤
- 置信度过滤（内部）

### 性能优化
- 使用PaddleOCR的高性能模型
- 支持区域识别减少计算量
- 图像预处理优化识别效果

## 使用示例

```python
# 初始化
ocr_helper = OCRHelper(lang='ch')

# 全图识别
results = ocr_helper.extract_text(
    image_path="screenshot.png"
)

# 带关键词的区域识别
results = ocr_helper.extract_text(
    image_path="screenshot.png",
    keywords=["目标文字"],
    region=[100, 200, 500, 800]
)

# 处理识别结果
for result in results:
    text = result['text']
    confidence = result['confidence']
    box = result['box']
    print(f"识别文字: {text}, 置信度: {confidence}")
```
