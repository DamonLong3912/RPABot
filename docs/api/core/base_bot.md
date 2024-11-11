# BaseBot API

## 类定义
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

### _check_conditions
```python
def _check_conditions(self, conditions: List[Dict[str, Any]]) -> bool:
    """检查步骤执行条件
    
    Args:
        conditions: 条件列表
        
    Returns:
        bool: 条件是否满足
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

## 调试支持

调试模式下，BaseBot 会：
1. 创建调试输出目录
2. 保存每个步骤的配置
3. 记录详细的执行日志
4. 保存截图和OCR结果

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
