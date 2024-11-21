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
        
        try:
            # 先解析变量引用
            if isinstance(region, str) and region.startswith('${') and region.endswith('}'):
                var_name = region.strip('${}')
                region = self.bot.get_variable(var_name)
            
            # 处理region参数
            if isinstance(region, (list, tuple)):
                if len(region) != 4:
                    raise ValueError("region参数必须包含4个值: [x1, y1, x2, y2]")
                x1, y1, x2, y2 = map(int, region)
            elif isinstance(region, str):
                # 如果是字符串表示的列表，尝试解析
                if region.startswith('[') and region.endswith(']'):
                    try:
                        import ast
                        region_list = ast.literal_eval(region)
                        if len(region_list) != 4:
                            raise ValueError("region参数必须包含4个值: [x1, y1, x2, y2]")
                        x1, y1, x2, y2 = map(int, region_list)
                    except:
                        # 如果解析失败，尝试作为bounds字符串处理
                        bounds_parts = region.strip('[]').split('][')
                        if len(bounds_parts) != 2:
                            raise ValueError("bounds格式错误，应为: [x1,y1][x2,y2]")
                        x1, y1 = map(int, bounds_parts[0].split(','))
                        x2, y2 = map(int, bounds_parts[1].split(','))
                else:
                    raise ValueError("region参数格式错误")
            else:
                raise ValueError("region参数必须是列表、元组或字符串")
                        
            start_time = time.time()
            while time.time() - start_time < timeout:
                # 计算中心点
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                
                # 使用UIAutomator2执行点击
                self.ui_animator.click(center_x, center_y)
                
                return True
                
            self.logger.warning(f"等待点击区域超时: {region}")
            return False
            
        except Exception as e:
            self.logger.error(f"点击区域失败: {str(e)}")
            self.logger.debug(f"原始region参数: {region}, 类型: {type(region)}")
            return False

class ScrollAction(BaseAction):
    """滚动屏幕"""
    def execute(self, params: Dict[str, Any]) -> bool:
        direction = params['direction']
        distance = int(params['distance'])
        duration = params.get('duration', 0.5)  # 默认0.5秒
        
        try:
            # 获取屏幕尺寸
            window_size = self.ui_animator.window_size()
            width = window_size[0]
            height = window_size[1]
            screen_center = height // 2
            
            # 计算滑动的起点和终点，保证中心点在屏幕中间
            start_x = width // 2
            if direction == 'up':
                # 计算起点和终点，使滑动中心在屏幕中间
                half_distance = distance // 2
                start_y = min(screen_center + half_distance, height - 100)
                end_y = max(screen_center - half_distance, 100)
                
                # 使用UIAutomator2的swipe方法
                self.logger.debug(f"滑动: ({start_x}, {start_y}) -> ({start_x}, {end_y})")
                self.ui_animator.swipe(start_x, start_y, start_x, end_y, duration=duration)
                
            elif direction == 'down':
                # 计算起点和终点，使滑动中心在屏幕中间
                half_distance = distance // 2
                start_y = max(screen_center - half_distance, 100)
                end_y = min(screen_center + half_distance, height - 100)
                
                self.logger.debug(f"滑动: ({start_x}, {start_y}) -> ({start_x}, {end_y})")
                self.ui_animator.swipe(start_x, start_y, start_x, end_y, duration=duration)
                
            else:
                raise ValueError(f"不支持的滑动方向: {direction}")
                
            self.logger.info(f"滑动方向: {direction}, 距离: {distance}, 实际滑动: {abs(end_y - start_y)}")
            return True
            
        except Exception as e:
            self.logger.error(f"滑动失败: {str(e)}")
            self.logger.debug(f"参数: direction={direction}, distance={distance}, 屏幕尺寸={window_size}")
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
            
            return True
            
        except Exception as e:
            self.logger.error(f"点击区域失败: {str(e)}")
            return False