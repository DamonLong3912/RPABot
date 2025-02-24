import os
import logging
import subprocess
from typing import Dict, Any, List
from pathlib import Path
import time
import yaml
from rpa.utils.logger import get_logger  # 改为绝对导入
from rpa.utils.screenshot import ScreenshotHelper
from rpa.utils.ocr_helper import OCRHelper
import uiautomator2 as u2  # 修改导入方式

class BaseBot:
    """RPA基础机器人类"""
    
    def __init__(self, flow_config: dict):
        # 加载配置文件
        self.config = self._load_config(flow_config)
        
        self.logger = get_logger(__name__)
        # 优先使用传入的debug参数,其次使用配置文件中的设置
        self.debug = self.config.get('debug', False)
        self.current_step_index = 0
        
        # 从流程配置中获取设备配置
        self.device_config = flow_config.get('device', {})
        self.device = self._init_device()
        
        # 设置环境变量
        assets_dir = self.config.get('assets_dir', 'assets')
        self.env = {
            "ASSETS_DIR": str(Path(__file__).parent.parent / assets_dir),
        }
        
        # 初始化工具类
        self.screenshot_helper = ScreenshotHelper(self.device_id)
        self.ocr_helper = OCRHelper()
        
    def _load_config(self, flow_config: dict) -> Dict[str, Any]:
        """加载配置文件
        
        Args:
            flow_config: 流程配置
            
        Returns:
            配置字典
            
        Raises:
            FileNotFoundError: 配置文件不存在时抛出
            yaml.YAMLError: 配置文件格式错误时抛出
        """
            
        try:
            with open(flow_config, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise RuntimeError(f"配置文件格式错误: {str(e)}")
        
    def _init_device(self):
        """根据配置初始化设备连接"""
        import uiautomator2 as u2
        
        # 优先使用IP连接
        if 'ip' in self.device_config:
            device = u2.connect(self.device_config['ip'])
        # 其次尝试序列号连接
        elif 'serial' in self.device_config:
            device = u2.connect(self.device_config['serial'])
        else:
            # 如果没有指定设备，抛出异常
            raise RuntimeError("未指定设备IP或序列号")
            
        # 应用设备配置
        if 'settings' in self.device_config:
            settings = self.device_config['settings']
            device.wait_timeout = settings.get('wait_timeout', 20)
            device.click_post_delay = settings.get('click_post_delay', 0.5)
            
        return device
        
    def _get_connected_devices(self) -> List[str]:
        """获取已连接的设备列表
        
        Returns:
            设备ID列表
        """
        result = subprocess.run(
            ['adb', 'devices'], 
            capture_output=True, 
            text=True,
            check=True
        )
        
        # 解析设备列表
        devices = []
        for line in result.stdout.split('\n')[1:]:  # 跳过第一行的"List of devices attached"
            if line.strip() and '\tdevice' in line:
                devices.append(line.split('\t')[0])
                
        return devices
        
    def _check_device_status(self) -> None:
        """检查设备状态
        
        Raises:
            RuntimeError: 设备状态异常时抛出
        """
        # 检查设备是否响应
        try:
            result = subprocess.run(
                ['adb', '-s', self.device_id, 'shell', 'getprop', 'sys.boot_completed'],
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.stdout.strip() != '1':
                raise RuntimeError("设备未完全启动")
                
        except subprocess.CalledProcessError:
            raise RuntimeError("设备状态检查失败")
            
    def _resolve_variable(self, value: str) -> str:
        """解析配置中的变量引用，支持嵌套引用
        
        Args:
            value: 包含变量引用的字符串
            
        Returns:
            解析后的字符串
        """
        if not isinstance(value, str):
            return value
            
        if "${" not in value:
            return value
            
        # 解析环境变量
        result = value
        for key, val in self.env.items():
            result = result.replace(f"${{{key}}}", str(val))
        
        # 解析流程配置中的变量
        if hasattr(self, 'current_flow_config'):
            # 解析 variables 中的变量
            variables = self.current_flow_config.get('variables', {})
            for key, val in variables.items():
                placeholder = f"${{variables.{key}}}"
                if placeholder in result:
                    result = result.replace(placeholder, str(val))
            
            # 解析 prerequisites 中的变量
            prerequisites = self.current_flow_config.get('prerequisites', {})
            for section, section_data in prerequisites.items():
                if isinstance(section_data, dict):
                    for key, val in section_data.items():
                        placeholder = f"${{prerequisites.{section}.{key}}}"
                        if placeholder in result:
                            result = result.replace(placeholder, str(val))
                            
        return result
        
    def run_flow(self, flow_config: Dict[str, Any]) -> None:
        """执行流程"""
        try:
            # 保存当前流程配置以变量解析使用
            self.current_flow_config = flow_config
            
            # 验证流程配置
            self._validate_flow_config(flow_config)
            
            # 执行流程步骤
            steps = flow_config.get('steps', [])
            for step in steps:
                self.current_step_index += 1  # 每个步骤执行前递增序号
                self._execute_step(step)
                
        except Exception as e:
            self.logger.error(f"流程执行失败: {str(e)}")
            raise RuntimeError(f"流程执行失败: {str(e)}")
        finally:
            # 清理流程配置
            self.current_flow_config = None
            
    def _validate_flow_config(self, config: Dict[str, Any]) -> None:
        """验证流程配置格式"""
        required_fields = ['name', 'version', 'steps']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"缺少必要的配置项: {field}")
                
    def _execute_step(self, step: Dict[str, Any]) -> None:
        """执行单个流程步骤"""
        step_type = step.get('action')
        step_name = step.get('name', '未命名步骤')
        
        try:
            # 统一处理条件检查
            if not self._should_execute_step(step):
                self.logger.info(f"跳过步骤 {step_name}: 条件不满足")
                return
            
            self.logger.info(f"执行步骤: {step_name} (动作: {step_type})")
            
            # 解析参数中的变量
            params = step.get('params', {})
            resolved_params = {}
            for key, value in params.items():
                resolved_params[key] = self._resolve_variable(value)
                
            # 执行动作并保存结果
            result = self._execute_action(step_type, resolved_params)
            self._save_step_result(step_name, result)
            
        except Exception as e:
            self.logger.error(f"流程执行失败: {str(e)}")
            raise RuntimeError(f"流程执行失败: {str(e)}")

    def _should_execute_step(self, step: Dict[str, Any]) -> bool:
        """检查步骤是否应该执行"""
        # 处理单个condition
        condition = step.get('condition')
        if condition:
            if isinstance(condition, str) and "${" in condition:
                # 解析条件变量
                var_name = condition[2:-1]  # 去掉 ${ 和 }
                condition_value = self.get_variable(var_name)
                if not condition_value:
                    self.logger.info(f"跳过步骤 {step.get('name', '')}: 条件不满足 ({var_name} = {condition_value})")
                    return False
        
        # 处理conditions列表
        conditions = step.get('conditions', [])
        if conditions:
            # 所有条件都必须满足
            for condition in conditions:
                condition_type = condition['type']
                if condition_type == 'variable':
                    var_name = condition['name']
                    expected_value = condition['value']
                    actual_value = self.get_variable(var_name)
                    if actual_value != expected_value:
                        self.logger.info(f"跳过步骤 {step.get('name', '')}: 条件不满足 ({var_name} = {actual_value}, 期望 = {expected_value})")
                        return False
                elif condition_type == 'step_result':
                    step_name = condition['step']
                    expected_value = condition['value']
                    step_result = self._get_step_result(step_name)
                    if step_result != expected_value:
                        self.logger.info(f"跳过步骤 {step.get('name', '')}: 条件不满足 ({step_name} = {step_result}, 期望 = {expected_value})")
                        return False
        
        return True

    def _save_step_result(self, step_name: str, result: Any) -> None:
        """保存步骤执行结果"""
        if not hasattr(self, '_step_results'):
            self._step_results = {}
        self._step_results[step_name] = result

    def _get_step_result(self, step_name: str) -> Any:
        """获取步骤执行结果"""
        return getattr(self, '_step_results', {}).get(step_name)

    def _execute_action(self, action_type: str, params: Dict[str, Any]) -> Any:
        """执行指定类型的动作"""
        try:
            from .actions import get_action_class
            action_class = get_action_class(action_type)
            
            # 缓存实例
            action_cache_name = f'_{action_type}_action'
            if not hasattr(self, action_cache_name):
                setattr(self, action_cache_name, action_class(self))
                
            action = getattr(self, action_cache_name)
            return action.execute(params)
            
        except Exception as e:
            self.logger.error(f"执行动作 {action_type} 失败: {str(e)}")
            raise

    def get_variable(self, name: str, default: Any = None) -> Any:
        """获取变量值"""
        if not hasattr(self, '_variables'):
            self._variables = {}
        return self._variables.get(name, default)
    
    def set_variable(self, name: str, value: Any) -> None:
        """设置变量值"""
        if not hasattr(self, '_variables'):
            self._variables = {}
        self._variables[name] = value