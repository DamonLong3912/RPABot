from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
import cv2
import time
import yaml
import numpy as np
from ...utils.logger import get_logger
import subprocess

class BaseAction:
    """动作基类"""
    
    def __init__(self, bot):
        """初始化动作
        
        Args:
            bot: BaseBot实例
        """
        self.bot = bot
        self.logger = get_logger(self.__class__.__name__)
        
        # 常用工具类的引用
        if hasattr(bot, 'ocr_helper'):
            self.ocr_helper = bot.ocr_helper
        if hasattr(bot, 'screenshot_helper'):
            self.screenshot_helper = bot.screenshot_helper
        if hasattr(bot, 'app_helper'):
            self.app_helper = bot.app_helper
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
    
    def _click_at_point(self, x: Union[int, float], y: Union[int, float], 
                       region: List[int] = None) -> bool:
        """在指定坐标点执行点击
        
        Args:
            x: 点击位置的x坐标
            y: 点击位置的y坐标
            region: 截图区域[x1,y1,x2,y2]，如果提供则坐标会加上区域偏移
            
        Returns:
            bool: 点击是否成功
        """
        try:
            # 确保坐标为整数
            click_x = int(x)
            click_y = int(y)
            
            # 如果有区域偏移，加上偏移量
            if region:
                click_x += int(region[0])
                click_y += int(region[1])
            
            # 执行点击
            subprocess.run(
                ['adb', '-s', self.bot.device_id, 'shell', 
                 f'input tap {click_x} {click_y}'],
                check=True
            )
            
            self.logger.info(f"点击坐标: ({click_x}, {click_y})")
            return True
            
        except subprocess.CalledProcessError as e:
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
    
    def save_debug_screenshot(self, step_name: str, region: List[int] = None,
                            annotations: List[Dict] = None,
                            extra_info: Dict[str, Any] = None) -> None:
        """保存调试截图和信息"""
        if not self.bot.debug:
            return
            
        try:
            # 获取当前调试目录
            debug_dir = self.bot.current_debug_dir
            if not debug_dir:
                return
                
            # 添加时间戳到文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename_prefix = f"{step_name}_{timestamp}"
                
            # 获取截图
            screenshot = self.screenshot_helper.take_screenshot(
                save_path=str(debug_dir),
                region=region,
                filename_prefix=filename_prefix
            )
            
            # 如果有标注，创建标注后的图片
            if annotations:
                img = cv2.imread(screenshot)
                
                # 绘制区域框
                if region:
                    x1, y1, x2, y2 = map(int, region)
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # 绘制其他标注
                for annotation in annotations:
                    ann_type = annotation['type']
                    data = annotation['data']
                    color = annotation.get('color', (0, 0, 255))
                    thickness = annotation.get('thickness', 2)
                    
                    if ann_type == 'circle':
                        cv2.circle(img, (data[0], data[1]), data[2], color, thickness)
                    elif ann_type == 'text':
                        cv2.putText(img, data[0], (data[1], data[2]),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness)
                    elif ann_type == 'rectangle':
                        cv2.rectangle(img, (data[0], data[1]), (data[2], data[3]),
                                    color, thickness)
                
                # 保存标注后的图片（使用带时间戳的文件名）
                cv2.imwrite(str(debug_dir / f"{filename_prefix}_annotated.png"), img)
            
            # 保存调试信息（使用带时间戳的文件名）
            if extra_info or region or annotations:
                debug_info = {
                    'step_name': step_name,
                    'timestamp': timestamp,
                    'region': region,
                    'annotations': annotations
                }
                if extra_info:
                    debug_info.update(extra_info)
                
                with open(debug_dir / f"{filename_prefix}_debug_info.yaml", 'w',
                         encoding='utf-8') as f:
                    yaml.dump(debug_info, f, allow_unicode=True)
                    
        except Exception as e:
            self.logger.error(f"保存调试信息失败: {str(e)}")
    
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