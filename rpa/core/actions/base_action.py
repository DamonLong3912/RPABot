from typing import Dict, Any, List, Optional
from pathlib import Path
import cv2
import time
import yaml
import numpy as np
from ...utils.logger import get_logger

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
    
    def save_debug_screenshot(self, 
                            step_name: str,
                            region: Optional[List[int]] = None,
                            annotations: Optional[List[Dict]] = None,
                            extra_info: Optional[Dict] = None) -> Path:
        """保存调试截图和相关信息
        
        Args:
            step_name: 步骤名称
            region: 需要标注的区域 [x1, y1, x2, y2]
            annotations: 需要标注的内容列表，每项包含:
                - type: 标注类型 ('rect', 'circle', 'text')
                - data: 标注数据
                - color: 颜色 (B,G,R)
                - thickness: 线条粗细
            extra_info: 需要保存到yaml的额外信息
            
        Returns:
            Path: 调试目录路径
        """
        if not self.bot.debug:
            return None
            
        # 创建调试目录
        step_index = self.bot.current_step_index
        debug_dir = self.bot.debug_dir / f"{step_index:03d}_{step_name}"
        debug_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成单个timestamp用于所有文件
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # 获取并保存原始截图
        screenshot = self.bot.screenshot_helper.take_screenshot(
            save_path=str(debug_dir),
            filename_prefix=f"{timestamp}_original"
        )
        
        # 读取截图进行标注
        img = cv2.imread(screenshot)
        if img is not None:
            scale = self.bot.screenshot_helper.get_scale_factor()
            
            # 标注指定区域
            if region:
                x1, y1, x2, y2 = map(int, region)
                scaled_x1 = int(x1 * scale)
                scaled_y1 = int(y1 * scale)
                scaled_x2 = int(x2 * scale)
                scaled_y2 = int(y2 * scale)
                cv2.rectangle(img, (scaled_x1, scaled_y1), (scaled_x2, scaled_y2), 
                            (0, 255, 0), 2)
                
            # 添加其他标注
            if annotations:
                for ann in annotations:
                    ann_type = ann['type']
                    data = ann['data']
                    color = ann.get('color', (0, 0, 255))  # 默认红色
                    thickness = ann.get('thickness', 2)
                    
                    if ann_type == 'rect':
                        x1, y1, x2, y2 = map(lambda x: int(x * scale), data)
                        cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
                    
                    elif ann_type == 'circle':
                        x, y, radius = map(lambda x: int(x * scale), data)
                        cv2.circle(img, (x, y), radius, color, thickness)
                    
                    elif ann_type == 'text':
                        text, x, y = data
                        x, y = map(lambda x: int(x * scale), (x, y))
                        cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX,
                                  0.5, color, thickness)
            
            # 保存标注后的截图
            annotated_path = debug_dir / f"{timestamp}_annotated.png"
            cv2.imwrite(str(annotated_path), img)
        
        # 保存调试信息
        debug_info = {
            'step_index': step_index,
            'step_name': step_name,
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'region': region
        }
        
        # 添加额外信息
        if extra_info:
            debug_info.update(extra_info)
            
        info_path = debug_dir / f"{timestamp}_debug_info.yaml"
        with open(info_path, 'w', encoding='utf-8') as f:
            yaml.dump(debug_info, f, allow_unicode=True)
            
        return debug_dir