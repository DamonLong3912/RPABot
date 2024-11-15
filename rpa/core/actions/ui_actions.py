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
        step_name = params.get('name', 'wait_and_click_region')
        timeout = params.get('timeout', 30)        
        # 验证区域参数
        if len(region) != 4:
            raise ValueError("region参数必须包含4个值: [x1, y1, x2, y2]")
        
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                # 计算中心点
                x1, y1, x2, y2 = map(int, region)
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                
                # 使用UIAutomator2执行点击
                self.ui_animator.click(center_x, center_y)
                
                # 如果是调试模式，保存调试信息
                if self.bot.debug:
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
                        annotations=annotations,
                        extra_info={
                            'click_point': [center_x, center_y]
                        }
                    )
                
                return True
                
            self.logger.warning(f"等待点击区域超时: {region}")
            return False
            
        except Exception as e:
            self.logger.error(f"点击区域失败: {str(e)}")
            return False

class ScrollAction(BaseAction):
    """滚动屏幕"""
    def execute(self, params: Dict[str, Any]) -> bool:
        direction = params['direction']
        distance = int(params['distance'])
        
        try:
            # 获取屏幕尺寸
            window_size = self.ui_animator.window_size()
            width = window_size[0]
            height = window_size[1]
            
            # 计算滑动的起点和终点
            start_x = width // 2
            if direction == 'up':
                start_y = height * 2 // 3
                end_y = start_y - distance
                # 使用UIAutomator2的swipe方法
                self.ui_animator.swipe(start_x, start_y, start_x, end_y)
            elif direction == 'down':
                start_y = height // 3
                end_y = start_y + distance
                self.ui_animator.swipe(start_x, start_y, start_x, end_y)
            else:
                raise ValueError(f"不支持的滑动方向: {direction}")
                
            self.logger.info(f"滑动方向: {direction}, 距离: {distance}")
            return True
            
        except Exception as e:
            self.logger.error(f"滑动失败: {str(e)}")
            return False

class SwipeAction(BaseAction):
    """滑动操作"""
    def execute(self, params: Dict[str, Any]) -> bool:
        start_x = params['start_x']
        start_y = params['start_y']
        end_x = params['end_x']
        end_y = params['end_y']
        duration = params.get('duration', 500)  # 默认500ms
        
        try:
            # 使用UIAnimator2执行滑动
            self.ui_animator.swipe(
                start_x, start_y,
                end_x, end_y,
                duration=duration
            )
            return True
        except Exception as e:
            self.logger.error(f"滑动操作失败: {str(e)}")
            return False

class ClickRegionAction(BaseAction):
    """点击指定区域"""
    def execute(self, params: Dict[str, Any]) -> bool:
        region = params['region']
        
        if len(region) != 4:
            raise ValueError("region参数必须包含4个值: [x1, y1, x2, y2]")
        
        try:
            x1, y1, x2, y2 = map(int, region)
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            # 使用UIAnimator2执行点击
            self.ui_animator.click(center_x, center_y)
            
            if self.bot.debug:
                self.save_debug_screenshot(
                    step_name='click_region',
                    annotations=[{
                        'type': 'circle',
                        'data': [center_x, center_y, 10],
                        'color': (0, 0, 255),
                        'thickness': -1
                    }],
                    extra_info={'click_point': [center_x, center_y]}
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"点击区域失败: {str(e)}")
            return False