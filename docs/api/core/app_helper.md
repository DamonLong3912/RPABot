# AppHelper API

## 类定义
```python
class AppHelper:
    def __init__(self, device_id: str):
        """初始化应用管理助手
        
        Args:
            device_id: 设备ID
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
        }
        
    Raises:
        ValueError: 需要安装但未提供APK路径时抛出
        RuntimeError: 安装启动失败时抛出
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
    """
```

### start_app
```python
def start_app(self, package: str, max_retries: int = 5, retry_interval: int = 2) -> bool:
    """启动应用
    
    Args:
        package: 包名
        max_retries: 最大重试次数
        retry_interval: 重试间隔(秒)
            
    Returns:
        bool: 是否成功启动
    
    Notes:
        - 启动失败会自动重试
        - 每次重试前会强制停止应用
        - 支持备选的monkey启动方案
    """
```

## 内部方法

### _start_install
```python
def _start_install(self, apk_path: str) -> None:
    """启动APK安装过程，不等待完成
    
    Args:
        apk_path: APK文件路径
        
    Raises:
        RuntimeError: 安装启动失败时抛出
    """
```

## 使用示例

```python
# 初始化
app_helper = AppHelper("device_id")

# 检查并安装应用
result = app_helper.check_and_install_app(
    package="com.example.app",
    apk_path="path/to/app.apk"
)

# 等待安装完成
if result['need_install']:
    installed = app_helper.verify_app_installed(
        package="com.example.app",
        timeout=60
    )

# 启动应用
started = app_helper.start_app(
    package="com.example.app",
    max_retries=5,
    retry_interval=2
)
