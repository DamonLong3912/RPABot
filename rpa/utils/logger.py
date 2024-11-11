import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logger(log_file: str = "run.log", log_level=logging.INFO):
    """设置日志配置
    
    Args:
        log_file (str): 日志文件路径，默认为当前目录下的run.log
        log_level (int): 日志级别，默认INFO
        
    Returns:
        logging.Logger: 配置好的logger对象
    """
    # 如果log_file是相对路径，则保存在项目根目录的logs目录下
    if not os.path.isabs(log_file):
        project_root = os.environ.get('RPA_PROJECT_ROOT', os.getcwd())
        log_dir = os.path.join(project_root, 'logs')
        log_file = os.path.join(log_dir, log_file)
    
    # 创建日志目录
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # 配置根logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # 清除已存在的处理器
    logger.handlers.clear()
    
    # 配置文件处理器
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # 配置控制台处理器
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger 