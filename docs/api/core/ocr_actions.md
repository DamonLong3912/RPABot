# OCR动作 API

## 类定义

### OCRActions
```python
class OCRActions:
    def __init__(self, bot: BaseBot):
        """OCR相关动作处理类
        
        Args:
            bot: BaseBot实例，提供UI自动化和OCR能力
        """
```

## 主要动作

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
            click_offset: 点击偏移量[x,y]，默认[0,0]
            
    Returns:
        bool: 是否成功点击
        
    Notes:
        - 使用UIAutomator2执行点击操作
        - 支持坐标偏移
        - 自动重试直到超时
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
        
    Notes:
        - 支持多个弹窗规则
        - 按优先级处理弹窗
        - 自动重试直到目标出现或超时
    """
```

### wait_for_input_ready
```python
def wait_for_input_ready(self, params: Dict[str, Any]) -> bool:
    """等待输入框就绪
    
    Args:
        params:
            timeout: 超时时间(秒)，默认5
            check_interval: 检查间隔(秒)，默认0.5
            
    Returns:
        bool: 输入框是否就绪
        
    Notes:
        - 检查输入法状态
        - 等待键盘显示
        - 自动处理输入法切换
    """
```

### input_text
```python
def input_text(self, params: Dict[str, Any]) -> bool:
    """输入文本
    
    Args:
        params:
            text: 要输入的文本
            clear_first: 是否先清空，默认True
            
    Returns:
        bool: 输入是否成功
        
    Notes:
        - 使用UIAutomator2的send_keys方法
        - 支持变量解析
        - 失败时尝试adb输入
    """
```

## 调试支持

### 调试信息
- OCR识别结果可视化
- 点击位置标注
- 弹窗处理过程记录
- 输入状态跟踪

### 调试目录结构
```
debug/
└── {timestamp}/
    └── {step_name}/
        ├── screenshot.png      # 原始截图
        ├── annotated.png      # 标注后的截图
        ├── ocr_results.yaml   # OCR结果
        └── action_log.txt     # 动作执行日志
```

## 使用示例

```yaml
# 等待并点击文字
- name: "等待并点击按钮"
  action: "wait_and_click_ocr_text"
  params:
    text: "开始使用"
    timeout: 30
    screenshot_region: [0, 1600, 1080, 2400]
    click_offset: [0, 10]

# 处理多个弹窗
- name: "处理启动弹窗"
  action: "handle_popups_until_target"
  params:
    target_text: "首页"
    screenshot_region: [0, 0, 1080, 2400]
    popups:
      - name: "协议与规则"
        patterns: ["同意", "协议与规则"]
        action: "click_first"
        priority: 1
      - name: "权限请求"
        patterns: ["允许", "授权"]
        action: "click_first"
        priority: 2

# 输入文本
- name: "输入手机号"
  action: "input_text"
  params:
    text: "${phone_number}"
    clear_first: true
``` 
</rewritten_file>