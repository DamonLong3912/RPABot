# ScreenshotHelper API

## 类定义

### ScreenshotHelper
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
    """获取屏幕截图
    
    Args:
        save_path: 保存目录
        region: 截图区域 [x1, y1, x2, y2]，None表示全屏
        filename_prefix: 文件名前缀
            
    Returns:
        str: 截图文件的完整路径
    """
```

### get_scale_factor
```python
def get_scale_factor(self) -> float:
    """获取当前缩放比例
    
    Returns:
        float: 当前使用的缩放比例(默认0.5)
    """
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

## 图像处理流程

1. 截图获取
   - 使用ADB screencap命令获取原始截图
   - 临时保存到设备/data/local/tmp/目录
   - 通过ADB pull命令获取到本地

2. 图像预处理
   - 区域裁剪（如果指定了region）
   - 图像缩放（默认0.5倍）
   - 转换为灰度图
   - JPEG压缩优化（质量50）

3. 性能优化
   - 使用PIL进行高效图像处理
   - 支持区域截图减少数据量
   - 图像预处理减少OCR负担
   - 自动清理设备临时文件

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
print(f"实际坐标: ({real_x}, {real_y})")
```

## 注意事项

1. 截图区域
   - region参数使用[x1,y1,x2,y2]格式
   - 坐标值必须在屏幕范围内
   - 建议使用标准分辨率(1080x2400)

2. 文件管理
   - 自动创建保存目录
   - 文件名格式: {prefix}_{timestamp}.jpg
   - 自动清理临时文件

3. 性能考虑
   - 默认缩放比例0.5可根据需要调整
   - JPEG质量50在大多数场景下够用
   - 建议使用区域截图提升性能