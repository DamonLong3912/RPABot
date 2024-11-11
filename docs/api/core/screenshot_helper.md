# ScreenshotHelper API

## 类定义
```python
class ScreenshotHelper:
    def __init__(self, device_id: str):
        """初始化截图助手
        
        Args:
            device_id: 设备ID
        """
```

## 主要方法

### take_screenshot
```python
def take_screenshot(self, 
                   save_path: str,
                   region: Optional[List[int]] = None,
                   filename_prefix: str = "screenshot") -> str:
    """获取屏幕截图，支持区域截图
    
    Args:
        save_path: 保存目录
        region: 截图区域 [x1, y1, x2, y2]，None表示全屏
        filename_prefix: 文件名前缀
            
    Returns:
        str: 截图文件的完整路径
        
    Notes:
        - 自动创建保存目录
        - 自动进行图像优化
        - 支持区域截图
    """
```

### get_scale_factor
```python
def get_scale_factor(self) -> float:
    """获取当前缩放比例"""
```

### get_real_coordinates
```python
def get_real_coordinates(self, x: int, y: int) -> Tuple[int, int]:
    """将缩放后的坐标转换为实际坐标
    
    Args:
        x: 缩放图片上的x坐标
        y: 缩放图片上的y坐标
            
    Returns:
        Tuple[int, int]: 实际屏幕上的坐标(x, y)
    """
```

## 图像优化

### 预处理流程
1. 区域裁剪（如果指定）
2. 图像缩放（默认0.5倍）
3. 转换为灰度图
4. JPEG压缩优化（质量50）

### 性能优化
- 使用PIL进行图像处理
- 支持区域截图减少数据量
- 图像预处理减少OCR负担

## 使用示例

```python
# 初始化
screenshot_helper = ScreenshotHelper("device_id")

# 全屏截图
full_path = screenshot_helper.take_screenshot(
    save_path="screenshots",
    filename_prefix="full"
)

# 区域截图
region_path = screenshot_helper.take_screenshot(
    save_path="screenshots",
    region=[100, 200, 500, 800],
    filename_prefix="region"
)

# 坐标转换
real_x, real_y = screenshot_helper.get_real_coordinates(250, 400)
```
