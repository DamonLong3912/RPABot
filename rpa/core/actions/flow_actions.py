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
        if self._check_any_condition(break_conditions):
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
            if self._check_any_condition(break_conditions):
                self.logger.info("循环退出")
                break
                
        return True
    
    def _check_any_condition(self, conditions: List[Dict[str, Any]]) -> bool:
        """检查是否有任一条件满足"""
        for condition in conditions:
            if condition['type'] == 'step_result':
                step_name = condition['step']
                expected_value = condition['value']
                step_result = self.bot._get_step_result(step_name)
                
                if step_result == expected_value:
                    self.logger.info(f"满足退出条件: {step_name} = {expected_value}")
                    return True
                    
            elif condition['type'] == 'variable':
                var_name = condition['name']
                expected_value = condition['value']
                var_value = self.bot.get_variable(var_name)
                
                if var_value == expected_value:
                    self.logger.info(f"满足退出条件: {var_name} = {expected_value}")
                    return True
        
        return False

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

class CheckRepeatedValueAction(BaseAction):
    """检查列表中的值是否全部相同"""
    
    def execute(self, params: Dict[str, Any]) -> bool:
        try:
            # 获取参数
            list_param = params['list']
            min_length = params.get('min_length', 1)
            save_to = params.get('save_to')
            
            # 获取列表数据
            items = self.bot.get_variable(list_param)
            self.logger.info(f"检查列表内容: {list_param} = {items}")
            if not isinstance(items, list):
                self.logger.error(f"参数必须是列表类型，当前类型: {type(items)}")
                return False
                
            # 如果列表长度小于要求的最小长度，返回False
            if len(items) < min_length:
                result = False
            else:
                # 检查最近min_length个元素是否相同
                recent_items = items[-min_length:]
                result = all(x == recent_items[0] for x in recent_items)
            
            # 保存结果到变量
            if save_to:
                self.bot.set_variable(save_to, result)
            
            if result:
                self.logger.info(f"检测到连续{min_length}次重复值: {items[-1]}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"检查重复值失败: {str(e)}")
            return False