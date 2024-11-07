# RPA Framework

一个通用的RPA自动化框架，支持通过配置文件定义自动化流程。
本项目是AI copilot的文档式编程尝试，通过文档/代码的同步更新完成功能迭代。

## 功能特点

- 配置驱动：通过YAML配置文件定义自动化流程
- 模块化设计：支持自定义动作组件
- 多平台支持：支持Android设备自动化操作
- 灵活扩展：提供插件机制，方便扩展新功能
- 日志追踪：详细的执行日志，便于调试和监控

## 环境要求

- Python 3.8+
- Android设备或模拟器（已开启USB调试）
- ADB工具（已配置环境变量）
- OCR支持（可选，用于文字识别）

## 项目结构

```
rpa_framework/
├── docs/               # 项目文档
├── flows/             # 流程配置文件
├── rpa/               # 核心代码
│   ├── core/         # 框架核心
│   └── utils/        # 工具类
└── tests/            # 测试用例
```

## 安装步骤

1. 克隆项目
```bash
git clone https://github.com/your-repo/rpa_framework.git
cd rpa_framework
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境
```bash
./setup.sh
```

## 快速开始

1. 准备配置文件 `flows/example_flow.yaml`:

```yaml
name: 示例流程
description: 这是一个示例自动化流程
steps:
  - name: 点击按钮
    action: click
    target: "按钮1"
    
  - name: 输入文本
    action: input
    target: "输入框"
    value: "测试文本"
```

2. 运行自动化流程:

```bash
python run.py --config flows/example_flow.yaml
```

## 详细文档

- [使用指南](docs/INDEX.md)
- [历史记录](docs/HISTORY.md)
- [需求概览](docs/requirements/overview.md)

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目。

## 许可证

MIT License