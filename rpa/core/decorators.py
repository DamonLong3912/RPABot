import functools
import time
from ..utils.logger import get_logger

logger = get_logger(__name__)

def log_step(func):
    """记录步骤执行的装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"执行步骤: {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

def retry_step(max_retries=3, delay=1):
    """步骤重试装饰器
    
    Args:
        max_retries (int): 最大重试次数
        delay (int): 重试间隔(秒)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:  # 最后一次尝试
                        logger.error(f"步骤 {func.__name__} 执行失败，已重试 {max_retries} 次")
                        raise e
                    logger.warning(f"步骤 {func.__name__} 执行失败，{attempt + 1}/{max_retries} 次重试")
                    time.sleep(delay)
        return wrapper
    return decorator