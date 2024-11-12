# OCRActions API

## 类定义

### OCRActions
```python
class OCRActions:
    def __init__(self, bot: BaseBot):
        """OCR相关动作处理类
        
        Args:
            bot: BaseBot实例
        """
```

## 主要方法

### wait_and_click_ocr_text
```python
def wait_and_click_ocr_text(self, params: Dict[str, Any]) -> bool:
    """等待指定文字出现并点击
    
    Args:
        params:
            text: 要等待的文字
            timeout: 超时时间(秒)，默认30
            check_interval: 检查间隔(秒)，默认2
            screenshot_region: 截图区域[x1,y1,x2,y2]
            
    Returns:
        bool: 是否成功点击
    """
```

### handle_popups_until_target
```python
def handle_popups_until_target(self, params: Dict[str, Any]) -> bool:
    """处理弹窗直到出现目标文本
    
    Args:
        params:
            timeout: 超时时间(秒)，默认60
            check_interval: 检查间隔(秒)，默认1
            target_text: 目标文本
            screenshot_region: 截图区域[x1,y1,x2,y2]，默认全屏
            popups: 弹窗配置列表
                - name: 弹窗名称
                - patterns: 匹配文本列表
                - action: 动作类型(默认click_first)
                - priority: 优先级(数字越小优先级越高)
            
    Returns:
        bool: 是否成功到达目标页面
    """
```

## 内部方法

### _click_ocr_result
```python
def _click_ocr_result(self, result: Dict[str, Any], screenshot_region: List[int] = None) -> bool:
    """点击OCR识别结果的中心位置
    
    Args:
        result: OCR识别结果
        screenshot_region: 截图区域[x1,y1,x2,y2]
    
    Returns:
        bool: 点击是否成功
    """
```

### _save_debug_info
```python
def _save_debug_info(self, step_name: str, screenshot_path: str, 
                    ocr_results: List[Dict], region: List[int] = None,
                    debug_dir: str = None):
    """保存调试信息
    
    Args:
        step_name: 步骤名称
        screenshot_path: 截图路径
        ocr_results: OCR结果
        region: 截图区域
        debug_dir: 调试目录
    """
```

## 调试支持

### 调试目录结构
```
debug/
└── {timestamp}/
    └── {step_name}/
        ├── screenshot.png      # 原始截图
        ├── annotated.png      # 标注后的截图
        └── ocr_results.yaml   # OCR结果
```

### 调试信息
- 原始截图保存
- OCR结果可视化（带框和文字标注）
- 坐标计算过程日志
- 点击操作结果记录

## 使用示例

```yaml
# 等待并点击文字
- name: "等待并点击安装确认"
  action: "wait_and_click_ocr_text"
  params:
    text: "继续安装"
    timeout: 30
    screenshot_region: [50, 1600, 1030, 2400]

# 处理多个弹窗
- name: "处理启动弹窗"
  action: "handle_popups_until_target"
  params:
    target_text: "附近油站"
    screenshot_region: [0, 0, 1080, 2400]
    popups:
      - name: "协议与规则"
        patterns: ["同意", "协议与规则"]
        action: "click_first"
        priority: 1
``` 
</rewritten_file>