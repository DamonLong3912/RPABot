from typing import Dict, Any, List
from .base_action import BaseAction
import time

class LoopAction(BaseAction):
    """循环执行步骤"""
    
    def execute(self, params: Dict[str, Any]) -> bool:
        max_iterations = int(params.get('max_iterations', 100))
        steps = params.get('steps', [])
        break_conditions = params.get('break_conditions', [])
        
        self.logger.info(f"开始循环，最大迭代次数: {max_iterations}")
        
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            self.logger.info(f"开始第 {iteration} 次循环")
            
            try:
                # 执行循环中的步骤
                for step in steps:
                    step_type = step.get('action')
                    step_name = step.get('name', '未命名步骤')
                    
                    # 检查条件
                    conditions = step.get('conditions', [])
                    if conditions:
                        should_execute = True
                        for condition in conditions:
                            if condition['type'] == 'variables':
                                var_name = condition['variable']
                                expected_value = condition['value']
                                actual_value = self.bot.get_variable(var_name)
                                if actual_value != expected_value:
                                    should_execute = False
                                    break
                        if not should_execute:
                            self.logger.info(f"跳过步骤 {step_name}: 条件不满足")
                            continue
                    
                    self.logger.info(f"执行步骤: {step_name} (动作: {step_type})")
                    
                    # 解析参数中的变量
                    params = step.get('params', {})
                    resolved_params = {}
                    for key, value in params.items():
                        resolved_params[key] = self.bot._resolve_variable(value)
                    
                    # 执行动作并保存结果
                    result = self.bot._execute_action(step_type, resolved_params)
                    self.bot._save_step_result(step_name, result)
                
                # 检查是否满足退出条件
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
                
                if should_break:
                    self.logger.info("退出循环")
                    break
                
            except Exception as e:
                self.logger.error(f"循环执行出错: {str(e)}")
                return False
            
        return True