# BaseBot API

## 类定义

### BaseBot
```python
class BaseBot:
    def __init__(self, debug=False):
        """初始化RPA基础机器人
        
        Args:
            debug: 是否启用调试模式
        """
```

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

### _execute_step
```python
def _execute_step(self, step: Dict[str, Any]) -> None:
    """执行单个流程步骤
    
    Args:
        step: 步骤配置字典
    """
```

## 变量解析

### _resolve_variable
```python
def _resolve_variable(self, value: str) -> str:
    """解析配置中的变量引用
    
    Args:
        value: 包含变量引用的字符串
        
    Returns:
        str: 解析后的字符串
    """
```

## 步骤结果管理

### _save_step_result
```python
def _save_step_result(self, step_name: str, result: Any) -> None:
    """保存步骤执行结果
    
    Args:
        step_name: 步骤名称
        result: 执行结果
    """
```

### _get_step_result
```python
def _get_step_result(self, step_name: str) -> Any:
    """获取步骤执行结果
    
    Args:
        step_name: 步骤名称
        
    Returns:
        Any: 步骤结果
    """
```

## 动作执行

### _execute_action
```python
def _execute_action(self, action_type: str, params: Dict[str, Any]) -> Any:
    """执行指定类型的动作
    
    Args:
        action_type: 动作类型
        params: 动作参数
        
    Returns:
        Any: 动作执行结果
        
    Raises:
        ValueError: 未知的动作类型
    """
```

## 支持的动作类型

1. 应用管理
   - check_and_install_app: 检查并安装应用
   - wait_for_app_installed: 等待应用安装完成
   - start_app: 启动应用

2. OCR相关
   - wait_and_click_ocr_text: 等待并点击文字
   - handle_popups_until_target: 处理弹窗直到目标出现

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

## 使用示例

```python
# 初始化
bot = BaseBot(debug=True)

# 加载流程配置
with open("flow.yaml", "r", encoding="utf-8") as f:
    flow_config = yaml.safe_load(f)

# 执行流程
bot.run_flow(flow_config)
```

## 环境变量

- ASSETS_DIR: 资源文件目录
- RPA_PROJECT_ROOT: 项目根目录
- RPA_LOG_DIR: 日志目录
- RPA_LOG_LEVEL: 日志级别