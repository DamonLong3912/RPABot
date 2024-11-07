from typing import List, Optional, Tuple
import os
from PIL import Image
from loguru import logger

class ScreenshotHelper:
    def __init__(self, device):
        """
        初始化截图助手
        
        Args:
            device: uiautomator2设备实例
        """
        self.device = device
        self.logger = logger

    def take_screenshot(self, 
                       save_path: str,
                       region: Optional[List[int]] = None,
                       filename_prefix: str = "screenshot") -> str:
        """
        获取屏幕截图，支持区域截图
        
        Args:
            save_path: 保存目录
            region: 截图区域 [x1, y1, x2, y2]，None表示全屏
            filename_prefix: 文件名前缀
            
        Returns:
            截图文件的完整路径
        """
        try:
            # 确保保存目录存在
            os.makedirs(save_path, exist_ok=True)
            
            # 生成文件名
            import time
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.png"
            full_path = os.path.join(save_path, filename)
            
            # 获取截图
            self.device.screenshot(full_path)
            
            # 如果指定了区域，裁剪图片
            if region:
                with Image.open(full_path) as img:
                    x1, y1, x2, y2 = region
                    cropped = img.crop((x1, y1, x2, y2))
                    cropped.save(full_path)
            
            self.logger.info(f"截图已保存: {full_path}")
            return full_path
            
        except Exception as e:
            self.logger.error(f"截图失败: {str(e)}")
            raise 