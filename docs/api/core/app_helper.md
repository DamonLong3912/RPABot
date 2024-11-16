# AppHelper API

## 类定义

### AppHelper
```python
class AppHelper:
    def __init__(self, device: u2.Device):
        """初始化应用管理助手
        
        Args:
            device: UIAutomator2设备实例
        """
```

## 主要方法

### check_and_install_app
```python
def check_and_install_app(self, package: str, apk_path: str = None) -> Dict[str, Any]:
    """检查应用是否已安装，如果未安装则启动安装过程
    
    Args:
        package: 包名
        apk_path: APK路径
        
    Returns:
        Dict[str, Any]: {
            'installed': bool,  # 是否已安装
            'need_install': bool,  # 是否需要安装
            'version': str,  # 当前版本号
        }
        
    Notes:
        - 使用UIAutomator2的app_info接口
        - 支持版本检查
        - 自动处理安装权限
    """
```

### verify_app_installed
```python
def verify_app_installed(self, package: str, timeout: int = 60) -> bool:
    """验证应用是否已成功安装
    
    Args:
        package: 包名
        timeout: 超时时间(秒)
            
    Returns:
        bool: 是否安装成功
        
    Notes:
        - 使用UIAutomator2的app_info接口
        - 支持等待安装完成
        - 自动处理安装确认
    """
```

### start_app
```python
def start_app(self, package: str, wait: bool = True) -> bool:
    """启动应用
    
    Args:
        package: 包名
        wait: 是否等待启动完成
            
    Returns:
        bool: 是否成功启动
    
    Notes:
        - 使用UIAutomator2的app_start接口
        - 支持等待应用启动完成
        - 自动处理ANR和崩溃
    """
```

### stop_app
```python
def stop_app(self, package: str) -> bool:
    """停止应用
    
    Args:
        package: 包名
            
    Returns:
        bool: 是否成功停止
        
    Notes:
        - 使用UIAutomator2的app_stop接口
        - 强制停止进程
        - 清理应用数据
    """
```

### clear_app_data
```python
def clear_app_data(self, package: str) -> bool:
    """清理应用数据
    
    Args:
        package: 包名
            
    Returns:
        bool: 是否清理成功
        
    Notes:
        - 使用UIAutomator2的app_clear接口
        - 清理所有数据和缓存
        - 重置应用状态
    """
```

## 应用状态监控

### 状态检查
- 应用是否安装
- 应用版本信息
- 应用运行状态
- ANR和崩溃检测
- 权限状态检查

### 状态变更处理
- 安装状态变更
- 运行状态变更
- 权限状态变更
- 异常状态处理

## 调试支持

### 调试信息
- 应用状态记录
- 安装过程日志
- 权限变更记录
- 异常信息采集

### 调试目录结构
```
debug/
└── {timestamp}/
    └── app/
        ├── status.json     # 状态记录
        ├── install.log     # 安装日志
        └── error.log      # 错误日志
```

## 使用示例

```python
# 初始化
app_helper = AppHelper(device)

# 检查并安装应用
result = app_helper.check_and_install_app(
    package="com.example.app",
    apk_path="app.apk"
)

if result['need_install']:
    # 等待安装完成
    installed = app_helper.verify_app_installed(
        package="com.example.app",
        timeout=60
    )
    
    if not installed:
        print("安装失败")
        exit(1)

# 启动应用
started = app_helper.start_app(
    package="com.example.app",
    wait=True
)

if not started:
    print("启动失败")
    exit(1)

# 清理应用数据
app_helper.clear_app_data("com.example.app")

# 停止应用
app_helper.stop_app("com.example.app")
```

## 注意事项

1. 应用安装
   - 确保APK文件存在
   - 检查安装权限
   - 处理版本冲突

2. 应用启动
   - 等待启动完成
   - 处理ANR和崩溃
   - 检查必要权限

3. 数据清理
   - 备份重要数据
   - 避免清理系统应用
   - 确认清理范围
