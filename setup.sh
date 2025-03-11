#!/bin/bash
# 设置UTF-8编码
export LANG=en_US.UTF-8

echo "开始配置RPA Framework环境..."

# 检查Python版本
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python，请先安装Python 3.8或更高版本"
    exit 1
fi

# 创建虚拟环境
echo "创建虚拟环境..."
python3 -m venv venv

# 等待虚拟环境创建完成
sleep 2

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

export PYTHONIOENCODING=utf8

# 创建tools目录并解压adb
echo "配置ADB工具..."
mkdir -p tools
if [[ ! -f tools/platform-tools/adb ]]; then
    echo "解压platform-tools..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # Mac系统
        unzip -o tools/platform-tools-mac.zip -d tools/
    else
        # Linux系统
        unzip -o tools/platform-tools-linux.zip -d tools/
    fi
    # 设置执行权限
    chmod +x tools/platform-tools/adb
fi

# 配置ADB环境变量
echo "配置ADB环境变量..."
ADB_HOME="$(pwd)/tools/platform-tools"
export PATH="$ADB_HOME:$PATH"

# 永久添加ADB到环境变量
echo "永久添加ADB到系统环境变量..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # Mac系统 - 添加到 .zshrc 或 .bash_profile
    SHELL_RC="$HOME/.zshrc"
    [[ ! -f "$SHELL_RC" ]] && SHELL_RC="$HOME/.bash_profile"
else
    # Linux系统
    SHELL_RC="$HOME/.bashrc"
fi

# 检查是否已存在PATH配置
if ! grep -q "export PATH=\"$ADB_HOME:\$PATH\"" "$SHELL_RC"; then
    echo "export PATH=\"$ADB_HOME:\$PATH\"" >> "$SHELL_RC"
fi

# 检查设备连接
echo "检查Android设备连接..."
adb devices

# 安装依赖
echo "安装依赖..."
#python3 -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
#pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements.txt

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p logs temp debug

echo "环境配置完成！"
echo "请重启终端以使环境变量生效"
echo "请按照以下步骤运行程序："
echo "1. 首先运行："
echo "   source venv/bin/activate"
echo ""
echo "2. 然后运行以下命令之一："
echo "   - 运行实例流程："
echo "     python run.py --config flows/taobao_pay.yaml"
echo ""
echo "   - 启动API服务："
echo "     python run.py --api --host 0.0.0.0 --port 5000"
echo "     (API服务将在 http://127.0.0.1:5000/api/flow/start 上运行)"

# 给脚本添加执行权限
chmod +x setup.sh 