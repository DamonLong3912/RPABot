from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
import cv2
import time
import yaml
import numpy as np
from ...utils.logger import get_logger
import subprocess
import uiautomator2 as u2

class BaseAction:
    """动作基类"""
    
    def __init__(self, bot):
        """初始化动作
        
        Args:
            bot: BaseBot实例
        """
        self.bot = bot
        self.logger = get_logger(self.__class__.__name__)
        
        # 添加UIAnimator2引用
        if hasattr(bot, 'ui_animator'):
            self.ui_animator: u2.Device = bot.ui_animator
        if hasattr(bot, 'ocr_helper'):
            self.ocr_helper = bot.ocr_helper
        if hasattr(bot, 'screenshot_helper'):
            self.screenshot_helper = bot.screenshot_helper
        if hasattr(bot, 'device_id'):
            self.device_id = bot.device_id
    
    def execute(self, params: Dict[str, Any]) -> Any:
        """执行动作
        
        Args:
            params: 动作参数
            
        Returns:
            执行结果
            
        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError("子类必须实现execute方法")
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """获取变量值
        
        Args:
            name: 变量名
            default: 默认值
            
        Returns:
            变量值
        """
        return self.bot.get_variable(name, default)
    
    def set_variable(self, name: str, value: Any) -> None:
        """设置变量值
        
        Args:
            name: 变量名
            value: 变量值
        """
        self.bot.set_variable(name, value) 
    
    def _click_at_point(self, x: int, y: int, region: List[int] = None) -> bool:
        """使用UIAnimator2在指定坐标点执行点击"""
        try:
            click_x = int(x)
            click_y = int(y)
            
            if region:
                click_x += int(region[0])
                click_y += int(region[1])
            
            # 使用UIAnimator2执行点击
            self.ui_animator.click(click_x, click_y)
            self.logger.info(f"点击坐标: ({click_x}, {click_y})")
            return True
            
        except Exception as e:
            self.logger.error(f"点击失败: {str(e)}")
            return False
    
    def _click_region(self, region: List[int]) -> bool:
        """点击指定区域的中心位置
        
        Args:
            region: 区域坐标[x1,y1,x2,y2]
            
        Returns:
            bool: 点击是否成功
        """
        try:
            # 确保所有坐标为整数
            x1, y1, x2, y2 = map(int, region)
            
            # 计算中心点
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            return self._click_at_point(center_x, center_y)
            
        except Exception as e:
            self.logger.error(f"计算区域中心点失败: {str(e)}")
            return False
    
    def _is_element_clickable(self, element: Dict[str, Any], screenshot_path: str) -> bool:
        """检查元素是否可点击
        
        Args:
            element: OCR识别结果元素
            screenshot_path: 截图路径
            
        Returns:
            bool: 元素是否可点击
        """
        try:
            # 获取元素的box
            box = element['box']
            center_x = (box[0][0] + box[2][0]) // 2
            center_y = (box[0][1] + box[2][1]) // 2
            
            # 读取截图
            import cv2
            import numpy as np
            img = cv2.imread(screenshot_path)
            
            # 获取点击位置的颜色值
            color = img[int(center_y), int(center_x)]
            
            # 检查是否为半透明遮罩
            # 一般遮罩层的RGB值接近，且不会太暗或太亮
            rgb_diff = np.max(color) - np.min(color)
            if rgb_diff < 30 and 30 < np.mean(color) < 225:
                return False
            
            # 获取周围区域的颜色值
            region_size = 20
            y1 = max(0, int(center_y - region_size))
            y2 = min(img.shape[0], int(center_y + region_size))
            x1 = max(0, int(center_x - region_size))
            x2 = min(img.shape[1], int(center_x + region_size))
            
            region = img[y1:y2, x1:x2]
            
            # 计算区域内的颜色方差
            variance = np.var(region)
            
            # 如果方差太小，说明可能是纯色遮罩
            if variance < 100:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"检查元素可点击性时出错: {e}")
            return True  # 出错时默认认为可点击