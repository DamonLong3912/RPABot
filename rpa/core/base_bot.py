import os
import logging
import subprocess
from typing import Dict, Any, List
from pathlib import Path
from ..utils.app_helper import AppHelper  # 修改导入路径
import time
import yaml
from ..utils.logger import get_logger  # 修改导入路径
from ..utils.screenshot import ScreenshotHelper
from ..utils.ocr_helper import OCRHelper

class BaseBot:
    """RPA基础机器人类"""
    
    def __init__(self, debug=False):
        self.logger = get_logger(__name__)
        self.debug = debug
        self.debug_dir = None
        self.current_step_index = 0  # 添加步骤序号计数器
        
        if self.debug:
            # 创建调试输出目录
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            self.debug_dir = Path("debug") / timestamp
            self.debug_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"调试模式已启用，输出目录: {self.debug_dir}")
        
        # 设置环境变量
        self.env = {
            "ASSETS_DIR": str(Path(__file__).parent.parent / "assets"),
        }
        
        # 检查并初始化设备
        self._init_device()
        
        # 初始化工具类
        self.app_helper = AppHelper(self.device_id)
        self.screenshot_helper = ScreenshotHelper(self.device_id)
        self.ocr_helper = OCRHelper()
        
    def _init_device(self) -> None:
        """初始化并检查Android设备
        
        Raises:
            RuntimeError: 未找到设备或设备未就绪时抛出
        """
        try:
            # 启动ADB服务器
            subprocess.run(['adb', 'start-server'], check=True)
            
            # 获取设备列表
            devices = self._get_connected_devices()
            
            if not devices:
                raise RuntimeError("未找到已连接的Android设备")
                
            if len(devices) > 1:
                self.logger.warning(f"检测到多个设备: {devices}")
                self.logger.warning(f"将使用第一个设备: {devices[0]}")
                
            # 使用第一个设备
            self.device_id = devices[0]
            self.logger.info(f"已连接设备: {self.device_id}")
            
            # 检查设备状态
            self._check_device_status()
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"ADB命令执行失败: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"设备初始化失败: {str(e)}")
            
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
        
        if self.debug:
            # 保存步骤配置
            step_debug_dir = self.debug_dir / f"{step_name}"
            step_debug_dir.mkdir(exist_ok=True)
            
            with open(step_debug_dir / "step_config.yaml", "w", encoding="utf-8") as f:
                yaml.dump(step, f, allow_unicode=True)
        
        # 检查条件
        conditions = step.get('conditions', [])
        if conditions and not self._check_conditions(conditions):
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

    def _check_conditions(self, conditions: List[Dict[str, Any]]) -> bool:
        """检查步骤执行条件"""
        for condition in conditions:
            if condition['type'] == 'step_result':
                step_name = condition['step']
                expected_value = condition['value']
                step_result = self._get_step_result(step_name)
                
                # 如果期望值是字符串，直接查结果中是否包含键
                if isinstance(expected_value, str):
                    if isinstance(step_result, dict):
                        if not step_result.get(expected_value, False):
                            return False
                    else:
                        if step_result != expected_value:
                            return False
                # 否则进行相等性比较
                else:
                    if step_result != expected_value:
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
        # 应用管理相关动作
        if action_type == "check_and_install_app":
            return self.app_helper.check_and_install_app(**params)
        elif action_type == "wait_for_app_installed":
            return self.app_helper.verify_app_installed(**params)
        elif action_type == "start_app":
            return self.app_helper.start_app(**params)
            
        # OCR交互相关动作
        elif action_type in ["wait_and_click_ocr_text", "handle_popups_until_target", 
                            "wait_for_input_ready", "input_text"]:
            if not hasattr(self, 'ocr_interactive_actions'):
                from .actions.ocr_actions import OCRActions
                self.ocr_interactive_actions = OCRActions(self)
                
            if action_type == "wait_and_click_ocr_text":
                return self.ocr_interactive_actions.wait_and_click_ocr_text(params)
            elif action_type == "handle_popups_until_target":
                return self.ocr_interactive_actions.handle_popups_until_target(params)
            elif action_type == "wait_for_input_ready":
                return self.ocr_interactive_actions.wait_for_input_ready(params)
            elif action_type == "input_text":
                return self.ocr_interactive_actions.input_text(params)
        # UI相关动作
        elif action_type == "wait_and_click_region":
            if not hasattr(self, 'wait_click_action'):
                from .actions.ui_actions import WaitAndClickRegionAction
                self.wait_click_action = WaitAndClickRegionAction(self)
            return self.wait_click_action.execute(params)
        elif action_type == "scroll":
            if not hasattr(self, 'scroll_action'):
                from .actions.ui_actions import ScrollAction
                self.scroll_action = ScrollAction(self)
            return self.scroll_action.execute(params)
        
        # OCR识别相关动作
        elif action_type == "get_text_from_region":
            if not hasattr(self, 'get_text_action'):
                from .actions.ocr_actions import GetTextFromRegionAction
                self.get_text_action = GetTextFromRegionAction(self)
            return self.get_text_action.execute(params)
        elif action_type == "check_text_exists":
            if not hasattr(self, 'check_text_action'):
                from .actions.ocr_actions import CheckTextExistsAction
                self.check_text_action = CheckTextExistsAction(self)
            return self.check_text_action.execute(params)
        
        # 数据操作动作
        elif action_type == "append_to_list":
            if not hasattr(self, 'data_actions'):
                from .actions.data_actions import AppendToListAction
                self.data_actions = AppendToListAction(self)
            return self.data_actions.execute(params)
        # 通用工具动作
        elif action_type == "sleep":
            if not hasattr(self, 'utility_actions'):
                from .actions.utility_actions import SleepAction
                self.utility_actions = SleepAction(self)
            return self.utility_actions.execute(params)
        # 流程控制动作
        elif action_type == "loop":
            if not hasattr(self, 'flow_actions'):
                from .actions.flow_actions import LoopAction
                self.flow_actions = LoopAction(self)
            return self.flow_actions.execute(params)
        else:
            raise ValueError(f"未知的动作类型: {action_type}")

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