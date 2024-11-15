# RPA 动作系统设计

## 动作系统概述

动作系统是RPA框架的核心组件之一,负责执行具体的自动化操作。所有动作都继承自BaseAction基类,并按功能分类实现。

### 动作分类

1. UI动作
   - ClickRegionAction: 点击指定区域
   - WaitAndClickRegionAction: 等待并点击区域
   - ScrollAction: 屏幕滚动
   - SwipeAction: 屏幕滑动

2. OCR动作
   - GetTextFromRegionAction: 获取区域文字
   - VerifyTextInRegionAction: 验证区域文字
   - WaitAndClickOCRTextAction: 等待并点击文字
   - HandlePopupsUntilTargetAction: 处理弹窗直到目标出现
   - WaitForInputReadyAction: 等待输入框就绪
   - InputTextAction: 输入文字

3. 数据动作
   - AppendToListAction: 追加到列表
   - ExportDataAction: 导出数据
   - SetVariableAction: 设置变量
   - GetVariableAction: 获取变量

4. 流程控制动作
   - LoopAction: 循环执行
   - SleepAction: 等待

5. 应用管理动作
   - CheckAndInstallAppAction: 检查并安装应用
   - VerifyAppInstalledAction: 验证应用已安装
   - StartAppAction: 启动应用
   - WaitForAppInstalledAction: 等待应用安装完成

## 动作实现规范

### BaseAction 基类
```python
class BaseAction:
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger

    def execute(self, params: Dict[str, Any]) -> Any:
        """执行动作"""
        raise NotImplementedError
        
    def validate_params(self, params: Dict[str, Any]) -> None:
        """验证参数"""
        raise NotImplementedError
```

### 动作实现示例
```python
class WaitAndClickOCRTextAction(BaseAction):
    def validate_params(self, params):
        required = ['text', 'timeout']
        for param in required:
            if param not in params:
                raise ValueError(f"缺少必要参数: {param}")
                
    def execute(self, params):
        self.validate_params(params)
        text = params['text']
        timeout = params['timeout']
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            # 执行OCR识别和点击
            if self._try_click_text(text):
                return True
            time.sleep(1)
            
        raise TimeoutError(f"等待文字 '{text}' 超时")
```

## 动作注册机制

动作通过ACTION_MAP进行注册和管理:

```python
ACTION_MAP = {
    'click_region': ClickRegionAction,
    'wait_and_click_region': WaitAndClickRegionAction,
    'scroll': ScrollAction,
    # ...其他动作映射
}

def get_action_class(action_type: str) -> type:
    if action_type not in ACTION_MAP:
        raise ValueError(f"未知的动作类型: {action_type}")
    return ACTION_MAP[action_type]
```

## 动作调试支持

每个动作执行时会生成调试信息:

```
debug/
└── {timestamp}/
    └── {step_index}_{step_name}/
        ├── screenshot.png      # 执行前截图
        ├── annotated.png      # 标注后的截图
        └── action_result.yaml # 动作执行结果
```

## 动作参数说明

### 通用参数
- timeout: 超时时间(秒)
- check_interval: 检查间隔(秒)
- screenshot_region: 截图区域[x1,y1,x2,y2]

### OCR相关参数
- text: 要识别的文字
- patterns: 文字模式列表
- similarity: 相似度阈值

### UI相关参数
- x, y: 坐标位置
- direction: 滑动方向
- distance: 滑动距离

### 数据相关参数
- variable_name: 变量名
- value: 变量值
- file_path: 文件路径 