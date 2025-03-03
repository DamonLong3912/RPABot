# RPA Framework

一个基于Python的智能RPA(机器人流程自动化)框架，支持通过YAML配置文件快速构建自动化流程。集成了UI自动化、OCR识别、中断继续执行、AI控制等多种能力，适用于Android应用的自动化测试与操作。

## 核心特性

- **智能化控制**
  - AI辅助控制：基于截图分析的智能操作建议和自动化(开发中)
  - OCR智能识别：集成PaddleOCR的文字识别能力
  - 自动化决策：支持基于规则的智能判断

- **强大的自动化能力** 
  - UI自动化：基于UIAutomator2的稳定UI控制
  - 动作系统：可扩展的模块化动作设计
  - 流程编排：通过YAML配置灵活定义流程

- **完善的工程化特性**
  - 配置驱动：所有功能通过配置文件组织
  - 监控系统：支持网络状态、日志等多维度监控
  - 设备管理：支持多设备心跳检测和自动恢复
  - 任务恢复：支持异常中断任务的断点续执行
  - 异常处理：智能重试机制和支持人为故障恢复
  - 异常通知：可配置飞书的异常通知机器人  
  - 调试能力：详细的日志记录和可视化调试
  - REST API：提供HTTP接口支持远程调用

## 快速开始

### 1. 环境准备

- Python 3.8+
- Android设备或模拟器（已开启USB调试）
- ADB工具（已配置环境变量）
- UIAutomator2（用于UI自动化）
- PaddleOCR（用于文字识别）

## 快速开始

1. 环境配置
```bash
# 克隆项目
git clone https://github.com/DamonLong3912/RPABot.git
cd RPABot


# 运行环境配置脚本
Linux/Mac:
chmod +x setup.sh
./setup.sh


Windows:
setup.bat
```

setup.sh/setup.bat 会自动完成以下配置：
- 检查 Python 版本要求(3.8+)
- 创建并激活虚拟环境
- 安装项目依赖
- 设置 ADB 工具
- 创建必要的目录
- 设置执行权限


2. 配置设备连接和全局配置
```yaml
# flows/**.yaml
device:
  # 设备IP地址,格式为ip:port或device_id,如192.168.1.100:5555,多个用逗号隔开
  ip: "172.16.1.9:39847,172.16.1.10:39847"  


# 根目录建立config.yaml(可选)
# 全局配置
log:
  level: "DEBUG"
  path: "logs"

# 数据库配置
database:
  host: localhost
  port: 3306
  user: your_username
  password: your_password
  database: rpa_db

# 其他全局配置
assets_dir: "assets"
```

3. 编写流程配置
```yaml
name: "示例流程"
version: "1.0"

# 设备配置
device:
  ip: "172.16.1.9:39847"  # 设备IP:端口, 或device_id

# yaml全局参数，此处可从API中获取替换
variables:
  var1: "手机"
  var2: "手机2"   

# 前置条件 一般用作安装应用 可跳过
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

提示:
- 运行方式一时，会自动加载*.yaml中的device设备，运行前请确保已填写正确device和设备已连接
- 运行方式二时，会自动加载flows/**.yaml和tests/**.yaml中的所有device设备，运行前请至少确保此次目标yaml已填写正确device和设备已连接

方式一:
```bash
# 确保在虚拟环境中
source venv/bin/activate

# 运行流程(使用默认配置文件config.yaml)
python run.py --flow flows/example_flow.yaml
```

方式二(API方式)(推荐):
```bash
# 运行流程(使用默认配置文件config.yaml)
python run.py --api --host 0.0.0.0 --port 5000
```

### 5. API调用示例

框架提供REST API支持通过HTTP接口调用:

```bash
# 启动流程
curl -X POST http://localhost:5000/api/v1/flow/start \
  -H "Content-Type: application/json" \
  -d '{
    "flow_file": "flows/example_flow.yaml",
    "task_id": "unique_task_id",     # 可选：用于任务恢复
    "start_step_index": 0            # 可选：数字0开始，指定开始步骤
  }'

# 查询状态
curl http://localhost:5000/api/v1/flow/status/<flow_id>

# 查询设备状态
curl http://localhost:5000/api/v1/devices
```


### 6. 日常辅助开发工具
```bash
# 确保已连接目标设备，控制台运行：
python -m uiautodev

# 在自动弹出的浏览器中观察手机页面布局
```



## 项目结构

```
rpa_framework/
├── docs/               # 项目文档
│   ├── design/        # 设计文档
│   │   ├── architecture.md    # 架构设计
│   │   ├── actions.md         # 动作系统设计
│   │   ├── device_manager.md  # 设备管理设计
│   │   └── flow_schema.md     # 流程定义格式
│   └── api/           # API文档
│       └── core/      # 核心API文档
├── rpa/               # 核心代码
│   ├── api/          # flask服务
│   ├── core/          # 框架核心
│   │   ├── actions/   # 动作实现
│   │   ├── network_monitor.py # 网络监控
│   │   └── base_bot.py # 基础机器人
│   ├── utils/         # 工具类
│   │   ├── screenshot.py     # 截图工具(UIAutomator2)
│   │   ├── ocr_helper.py    # OCR工具
│   │   └── app_helper.py    # 应用管理
│   └── assets/        # 内置资源文件
├── flows/             # 流程配置文件
├── tests/             # 测试用例
│   └── flows/         # 流程测试用例
│       ├── ui_actions_test.yaml     # UI动作测试
│       ├── ocr_actions_test.yaml    # OCR动作测试
│       ├── data_actions_test.yaml   # 数据动作测试
│       ├── app_actions_test.yaml    # 应用动作测试
│       └── flow_actions_test.yaml   # 流程控制动作测试
├── debug/             # 调试输出
└── logs/              # 日志输出
```

## 文档索引

- [架构设计](docs/design/architecture.md)
- [动作系统](docs/design/actions.md)
- [设备管理](docs/design/device_manager.md)
- [流程格式](docs/design/flow_schema.md)
- [API文档](docs/api/core/)
- [历史记录](docs/HISTORY.md)

## 版本记录

v1.7 设备管理增强
- 加入flask api服务
- 增加设备心跳检测机制
- 支持设备状态自动恢复
- 支持异常任务的设备监控
- 支持任务断点续执行
- 优化设备分配策略

v1.6 UI自动化增强
- 集成UIAutomator2框架
- 优化UI操作稳定性
- 增强输入框处理能力
- 添加网络状态监控
- 改进设备初始化流程


```

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目。详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

MIT License


## 测试

项目包含完整的测试用例集,按功能模块划分:

```bash
# 运行UI动作测试
python run.py --flow tests/flows/ui_actions_test.yaml

# 运行OCR动作测试
python run.py --flow tests/flows/ocr_actions_test.yaml

# 运行数据动作测试
python run.py --flow tests/flows/data_actions_test.yaml

# 运行应用动作测试
python run.py --flow tests/flows/app_actions_test.yaml

# 运行流程控制动作测试
python run.py --flow tests/flows/flow_actions_test.yaml

# 运行设备管理测试
python run.py --flow tests/flows/device_manager_test.yaml
```