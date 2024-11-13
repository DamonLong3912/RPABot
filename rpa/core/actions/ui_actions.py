from typing import Dict, Any, List
from .base_action import BaseAction
import time
import subprocess
import cv2
import numpy as np
from pathlib import Path
import shutil

class WaitAndClickRegionAction(BaseAction):
    """等待并点击指定区域"""
    
    def execute(self, params: Dict[str, Any]) -> bool:
        region = params['region']
        timeout = params.get('timeout', 10)
        check_interval = params.get('check_interval', 1)
        step_name = params.get('name', 'click_region')
        
        # 验证区域参数
        if len(region) != 4:
            raise ValueError("region参数必须包含4个值: [x1, y1, x2, y2]")
        
        try:
            # 如果是调试模式，保存调试信息
            if self.bot.debug:
                x1, y1, x2, y2 = map(int, region)
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                
                annotations = [
                    {
                        'type': 'circle',
                        'data': [center_x, center_y, 10],
                        'color': (0, 0, 255),
                        'thickness': -1
                    },
                    {
                        'type': 'text',
                        'data': [f"Click: ({center_x}, {center_y})",
                                center_x + 10, center_y - 10],
                        'color': (0, 0, 255),
                        'thickness': 2
                    }
                ]
                
                self.save_debug_screenshot(
                    step_name=step_name,
                    region=region,
                    annotations=annotations,
                    extra_info={
                        'click_point': [center_x, center_y]
                    }
                )
            
            # 使用基类的点击方法
            return self._click_region(region)
            
        except Exception as e:
            self.logger.error(f"点击区域失败: {str(e)}")
            return False

class ScrollAction(BaseAction):
    """滚动屏幕"""
    
    def execute(self, params: Dict[str, Any]) -> bool:
        direction = params['direction']
        try:
            # 确保 distance 是整数类型
            distance = int(params['distance'])
        except (ValueError, TypeError):
            self.logger.error(f"distance 参数必须是整数，当前值: {params['distance']}")
            return False
        
        try:
            # 获取屏幕尺寸
            result = subprocess.run([
                'adb', '-s', self.bot.device_id, 'shell', 'wm size'
            ], capture_output=True, text=True, check=True)
            
            # 解析屏幕尺寸
            size = result.stdout.strip().split()[-1].split('x')
            screen_width = int(size[0])
            screen_height = int(size[1])
            
            # 计算滑动起点和终点
            start_x = screen_width // 2
            start_y = screen_height // 2
            
            if direction == 'up':
                end_x = start_x
                end_y = start_y - distance
            elif direction == 'down':
                end_x = start_x
                end_y = start_y + distance
            else:
                raise ValueError(f"不支持的滑动方向: {direction}")
            
            # 确保所有坐标都是整数
            start_x = int(start_x)
            start_y = int(start_y)
            end_x = int(end_x)
            end_y = int(end_y)
                
            # 执行滑动
            subprocess.run([
                'adb', '-s', self.bot.device_id, 'shell',
                f'input swipe {start_x} {start_y} {end_x} {end_y}'
            ], check=True)
            
            self.logger.info(f"滑动方向: {direction}, 距离: {distance}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"滑动失败: {str(e)}")
            return False