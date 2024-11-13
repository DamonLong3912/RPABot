from typing import Dict, Any
from .base_action import BaseAction
import time

class SleepAction(BaseAction):
    """等待指定时间"""
    
    def execute(self, params: Dict[str, Any]) -> bool:
        try:
            seconds = float(params['seconds'])
            time.sleep(seconds)
            return True
            
        except Exception as e:
            self.logger.error(f"等待操作失败: {str(e)}")
            return False 

class HandlePopupsUntilTargetAction(BaseAction):
    """处理弹窗直到目标出现"""
    def execute(self, params: Dict[str, Any]) -> bool:
        return self.bot.ocr_interactive_actions.handle_popups_until_target(params) 