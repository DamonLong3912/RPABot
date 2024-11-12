import os
from pathlib import Path
from loguru import logger

def setup_logger(log_file: str = "run.log", log_level="INFO"):
    """设置日志配置
    
    Args:
        log_file (str): 日志文件路径，默认为当前目录下的run.log
        log_level (str): 日志级别，默认INFO
    """
    # 如果log_file是相对路径，则保存在项目根目录的logs目录下
    if not os.path.isabs(log_file):
        project_root = os.environ.get('RPA_PROJECT_ROOT', os.getcwd())
        log_dir = os.path.join(project_root, 'logs')
        log_file = os.path.join(log_dir, log_file)
    
    # 创建日志目录
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # 移除默认的sink
    logger.remove()
    
    # 修改日志格式，添加进程ID
    format_str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    
    # 控制台输出
    logger.add(
        sink=lambda msg: print(msg),
        format=format_str,
        level=log_level,
        colorize=True,
        enqueue=True  # 启用队列模式，避免多进程日志混乱
    )
    
    # 文件输出
    logger.add(
        sink=log_file,
        format=format_str,
        level=log_level,
        rotation="10 MB",
        retention="1 week",
        enqueue=True  # 启用队列模式
    )

def get_logger(name: str = None):
    """获取logger实例
    
    Args:
        name: logger名称，通常使用__name__
        
    Returns:
        logger实例
    """
    return logger.bind(name=name)