@echo off
chcp 65001
echo 开始配置RPA Framework环境...

:: 检查Python版本
python --version > nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8或更高版本
    exit /b 1
)

:: 以管理员权限创建和激活虚拟环境
echo 创建虚拟环境...
python -m venv venv

:: 等待虚拟环境创建完成
timeout /t 3 /nobreak > nul

:: 检测当前shell环境并选择合适的激活方式
echo 激活虚拟环境..
call venv\Scripts\activate

set PYTHONIOENCODING=utf8

:: 创建tools目录并解压adb
echo 配置ADB工具...
if not exist tools mkdir tools
if not exist tools\platform-tools\adb.exe (
    echo 解压Windows版本的platform-tools...
    powershell -command "Expand-Archive -Path tools\platform-tools-windows.zip -DestinationPath tools\ -Force"
)

:: 将adb工具路径添加到系统环境变量中
echo 配置ADB环境变量...
set "ADB_HOME=%cd%\tools\platform-tools"
set "PATH=%ADB_HOME%;%PATH%"

:: 永久添加ADB到系统环境变量
echo 永久添加ADB到系统环境变量...
powershell -Command "& {$adbPath = '%cd%\tools\platform-tools'; $currentPath = [Environment]::GetEnvironmentVariable('Path', 'Machine'); if ($currentPath -notlike '*' + $adbPath + '*') { [Environment]::SetEnvironmentVariable('Path', $currentPath + ';' + $adbPath, 'Machine'); }}"

:: 检查设备连接
echo 检查Android设备连接...
adb devices

:: 安装依赖
echo 安装依赖...
:: python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
:: pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements.txt

:: 创建必要的目录
echo 创建必要的目录...
if not exist logs mkdir logs
if not exist temp mkdir temp
if not exist debug mkdir debug

echo 环境配置完成！
echo 请重启软件或命令行窗口以生效
echo 请按照以下步骤运行程序：
echo 1. 首先运行：
echo    venv\Scripts\activate
echo.
echo 2. 然后运行以下命令之一：
echo    - 运行实例流程：
echo      python run.py --config flows/taobao_pay.yaml
echo.
echo    - 启动API服务：
echo      python run.py --api --host 0.0.0.0 --port 5000
echo      (API服务将在 http://127.0.0.1:5000/api/flow/start 上运行)