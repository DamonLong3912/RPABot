# RPA Framework 文档索引

> 在贡献文档前，请先阅读项目根目录下的 [CONTRIBUTING.md](../CONTRIBUTING.md) 文件。

## 项目结构

rpa_framework/
├── docs/               # 文档目录
│   ├── INDEX.md       # 文档索引
│   ├── HISTORY.md     # 开发历史记录
│   ├── requirements/  # 需求文档
│   │   ├── overview.md                # 需求概述
│   │   └── detailed/                  # 详细需求
│   │       ├── ocr.md                 # OCR功能需求
│   │       ├── flow_control.md        # 流程控制需求
│   │       └── app_management.md      # 应用管理需求
│   ├── design/       # 设计文档
│   │   ├── architecture.md            # 架构设计
│   │   └── flow_schema.md            # 流程定义格式
│   ├── api/          # API文档
│   │   └── core/                      # 核心API文档
│   │       ├── base_bot.md            # 基础机器人API
│   │       ├── ocr_helper.md          # OCR工具API
│   │       ├── screenshot_helper.md    # 截图工具API
│   │       └── app_helper.md          # 应用管理API
│   └── tests/        # 测试文档
├── rpa/              # 核心代码
│   ├── core/         # 核心功能模块
│   │   ├── actions/                   # 动作实现
│   │   │   └── ocr_actions.py         # OCR相关动作
│   │   ├── base_bot.py               # RPA基础类
│   │   ├── decorators.py             # 装饰器
│   │   └── exceptions.py             # 自定义异常
│   ├── assets/       # 内置资源文件
│   │   └── xxx.apk              # APK
│   └── utils/        # 工具模块
│       ├── logger.py                  # 日志工具
│       ├── ocr_helper.py             # OCR工具类
│       ├── screenshot.py             # 截图工具类
│       └── app_helper.py             # 应用管理工具类
├── flows/            # 流程配置文件
│   └── xxx_flow.yaml           # 流程配置文件
├── tests/            # 测试用例
│   ├── test_core/                    # 核心功能测试
│   └── test_utils/                   # 工具类测试
├── debug/            # 调试输出目录
├── logs/             # 日志输出目录
├── CONTRIBUTING.md   # 贡献指南
├── README.md         # 项目说明
├── requirements.txt  # Python依赖
├── run.py           # 主运行脚本
└── setup.sh         # 安装脚本

## 文档索引

### 需求文档
- [需求概述](requirements/overview.md) - 项目整体需求
- [OCR需求](requirements/detailed/ocr.md) - OCR相关功能需求
- [流程控制需求](requirements/detailed/flow_control.md) - 流程控制相关需求
- [应用管理需求](requirements/detailed/app_management.md) - 应用管理相关需求

### 设计文档
- [架构设计](design/architecture.md) - 系统整体架构
- [流程定义格式](design/flow_schema.md) - YAML流程定义详细说明

### API文档
- [BaseBot](api/core/base_bot.md) - 核心机器人类
- [OCRHelper](api/core/ocr_helper.md) - OCR工具类
- [ScreenshotHelper](api/core/screenshot_helper.md) - 截图工具类
- [AppHelper](api/core/app_helper.md) - 应用管理工具类

### 测试文档
- [测试计划](tests/test_plan.md) - 整体测试计划
- [测试用例](tests/test_cases.md) - 详细测试用例

这些动作支持以下参数:
- text: 要识别的文字
- timeout: 超时时间(秒)
- screenshot_region: 截图区域[x1,y1,x2,y2]

## OCR功能优化

### 图像预处理
- 自动缩放（默认0.5倍）
- 灰度转换
- JPEG压缩优化（质量50）
- 智能坐标转换

### 调试支持
- 按步骤组织的调试信息
- 截图和OCR结果可视化
- 坐标计算过程日志

## 最近更新

1. v1.4: OCR动作增强
   - 添加OCRActions类
   - 实现弹窗处理机制
   - 优化坐标计算

2. v1.3: 前置条件管理
   - 实现应用管理功能
   - 添加权限自动授予
   - 支持版本兼容性检查

3. v1.2: 截图功能增强
   - 添加区域截图支持
   - 优化图像预处理
   - 完善调试输出

4. v1.1: OCR功能集成
   - 集成PaddleOCR
   - 支持关键词过滤
   - 添加OCR API

5. v1.0: 项目初始化
   - 创建基础框架
   - 实现流程解析
   - 添加基础文档