# 流程定义格式

## YAML 结构

### 基本结构
```yaml
name: "流程名称"
description: "流程描述"
version: "版本号"

variables:      # 全局变量
  var1: "值1"
  var2: "值2"

prerequisites:  # 前置条件
  app:         
    package: "应用包名"
    apk_path: "APK路径"
    version: "版本要求"
  device:      
    min_android: "最低Android版本"
    required_permissions: ["所需权限列表"]

monitors:      # 监控配置
  network:     # 网络监控
    enabled: true
    check_interval: 1

steps:         # 步骤列表
  - name: "步骤名称"
    action: "动作类型"
    params: 
      param1: "参数值"
    conditions:  # 执行条件
      - type: "条件类型"
        step: "依赖步骤"
        value: "期望值"
```

## 动作类型说明

### 1. UI动作
```yaml
# 点击操作
- name: "点击按钮"
  action: "click"
  params:
    x: 500
    y: 800

# 滑动操作
- name: "滑动屏幕"
  action: "swipe"
  params:
    start_x: 500
    start_y: 1000
    end_x: 500
    end_y: 200
    duration: 0.5

# 输入文本
- name: "输入文本"
  action: "input_text"
  params:
    text: "测试文本"
    clear_first: true
```

### 2. OCR动作
```yaml
# 等待并点击文字
- name: "等待并点击"
  action: "wait_and_click_ocr_text"
  params:
    text: "开始使用"
    timeout: 30
    screenshot_region: [0, 1600, 1080, 2400]
    click_offset: [0, 10]

# 处理弹窗
- name: "处理弹窗"
  action: "handle_popups_until_target"
  params:
    target_text: "首页"
    timeout: 60
    popups:
      - name: "协议弹窗"
        patterns: ["同意", "确定"]
        action: "click_first"
        priority: 1
```

### 3. 应用管理动作
```yaml
# 检查并安装应用
- name: "安装应用"
  action: "check_and_install_app"
  params:
    package: "com.example.app"
    apk_path: "${ASSETS_DIR}/app.apk"

# 启动应用
- name: "启动应用"
  action: "start_app"
  params:
    package: "com.example.app"
    wait: true
```

### 4. 流程控制动作
```yaml
# 循环执行
- name: "循环操作"
  action: "loop"
  params:
    max_iterations: 5
    break_conditions:
      - type: "variable"
        name: "found_target"
        value: true
    steps:
      - name: "子步骤"
        action: "scroll"
        params:
          direction: "up"
          distance: 300

# 遍历列表
- name: "遍历数据"
  action: "for_each"
  params:
    list: "${data_list}"
    variable: "item"
    steps:
      - name: "处理数据"
        action: "process_item"
        params:
          value: "${item}"
```

## 变量引用

### 1. 环境变量
```yaml
apk_path: "${ASSETS_DIR}/app.apk"
log_dir: "${RPA_LOG_DIR}"
```

### 2. 全局变量
```yaml
text: "${global_var}"
value: "${variables.user_data}"
```

### 3. 步骤结果
```yaml
target: "${steps.step_name.result}"
condition: "${steps.previous_step.success}"
```

## 监控配置

### 1. 网络监控
```yaml
monitors:
  network:
    enabled: true
    check_interval: 1  # 检查间隔(秒)
    idle_timeout: 30   # 空闲超时(秒)
    error_retry: 3     # 错误重试次数
```

### 2. 日志监控
```yaml
monitors:
  logcat:
    enabled: true
    tags: ["ActivityManager", "System.err"]
    levels: ["E", "W"]  # 日志级别
    save_path: "logs/"  # 保存路径
```

## 调试配置

### 1. 调试模式
```yaml
debug:
  enabled: true
  save_screenshots: true
  save_ocr_results: true
  network_tracking: true
  logcat_tracking: true
```

### 2. 错误处理
```yaml
error_handling:
  max_retries: 3
  retry_interval: 2
  screenshot_on_error: true
  save_debug_info: true
```

## 使用示例

完整的流程配置示例：

```yaml
name: "应用自动化流程"
version: "1.0"
description: "自动化测试流程"

variables:
  phone: "13800138000"
  retry_count: 3

prerequisites:
  app:
    package: "com.example.app"
    apk_path: "${ASSETS_DIR}/app.apk"
    version: ">=1.0.0"
  device:
    min_android: "7.0"
    required_permissions: ["CAMERA", "STORAGE"]

monitors:
  network:
    enabled: true
    check_interval: 1
  logcat:
    enabled: true
    tags: ["ActivityManager"]

debug:
  enabled: true
  save_screenshots: true

steps:
  - name: "安装应用"
    action: "check_and_install_app"
    params:
      package: "${prerequisites.app.package}"
      apk_path: "${prerequisites.app.apk_path}"

  - name: "启动应用"
    action: "start_app"
    params:
      package: "${prerequisites.app.package}"
      wait: true

  - name: "处理弹窗"
    action: "handle_popups_until_target"
    params:
      target_text: "首页"
      timeout: 60
      popups:
        - patterns: ["同意", "确定"]
          action: "click_first"
          priority: 1

  - name: "输入手机号"
    action: "input_text"
    params:
      text: "${variables.phone}"
      clear_first: true
```
