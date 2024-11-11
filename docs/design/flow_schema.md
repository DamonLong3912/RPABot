# 流程定义格式

## YAML 结构

### 基本结构
```yaml
name: "流程名称"
description: "流程描述"
version: "版本号"

prerequisites:  # 前置条件
  app:         # 应用相关
    package: "应用包名"
    apk_path: "APK路径"
  device:      # 设备要求
    min_android: "最低Android版本"
    required_permissions: ["所需权限列表"]

steps:         # 步骤列表
  - name: "步骤名称"
    action: "动作类型"
    params: 
      param1: "参数值"
    conditions:
      - type: "条件类型"
        step: "依赖步骤"
        value: "期望值"
```

### 变量引用
- 环境变量: ${ENV_NAME}
- 配置变量: ${prerequisites.app.package}
- 步骤结果: ${steps.step_name.result}

## 支持的动作类型

### 应用管理
```yaml
# 检查并安装应用
- name: "检查应用安装"
  action: "check_and_install_app"
  params:
    package: "com.example.app"
    apk_path: "${ASSETS_DIR}/app.apk"

# 等待应用安装完成
- name: "等待安装完成"
  action: "wait_for_app_installed"
  params:
    package: "com.example.app"
    timeout: 60

# 启动应用
- name: "启动应用"
  action: "start_app"
  params:
    package: "com.example.app"
    max_retries: 5
    retry_interval: 2
```

### OCR操作
```yaml
# 等待文字出现
- name: "等待文字"
  action: "wait_for_ocr_text"
  params:
    text: "目标文字"
    timeout: 30
    screenshot_region: [x1, y1, x2, y2]

# 点击文字
- name: "点击文字"
  action: "click_by_ocr"
  params:
    text: "目标文字"
    retry_times: 3
```

## 条件配置

### 步骤结果条件
```yaml
conditions:
  - type: "step_result"
    step: "步骤名称"
    value: "期望值"
```

### 示例
```yaml
- name: "等待安装完成"
  action: "wait_for_app_installed"
  params:
    package: "${prerequisites.app.package}"
  conditions:
    - type: "step_result"
      step: "检查应用安装"
      value: "need_install"
```
