# OCRHelper API

## 类定义

### OCRHelper
```python
class OCRHelper:
    def __init__(self, lang='ch', use_gpu=False):
        """初始化PaddleOCR
        
        Args:
            lang: 识别语言,'ch'(中文),'en'(英文)等
            use_gpu: 是否使用GPU加速
        """
```

## 主要方法

### extract_text
```python
def extract_text(self, 
                image: Union[str, Image.Image], 
                keywords: List[str] = None,
                region: List[int] = None) -> List[Dict[str, Any]]:
    """识别图片中的文字
    
    Args:
        image: 图片路径或PIL.Image对象(支持UIAutomator2截图)
        keywords: 需要匹配的关键词列表
        region: 识别区域[x1,y1,x2,y2]
            
    Returns:
        List[Dict[str, Any]]: 包含识别结果的列表,每项包含:
            - box: 文字框坐标
            - text: 识别的文字
            - confidence: 置信度
    """
```

### extract_text_from_region
```python
def extract_text_from_region(self,
                           image: Union[str, Image.Image],
                           region: List[int],
                           keywords: List[str] = None) -> List[Dict[str, Any]]:
    """从指定区域识别文字
    
    Args:
        image: 图片路径或PIL.Image对象
        region: 识别区域[x1,y1,x2,y2]
        keywords: 需要匹配的关键词列表
            
    Returns:
        List[Dict[str, Any]]: OCR识别结果
    """
```

### find_text_position
```python
def find_text_position(self,
                      image: Union[str, Image.Image],
                      text: str,
                      region: List[int] = None) -> Optional[Dict[str, Any]]:
    """查找文字位置
    
    Args:
        image: 图片路径或PIL.Image对象
        text: 要查找的文字
        region: 查找区域[x1,y1,x2,y2]
            
    Returns:
        Optional[Dict[str, Any]]: 找到的文字信息，包含box和confidence
    """
```

## OCR结果格式

### 识别结果示例
```python
{
    'box': [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],  # 文字框四个角的坐标
    'text': "识别的文字",
    'confidence': 0.95  # 置信度
}
```

## 性能优化

### 1. 模型配置
- 使用轻量级模型
- 支持GPU加速
- 批量识别优化
  - cls_batch_num=1
  - rec_batch_num=1
  - det_db_score_mode='fast'

### 2. 图像预处理
- 区域裁剪减少计算量
- 图像缩放优化
- 灰度图转换
- 对比度增强

### 3. 内存管理
- 及时释放图像对象
- 避免重复加载模型
- 定期清理缓存

## 调试支持

### 调试信息
- OCR结果可视化
- 性能统计信息
- 识别区域标注
- 置信度分析

### 调试目录结构
```
debug/
└── {timestamp}/
    └── ocr/
        ├── input.jpg      # 输入图片
        ├── regions.jpg    # 区域标注
        ├── results.json   # 识别结果
        └── stats.json     # 性能统计
```

## 使用示例

```python
# 初始化
ocr_helper = OCRHelper(lang='ch')

# 从UIAutomator2截图识别
screenshot = device.screenshot()  # PIL.Image对象
results = ocr_helper.extract_text(
    image=screenshot,
    keywords=["目标文字"],
    region=[100, 200, 500, 800]
)

# 查找文字位置
position = ocr_helper.find_text_position(
    image=screenshot,
    text="登录",
    region=[0, 1600, 1080, 2400]
)

# 处理结果
for result in results:
    text = result['text']
    confidence = result['confidence']
    box = result['box']
    print(f"识别文字: {text}, 置信度: {confidence}")
```

## 注意事项

1. 图像质量
   - 建议使用清晰的截图
   - 避免模糊和变形
   - 合适的对比度

2. 区域选择
   - 精确定位目标区域
   - 避免干扰文字
   - 考虑文字方向

3. 性能优化
   - 合理使用关键词过滤
   - 适当的区域裁剪
   - 批量识别优化
