# RPA Framework

一个通用的RPA自动化框架，支持通过配置文件定义自动化流程。基于动作系统架构设计，提供灵活的自动化能力。

## 功能特点

- 动作系统：模块化的动作设计，支持UI、OCR、数据处理、流程控制等多种动作类型
- UI自动化：集成UIAutomator2，提供稳定可靠的UI操作能力
- 配置驱动：通过YAML配置文件定义自动化流程
- OCR支持：集成PaddleOCR，支持文字识别、智能点击和弹窗处理
- 应用管理：支持应用安装、启动和状态检查
- 调试支持：详细的执行日志和可视化调试信息
- 错误处理：智能重试机制和异常恢复
- 性能优化：针对OCR场景的图像预处理优化
- 扩展机制：支持自定义动作和工具扩展
- 流程控制：支持循环、条件判断和变量操作
- 网络监控：支持应用网络状态监控和异常处理

## 环境要求

- Python 3.8+
- Android设备或模拟器（已开启USB调试）
- ADB工具（已配置环境变量）
- UIAutomator2（用于UI自动化）
- PaddleOCR（用于文字识别）

## 快速开始

1. 环境配置
```bash
# 克隆项目
git clone https://github.com/your-username/rpa_framework.git
cd rpa_framework

# 运行环境配置脚本
chmod +x setup.sh
./setup.sh
```

setup.sh 会自动完成以下配置：
- 检查 Python 版本要求(3.8+)
- 创建并激活虚拟环境
- 安装项目依赖
- 检查 ADB 工具
- 检查设备连接
- 创建必要的目录
- 设置执行权限

2. 配置设备连接
```yaml
# config.yaml
device:
  # 设备IP地址,格式为ip:port,如192.168.1.100:5555,留空则使用USB连接
  ip: "172.16.1.9:39847"  

# 调试配置
debug: true

# 其他全局配置
assets_dir: "assets"
```

3. 编写流程配置
```yaml
name: "示例流程"
version: "1.0"

prerequisites:
  app:
    package: "com.example.app"
    apk_path: "${ASSETS_DIR}/app.apk"

monitors:
  network:
    enabled: true
    check_interval: 1
  logcat:
    enabled: true
    tags: ["ActivityManager"]

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
      target_text: "开始使用"
      popups:
        - patterns: ["同意", "确定"]
          action: "click_first"
```

4. 运行流程
```bash
# 确保在虚拟环境中
source venv/bin/activate

# 运行流程(使用默认配置文件config.yaml)
python run.py --flow flows/example_flow.yaml

# 指定配置文件
python run.py --flow flows/example_flow.yaml --config custom_config.yaml
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
│       └── core/      # 核心API文档
├── rpa/               # 核心代码
│   ├── core/          # 框架核心
│   │   ├── actions/   # 动作实现
│   │   ├── network_monitor.py # 网络监控
│   │   └── base_bot.py # 基础机器人
│   ├── utils/         # 工具类
│   │   ├── screenshot.py     # 截图工具(UIAutomator2)
│   │   ├── ocr_helper.py    # OCR工具
│   │   └── app_helper.py    # 应用管理
│   └── assets/        # 内置资源
├── flows/             # 流程配置
├── tests/             # 测试用例
├── debug/             # 调试输出
└── logs/              # 日志输出
```

## 文档索引

- [架构设计](docs/design/architecture.md)
- [动作系统](docs/design/actions.md)
- [流程格式](docs/design/flow_schema.md)
- [API文档](docs/api/core/)
- [历史记录](docs/HISTORY.md)

## 最新版本

v1.6 UI自动化增强
- 集成UIAutomator2框架
- 优化UI操作稳定性
- 增强输入框处理能力
- 添加网络状态监控
- 改进设备初始化流程

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目。详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

MIT License