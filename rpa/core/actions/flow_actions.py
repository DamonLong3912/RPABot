from typing import Dict, Any, List, Optional
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
        
        # 清理break conditions相关的step results
        self._clear_break_condition_results(break_conditions)
        
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
                
                # 检查是否需要中断循环
                if self.bot.get_variable('_break_current_loop', False):
                    self.bot.set_variable('_break_current_loop', False)  # 重置标记
                    self.logger.info("检测到中断信号，提前结束循环")
                    return True
                    
                # 检查是否需要继续下一次循环
                if self.bot.get_variable('_continue_current_loop', False):
                    self.bot.set_variable('_continue_current_loop', False)  # 重置标记
                    self.logger.info("检测到继续信号，跳过剩余步骤")
                    break
            
            # 检查退出条件
            if self._check_any_condition(break_conditions):
                self.logger.info("循环退出")
                break
                
        return True
        
    def _clear_break_condition_results(self, conditions: List[Dict[str, Any]]) -> None:
        """清理与break conditions相关的step results"""
        for condition in conditions:
            if condition['type'] == 'step_result':
                step_name = condition['step']
                # 只清理break condition中涉及的step result
                if hasattr(self.bot, '_step_results'):
                    self.bot._step_results.pop(step_name, None)
    
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

class BreakLoopAction(BaseAction):
    """中断当前循环的动作"""
    
    def execute(self, params: Optional[Dict[str, Any]] = None) -> bool:
        """执行中断循环动作
        
        Returns:
            bool: 始终返回True以表示成功执行
        """
        self.bot.set_variable('_break_current_loop', True)
        return True

class ForEachAction(BaseAction):
    """循环遍历列表中的每个元素"""
    
    def execute(self, params: Dict[str, Any]) -> bool:
        try:
            # 获取列表和变量名
            list_param = params['list']
            variable_name = params['variable']
            steps = params.get('steps', [])
            
            # 如果是字符串且包含变量引用，则获取变量值
            if isinstance(list_param, str):
                if list_param.startswith('${'):
                    var_name = list_param.strip('${}')
                    items = self.bot.get_variable(var_name)
                else:
                    # 尝试解析字符串为列表
                    try:
                        import ast
                        items = ast.literal_eval(list_param)
                    except:
                        raise ValueError(f"无法解析列表字符串: {list_param}")
            else:
                # 检查是否可以转换为列表
                try:
                    items = list(list_param)
                except:
                    raise ValueError(f"参数无法转换为列表: {list_param}")
            
            # 确保是列表类型
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
                    self.bot._execute_step(step)
                    
                    # 检查是否需要中断循环
                    if self.bot.get_variable('_break_current_loop', False):
                        self.bot.set_variable('_break_current_loop', False)  # 重置标记
                        self.logger.info("检测到中断信号，提前结束循环")
                        return True
                        
                    # 检查是否需要继续下一次循环
                    if self.bot.get_variable('_continue_current_loop', False):
                        self.bot.set_variable('_continue_current_loop', False)  # 重置标记
                        self.logger.info("检测到继续信号，跳过剩余步骤")
                        break
            
            self.logger.info("列表遍历完成")
            return True
            
        except Exception as e:
            self.logger.error(f"ForEach循环执行失败: {str(e)}")
            return False

class CheckNoRepeatedValueAction(BaseAction):
    """检查值是否不在列表中存在（用于判断是否为新值）"""
    
    def execute(self, params: Dict[str, Any]) -> bool:
        try:
            # 获取参数
            value = params.get('value')  # 要检查的值
            list_param = params['list']  # 列表名称
            save_to = params.get('save_to')  # 保存结果的变量名
            
            # 解析value中的变量引用
            if isinstance(value, str) and "${" in value:
                var_name = value[2:-1]  # 去掉 ${ 和 }
                value = self.bot.get_variable(var_name)
            
            # 获取列表数据
            items = self.bot.get_variable(list_param)
            if items is None:
                items = []  # 如果列表不存在，初始化为空列表
                self.bot.set_variable(list_param, items)
            
            self.logger.info(f"检查值 '{value}' 是否不在列表 {list_param} 中")
            
            if not isinstance(items, list):
                self.logger.error(f"参数必须是列表类型，当前类型: {type(items)}")
                return False
                
            # 检查值是否不在列表中
            result = value not in items
            
            # 保存结果到变量
            if save_to:
                self.bot.set_variable(save_to, result)
            
            if result:
                self.logger.info(f"值 '{value}' 在列表中不存在（新值）")
            else:
                self.logger.info(f"值 '{value}' 在列表中已存在（重复值）")
            
            return result
            
        except Exception as e:
            self.logger.error(f"检查值是否不存在失败: {str(e)}")
            return False

class ContinueLoopAction(BaseAction):
    """继续当前循环的动作"""
    
    def execute(self, params: Optional[Dict[str, Any]] = None) -> bool:
        """执行继续循环动作
        
        Returns:
            bool: 始终返回True以表示成功执行
        """
        self.bot.set_variable('_continue_current_loop', True)
        return True