# ScreenshotHelper API

## 类定义

### ScreenshotHelper
```python
class ScreenshotHelper:
    def __init__(self, device: u2.Device):
        """初始化截图助手
        
        Args:
            device: UIAutomator2设备实例
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
        
    Notes:
        - 使用UIAutomator2的screenshot接口
        - 支持区域截图和图像预处理
        - 自动进行缩放和优化
    """
```

### get_window_size
```python
def get_window_size(self) -> Tuple[int, int]:
    """获取屏幕尺寸
    
    Returns:
        Tuple[int, int]: (宽度, 高度)
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
   - 使用UIAutomator2的screenshot接口
   - 直接返回PIL.Image对象
   - 无需临时文件传输

2. 图像预处理
   - 区域裁剪（如果指定了region）
   - 图像缩放（默认0.5倍）
   - 转换为灰度图
   - JPEG压缩优化（质量50）

3. 性能优化
   - 使用PIL进行高效图像处理
   - 支持区域截图减少数据量
   - 图像预处理减少OCR负担
   - 内存优化，避免大图片

## 调试支持

### 调试信息
- 原始截图保存
- 处理后图片保存
- 坐标转换记录
- 性能统计信息

### 调试目录结构
```
debug/
└── {timestamp}/
    └── screenshot/
        ├── original.png    # 原始截图
        ├── processed.jpg   # 处理后图片
        └── metadata.json   # 元数据信息
```

## 使用示例

```python
# 初始化
screenshot_helper = ScreenshotHelper(device)

# 获取屏幕尺寸
width, height = screenshot_helper.get_window_size()
print(f"屏幕尺寸: {width}x{height}")

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

2. 性能考虑
   - 默认缩放比例0.5可根据需要调整
   - JPEG质量50在大多数场景下够用
   - 建议使用区域截图提升性能
   - 避免频繁全屏截图

3. 内存管理
   - 及时释放不需要的图片对象
   - 使用with语句处理图片文件
   - 定期清理调试目录