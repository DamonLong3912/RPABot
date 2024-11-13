from typing import Dict, Any, List
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

class LoopAction(BaseAction):
    """循环执行步骤"""
    
    def execute(self, params: Dict[str, Any]) -> bool:
        max_iterations = params.get('max_iterations', 999999)
        break_conditions = params.get('break_conditions', [])
        steps = params.get('steps', [])
        
        # 先检查一次条件,如果已经满足就直接返回
        for condition in break_conditions:
            if condition['type'] == 'step_result':
                step_name = condition['step']
                expected_value = condition['value']
                step_result = self.bot._get_step_result(step_name)
                
                if step_result == expected_value:
                    self.logger.info(f"初始条件已满足: {step_name} = {expected_value}")
                    return True
                    
            elif condition['type'] == 'variable':
                var_name = condition['name']
                expected_value = condition['value']
                var_value = self.bot.get_variable(var_name)
                
                if var_value == expected_value:
                    self.logger.info(f"初始条件已满足: {var_name} = {expected_value}")
                    return True
        
        # 如果条件未满足,则开始循环
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            self.logger.info(f"开始第 {iteration} 次循环")
            
            # 执行步骤
            for step in steps:
                step_type = step.get('action')
                step_params = step.get('params', {})
                
                # 解析参数中的变量
                resolved_params = {}
                for key, value in step_params.items():
                    resolved_params[key] = self.bot._resolve_variable(value)
                
                # 执行步骤
                result = self.bot._execute_action(step_type, resolved_params)
                
                # 保存步骤结果
                if 'name' in step:
                    self.bot._save_step_result(step['name'], result)
            
            # 检查退出条件
            should_break = False
            for condition in break_conditions:
                if condition['type'] == 'step_result':
                    step_name = condition['step']
                    expected_value = condition['value']
                    step_result = self.bot._get_step_result(step_name)
                    
                    if step_result == expected_value:
                        self.logger.info(f"满足退出条件: {step_name} = {expected_value}")
                        should_break = True
                        break
                        
                elif condition['type'] == 'variable':
                    var_name = condition['name']
                    expected_value = condition['value']
                    var_value = self.bot.get_variable(var_name)
                    
                    if var_value == expected_value:
                        self.logger.info(f"满足退出条件: {var_name} = {expected_value}")
                        should_break = True
                        break
            
            if should_break:
                self.logger.info("循环退出")
                break
                
        return True