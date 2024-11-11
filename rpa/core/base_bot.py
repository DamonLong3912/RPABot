import os
import logging
import subprocess
from typing import Dict, Any, List
from pathlib import Path
from ..utils.app_helper import AppHelper  # 导入AppHelper类

class BaseBot:
    """RPA基础机器人类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 设置环境变量
        self.env = {
            "ASSETS_DIR": str(Path(__file__).parent.parent / "assets"),
        }
        
        # 检查并初始化设备
        self._init_device()
        
        # 初始化工具类
        self.app_helper = AppHelper(self.device_id)  # 初始化AppHelper
        
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
        
        # 解析prerequisites中的变量
        if hasattr(self, 'current_flow_config'):
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
            # 保存当前流程配置以供变量解析使用
            self.current_flow_config = flow_config
            
            # 验证流程配置
            self._validate_flow_config(flow_config)
            
            # 执行流程步骤
            steps = flow_config.get('steps', [])
            for step in steps:
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
        
        self.logger.info(f"执行步骤: {step_name} (动作: {step_type})")
        
        # 解析参数中的变量
        params = step.get('params', {})
        resolved_params = {}
        for key, value in params.items():
            resolved_params[key] = self._resolve_variable(value)
            
        # 根据动作类型调用相应的处理函数
        if step_type == 'check_and_install_app':
            self.app_helper.check_and_install_app(**resolved_params)
        elif step_type == 'check_android_version':
            self.app_helper.check_android_version(**resolved_params)
        elif step_type == 'grant_permissions':
            self.app_helper.check_and_grant_permissions(**resolved_params)
        else:
            raise ValueError(f"未知的动作类型: {step_type}")