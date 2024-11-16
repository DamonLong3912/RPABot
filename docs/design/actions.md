# RPA 动作系统设计

## 动作系统概述

动作系统是RPA框架的核心组件之一，负责执行具体的自动化操作。所有动作都继承自BaseAction基类，并按功能分类实现。

### 动作分类

1. UI动作 (基于UIAutomator2)
   - ClickAction: 点击指定坐标
   - SwipeAction: 屏幕滑动
   - ScrollAction: 屏幕滚动
   - InputAction: 文本输入
   - WaitForElementAction: 等待元素出现

2. OCR动作
   - GetTextFromRegionAction: 获取区域文字
   - VerifyTextInRegionAction: 验证区域文字
   - WaitAndClickOCRTextAction: 等待并点击文字
   - HandlePopupsUntilTargetAction: 处理弹窗直到目标出现
   - WaitForInputReadyAction: 等待输入框就绪

3. 数据动作
   - AppendToListAction: 追加到列表
   - ExportDataAction: 导出数据
   - SetVariableAction: 设置变量
   - GetVariableAction: 获取变量

4. 流程控制动作
   - LoopAction: 循环执行
   - ForEachAction: 遍历列表
   - SleepAction: 等待
   - CheckRepeatedValueAction: 检查重复值

5. 应用管理动作
   - CheckAndInstallAppAction: 检查并安装应用
   - VerifyAppInstalledAction: 验证应用已安装
   - StartAppAction: 启动应用
   - StopAppAction: 停止应用
   - ClearAppDataAction: 清理应用数据

## 动作实现规范

### BaseAction 基类
```python
class BaseAction:
    def __init__(self, bot: BaseBot):
        """初始化动作
        
        Args:
            bot: BaseBot实例，提供UI自动化和工具支持
        """
        self.bot = bot
        self.logger = bot.logger
        self.ui_device = bot.ui_device  # UIAutomator2设备实例
        self.screenshot_helper = bot.screenshot_helper
        self.ocr_helper = bot.ocr_helper

    def execute(self, params: Dict[str, Any]) -> Any:
        """执行动作"""
        raise NotImplementedError
        
    def validate_params(self, params: Dict[str, Any]) -> None:
        """验证参数"""
        raise NotImplementedError
```

### UI动作示例
```python
class ClickAction(BaseAction):
    """点击指定坐标"""
    
    def execute(self, params: Dict[str, Any]) -> bool:
        x = params['x']
        y = params['y']
        return self.ui_device.click(x, y)

class SwipeAction(BaseAction):
    """滑动操作"""
    
    def execute(self, params: Dict[str, Any]) -> bool:
        start_x = params['start_x']
        start_y = params['start_y']
        end_x = params['end_x']
        end_y = params['end_y']
        duration = params.get('duration', 0.1)
        return self.ui_device.swipe(
            start_x, start_y,
            end_x, end_y,
            duration=duration
        )
```

## 动作注册机制

### 动作映射表
```python
ACTION_MAP = {
    # UI动作
    'click': ClickAction,
    'swipe': SwipeAction,
    'scroll': ScrollAction,
    'input': InputAction,
    'wait_for_element': WaitForElementAction,
    
    # OCR动作
    'get_text': GetTextFromRegionAction,
    'verify_text': VerifyTextInRegionAction,
    'wait_and_click_text': WaitAndClickOCRTextAction,
    'handle_popups': HandlePopupsUntilTargetAction,
    
    # 数据动作
    'append_to_list': AppendToListAction,
    'export_data': ExportDataAction,
    'set_variable': SetVariableAction,
    'get_variable': GetVariableAction,
    
    # 流程控制
    'loop': LoopAction,
    'for_each': ForEachAction,
    'sleep': SleepAction,
    
    # 应用管理
    'check_and_install': CheckAndInstallAppAction,
    'start_app': StartAppAction,
    'stop_app': StopAppAction,
    'clear_app_data': ClearAppDataAction
}
```

## 动作执行流程

### 1. 参数解析
- 解析YAML配置
- 变量替换
- 参数验证

### 2. 动作执行
- 创建动作实例
- 执行前检查
- 调用execute方法
- 异常处理

### 3. 结果处理
- 保存执行结果
- 更新变量
- 记录调试信息

## 调试支持

### 1. 动作日志
- 参数记录
- 执行过程
- 异常信息
- 性能统计

### 2. 可视化调试
- UI操作标注
- OCR结果展示
- 截图保存
- 状态追踪

### 3. 错误处理
- 智能重试
- 异常恢复
- 错误报告
- 调试建议

## 使用示例

```yaml
# UI操作示例
- name: "点击按钮"
  action: "click"
  params:
    x: 500
    y: 800

# OCR操作示例
- name: "等待并点击文字"
  action: "wait_and_click_text"
  params:
    text: "开始使用"
    timeout: 30

# 应用管理示例
- name: "启动应用"
  action: "start_app"
  params:
    package: "com.example.app"
    wait: true
```