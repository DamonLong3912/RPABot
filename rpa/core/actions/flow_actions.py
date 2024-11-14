from typing import Dict, Any, List
from .base_action import BaseAction
import time
import ast

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
                self.bot._execute_step(step)
            
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

class ForEachAction(BaseAction):
    """循环遍历列表中的每个元素"""
    
    def execute(self, params: Dict[str, Any]) -> bool:
        try:
            # 获取列表和变量名
            list_param = params['list']
            variable_name = params['variable']
            steps = params.get('steps', [])
            
            # 获取列表数据并转换
            items = self.bot._resolve_variable(list_param)
            if isinstance(items, str):
                try:
                    items = ast.literal_eval(items)
                except:
                    self.logger.error(f"无法解析列表字符串: {items}")
                    return False
            
            if not isinstance(items, list):
                raise ValueError(f"参数 {list_param} 必须是列表类型，当前类型: {type(items)}")
            
            self.logger.info(f"开始遍历列表，共 {len(items)} 项")
            
            # 遍历列表
            for index, item in enumerate(items, 1):
                # 设置当前项的变量
                self.bot.set_variable(variable_name, item)
                self.logger.info(f"处理第 {index}/{len(items)} 项: {item}")
                
                # 执行步骤
                for step in steps:
                    # 使用 _execute_step 替代直接调用 _execute_action
                    self.bot._execute_step(step)
            
            self.logger.info("列表遍历完成")
            return True
            
        except Exception as e:
            self.logger.error(f"ForEach循环执行失败: {str(e)}")
            return False