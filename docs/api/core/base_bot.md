# BaseBot API

## 类定义

### BaseBot
```python
class BaseBot:
    def __init__(self, device_id: str = None, debug: bool = False):
        """初始化RPA基础机器人
        
        Args:
            device_id: 设备ID，如果为None则使用当前连接的唯一设备
            debug: 是否启用调试模式
        """
```

## 核心组件

### UI自动化
- ui_device: UIAutomator2设备实例，处理UI自动化操作
- screenshot_helper: 基于UIAutomator2的截图工具
- app_helper: 应用管理工具

### OCR支持
- ocr_helper: OCR识别工具
- ocr_actions: OCR相关动作处理

### 监控组件
- network_monitor: 网络状态监控
- logcat_monitor: 日志监控

## 主要方法

### run_flow
```python
def run_flow(self, flow_config: Dict[str, Any]) -> None:
    """执行流程
    
    Args:
        flow_config: 流程配置字典
        
    Raises:
        RuntimeError: 流程执行失败时抛出
    """
```

### execute_step
```python
def execute_step(self, step: Dict[str, Any]) -> Any:
    """执行单个流程步骤
    
    Args:
        step: 步骤配置字典
        
    Returns:
        Any: 步骤执行结果
    """
```

## 变量管理

### set_variable
```python
def set_variable(self, name: str, value: Any) -> None:
    """设置变量值
    
    Args:
        name: 变量名
        value: 变量值
    """
```

### get_variable
```python
def get_variable(self, name: str, default: Any = None) -> Any:
    """获取变量值
    
    Args:
        name: 变量名
        default: 默认值
        
    Returns:
        Any: 变量值
    """
```

## UI操作

### click
```python
def click(self, x: int, y: int) -> bool:
    """点击指定坐标
    
    Args:
        x: x坐标
        y: y坐标
            
    Returns:
        bool: 点击是否成功
    """
```

### swipe
```python
def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, 
          duration: float = 0.1) -> bool:
    """滑动操作
    
    Args:
        start_x: 起始x坐标
        start_y: 起始y坐标
        end_x: 结束x坐标
        end_y: 结束y坐标
        duration: 持续时间(秒)
            
    Returns:
        bool: 滑动是否成功
    """
```

### input_text
```python
def input_text(self, text: str) -> bool:
    """输入文本
    
    Args:
        text: 要输入的文本
            
    Returns:
        bool: 输入是否成功
    """
```

## 调试支持

### 调试目录结构
```
debug/
└── {timestamp}/
    └── {step_name}/
        ├── step_config.yaml    # 步骤配置
        ├── screenshot.png      # 原始截图
        ├── annotated.png      # 标注后的截图
        └── ocr_results.yaml   # OCR结果
```

### 调试功能
- 自动创建调试目录
- 保存步骤配置
- 记录详细执行日志
- 保存OCR识别结果
- 可视化标注截图
- 网络请求监控
- Logcat日志采集

## 使用示例

```python
# 初始化(自动连接设备)
bot = BaseBot(debug=True)

# 手动指定设备
bot = BaseBot(device_id="device_id", debug=True)

# UI操作
bot.click(500, 800)
bot.swipe(500, 1000, 500, 200)
bot.input_text("测试文本")

# 变量操作
bot.set_variable("phone", "13800138000")
phone = bot.get_variable("phone")

# 加载并执行流程
with open("flow.yaml", "r", encoding="utf-8") as f:
    flow_config = yaml.safe_load(f)
bot.run_flow(flow_config)
```

## 环境变量

- ANDROID_HOME: Android SDK路径
- ASSETS_DIR: 资源文件目录
- RPA_PROJECT_ROOT: 项目根目录
- RPA_LOG_DIR: 日志目录
- RPA_LOG_LEVEL: 日志级别
- RPA_DEBUG: 是否启用调试模式