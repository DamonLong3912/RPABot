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
```

### OCR相关
```yaml
# 等待并点击文字
- name: "等待并点击按钮"
  action: "wait_and_click_ocr_text"
  params:
    text: "继续安装"
    timeout: 30
    check_interval: 1
    screenshot_region: [50, 1600, 1030, 2400]

# 处理弹窗
- name: "处理启动弹窗"
  action: "handle_popups_until_target"
  params:
    target_text: "附近油站"
    screenshot_region: [0, 0, 1080, 2400]
    timeout: 100
    check_interval: 1
    popups:
      - name: "协议与规则"
        patterns: ["同意", "协议与规则"]
        action: "click_first"
        priority: 1
      - name: "位置权限"
        patterns: ["仅在使用中允许", "位置信息"]
        action: "click_first"
        priority: 2
```

## 变量引用

### 环境变量
- ${ASSETS_DIR}: 资源目录
- ${RPA_PROJECT_ROOT}: 项目根目录
- ${RPA_LOG_DIR}: 日志目录

### 配置变量
- ${prerequisites.app.package}: 应用包名
- ${prerequisites.app.apk_path}: APK路径

### 步骤结果
- ${steps.step_name.result}: 步骤执行结果

## 条件配置

### 步骤结果条件
```yaml
conditions:
  - type: "step_result"
    step: "步骤名称"
    value: "期望值"
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
