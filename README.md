# RPA Framework

一个通用的RPA自动化框架，支持通过配置文件定义自动化流程。基于动作系统架构设计，提供灵活的自动化能力。

## 功能特点

- 动作系统：模块化的动作设计，支持UI、OCR、数据处理等多种动作类型
- 配置驱动：通过YAML配置文件定义自动化流程
- OCR支持：集成PaddleOCR，支持文字识别和智能点击
- 应用管理：支持应用安装、启动和状态检查
- 调试支持：详细的执行日志和可视化调试信息
- 错误处理：智能重试机制和异常恢复
- 性能优化：针对OCR场景的图像预处理优化
- 扩展机制：支持自定义动作和工具扩展

## 环境要求

- Python 3.8+
- Android设备或模拟器（已开启USB调试）
- ADB工具（已配置环境变量）
- PaddleOCR（用于文字识别）

## 快速开始

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 编写流程配置
```yaml
name: "示例流程"
version: "1.0"

prerequisites:
  app:
    package: "com.example.app"
    apk_path: "${ASSETS_DIR}/app.apk"

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

  - name: "处理弹窗"
    action: "handle_popups_until_target"
    params:
      target_text: "开始使用"
      popups:
        - patterns: ["同意", "确定"]
          action: "click_first"
```

3. 运行流程
```bash
python run.py --config flows/example_flow.yaml --debug
```

## 项目结构

```
rpa_framework/
├── docs/               # 项目文档
│   ├── design/        # 设计文档
│   │   ├── architecture.md    # 架构设计
│   │   ├── actions.md         # 动作系统设计
│   │   └── flow_schema.md     # 流程定义格式
│   └── api/           # API文档
├── rpa/               # 核心代码
│   ├── core/          # 框架核心
│   │   ├── actions/   # 动作实现
│   │   └── base_bot.py # 基础机器人
│   └── utils/         # 工具类
├── flows/             # 流程配置
└── tests/             # 测试用例
```

## 文档索引

- [架构设计](docs/design/architecture.md)
- [动作系统](docs/design/actions.md)
- [流程格式](docs/design/flow_schema.md)
- [历史记录](docs/HISTORY.md)

## 最新版本

v1.5 动作系统优化
- 优化动作执行流程
- 完善动作参数验证
- 增强动作调试功能
- 改进错误处理机制

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目。详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

MIT License