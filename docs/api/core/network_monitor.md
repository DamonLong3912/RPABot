# NetworkMonitor API

## 类定义

### NetworkMonitor
```python
class NetworkMonitor:
    def __init__(self, device: u2.Device):
        """初始化网络监控器
        
        Args:
            device: UIAutomator2设备实例
        """
```

## 主要方法

### start_monitoring
```python
def start_monitoring(self) -> None:
    """启动网络监控
    
    Notes:
        - 开启新线程监控网络状态
        - 记录网络请求和响应
        - 监控网络异常
    """
```

### stop_monitoring
```python
def stop_monitoring(self) -> None:
    """停止网络监控"""
```

### get_network_status
```python
def get_network_status(self) -> Dict[str, Any]:
    """获取当前网络状态
    
    Returns:
        Dict[str, Any]: {
            'connected': bool,  # 是否连接
            'type': str,       # 网络类型(WIFI/4G等)
            'strength': int,   # 信号强度
            'errors': List[str] # 错误记录
        }
    """
```

### wait_for_network_idle
```python
def wait_for_network_idle(self, timeout: int = 30, 
                         idle_time: float = 2.0) -> bool:
    """等待网络空闲
    
    Args:
        timeout: 超时时间(秒)
        idle_time: 空闲判定时间(秒)
            
    Returns:
        bool: 是否达到空闲状态
    """
```

## 监控数据

### 网络请求记录
```python
{
    'timestamp': '2024-01-01 12:00:00',
    'url': 'https://api.example.com/data',
    'method': 'POST',
    'status_code': 200,
    'response_time': 0.5,
    'error': None
}
```

### 网络状态记录
```python
{
    'timestamp': '2024-01-01 12:00:00',
    'connected': True,
    'type': 'WIFI',
    'strength': 4,
    'errors': []
}
```

## 调试支持

### 调试信息
- 网络请求记录
- 响应时间统计
- 错误追踪
- 网络状态变化

### 调试目录结构
```
debug/
└── {timestamp}/
    └── network/
        ├── requests.json    # 请求记录
        ├── errors.log      # 错误日志
        └── status.json     # 状态记录
```

## 使用示例

```python
# 初始化
monitor = NetworkMonitor(device)

# 启动监控
monitor.start_monitoring()

# 等待网络空闲
is_idle = monitor.wait_for_network_idle(timeout=30)

# 获取状态
status = monitor.get_network_status()
if not status['connected']:
    print(f"网络断开: {status['errors']}")

# 停止监控
monitor.stop_monitoring()
``` 