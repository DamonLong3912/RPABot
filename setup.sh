#!/bin/bash

echo "开始配置RPA Framework环境..."

# 检查Python版本
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if (( $(echo "$python_version < 3.8" | bc -l) )); then
    echo "错误: 需要Python 3.8或更高版本"
    exit 1
fi

# 检查pip
if ! command -v pip &> /dev/null; then
    echo "错误: 未找到pip，请先安装pip"
    exit 1
fi

# 创建虚拟环境
echo "创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 检查ADB
if ! command -v adb &> /dev/null; then
    echo "警告: 未找到ADB工具，请确保已安装Android SDK并配置环境变量"
    echo "可以从以下地址下载Android SDK Platform Tools:"
    echo "https://developer.android.com/studio/releases/platform-tools"
fi

# 检查设备连接
echo "检查Android设备连接..."
adb devices

# 设置执行权限
chmod +x run.py

echo "环境配置完成！"
echo "可以通过以下命令运行示例流程："
echo "python run.py --config flows/example_flow.yaml" 