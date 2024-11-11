# RPA Framework 文档索引

> 在贡献文档前，请先阅读项目根目录下的 [CONTRIBUTING.md](../CONTRIBUTING.md) 文件。

## 项目结构

rpa_framework/
├── docs/ # 文档目录
│ ├── INDEX.md # 文档索引
│ ├── HISTORY.md # 开发历史记录
│ ├── requirements/ # 需求文档
│ │ ├── overview.md # 需求概述
│ │ └── detailed/ # 详细需求
│ │ ├── ocr.md # OCR功能需求
│ │ ├── flow_control.md # 流程控制需求
│ │ └── app_management.md # 应用管理需求
│ ├── design/ # 设计文档
│ │ ├── architecture.md # 架构设计
│ │ └── flow_schema.md # 流程定义格式
│ ├── api/ # API文档
│ │ └── core/ # 核心API文档
│ │ ├── app_helper.md # 应用管理API
│ └── tests/ # 测试文档
├── rpa/ # 源代码目录
│ ├── init.py
│ ├── core/ # 核心功能模块
│ │ ├── init.py
│ │ ├── base_bot.py # RPA基础类
│ │ ├── decorators.py # 装饰器
│ │ └── exceptions.py # 自定义异常
│ ├── assets/ # 内置资源文件
│ │ └── didi_gas.apk # 滴滴加油APK
│ ├── utils/ # 工具模块
│ │ ├── init.py
│ │ ├── logger.py # 日志工具
│ │ ├── ocr_helper.py # OCR工具类
│ │ ├── screenshot.py # 截图工具类
│ │ └── app_helper.py # 应用管理工具类
│ └── config/ # 配置模块
│ ├── init.py
│ └── flow_schema.json # 流程定义schema
├── flows/ # 流程定义文件目录
│ └── didi_gas_flow.yaml # 滴滴加油油价爬取流程
├── examples/ # 示例代码
│ └── simple_bot.py # 简单机器人示例
├── tests/ # 测试目录
│ ├── init.py
│ ├── test_core/ # 核心功能测试
│ └── test_utils/ # 工具类测试
├── CONTRIBUTING.md # 贡献指南
├── README.md # 项目说明
├── requirements.txt # Python依赖
├── run.py # 主运行脚本
└── setup.sh # 安装脚本

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

### OCR相关动作
- wait_for_ocr_text: 等待指定文字出现
- click_by_ocr: 通过OCR识别文字并点击

这些动作支持以下参数:
- text: 要识别的文字
- timeout: 超时时间(秒)
- screenshot_region: 截图区域[x1,y1,x2,y2]
- retry_times: 重试次数(仅click_by_ocr)

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
- 2024-03-25: 添加滴滴加油油价爬取流程
- 2024-03-21: 实现基础日志功能和BaseBot类 (v1.4)
- 2024-03-20: 添加前置条件管理功能相关文档 (v1.3)
- 2024-03-15: 添加截图功能相关文档 (v1.2)
- 2024-03-10: 更新OCR功能文档 (v1.1)
- 2024-03-05: 创建项目基础结构和文档 (v1.0)
- 2024-03-01: 添加run.py主运行脚本
- 2024-03-01: 完善setup.sh安装脚本