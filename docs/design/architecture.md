# RPA Framework 架构设计

## 整体架构

### 核心组件
1. BaseBot
   - 流程解析和执行
   - 变量管理
   - 条件判断
   - 步骤依赖

2. 工具类
   - AppHelper: 应用管理
   - OCRHelper: 文字识别
   - ScreenshotHelper: 截图处理
   - Logger: 日志管理

3. 动作实现
   - OCRActions: OCR相关动作
   - 其他动作类型（待扩展）

### 目录结构
```
rpa/
├── core/           # 核心功能
│   ├── actions/    # 动作实现
│   ├── base_bot.py # 基础机器人
│   └── decorators.py # 功能装饰器
└── utils/          # 工具类
    ├── app_helper.py  # 应用管理
    ├── ocr_helper.py  # OCR支持
    └── screenshot.py  # 截图处理
```

## 核心流程

### 1. 流程执行
```mermaid
graph TD
    A[加载配置] --> B[解析变量]
    B --> C[执行步骤]
    C --> D{检查条件}
    D -->|满足| E[执行动作]
    D -->|不满足| F[跳过步骤]
    E --> G[保存结果]
    G --> C
```

### 2. 应用管理
```mermaid
graph TD
    A[检查安装] -->|未安装| B[安装APK]
    A -->|已安装| D[启动应用]
    B --> C[等待安装]
    C --> D
    D -->|失败| E[重试启动]
    E -->|重试次数未超限| D
```

## 关键机制

### 1. 变量解析
- 环境变量
- 步骤结果引用
- 配置变量

### 2. 条件判断
- 步骤结果条件
- 自定义条件（待扩展）

### 3. 错误处理
- 动作重试
- 异常恢复
- 错误日志

### 4. 调试支持
- 调试目录结构
- 日志分级
- 结果可视化
