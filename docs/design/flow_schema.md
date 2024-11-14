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
  device:      
    min_android: "最低Android版本"
    required_permissions: ["所需权限列表"]

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

请参考 [动作系统设计](actions.md) 文档了解详细的动作类型。
