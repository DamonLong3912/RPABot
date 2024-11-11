import os
import logging
from typing import Dict, Any
from pathlib import Path

class BaseBot:
    """RPA基础机器人类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 设置环境变量
        self.env = {
            "ASSETS_DIR": str(Path(__file__).parent.parent / "assets"),
        }
        
    def _resolve_variable(self, value: str) -> str:
        """解析配置中的变量引用
        
        Args:
            value: 包含变量引用的字符串,如 "${ASSETS_DIR}/some_file"
            
        Returns:
            解析后的字符串
        """
        if not isinstance(value, str):
            return value
            
        if "${" not in value:
            return value
            
        # 替换环境变量
        result = value
        for key, val in self.env.items():
            result = result.replace(f"${{{key}}}", val)
            
        return result
        
    def run_flow(self, flow_config: Dict[str, Any]) -> None:
        """执行流程
        
        Args:
            flow_config (Dict[str, Any]): 流程配置字典
            
        Raises:
            ValueError: 配置格式错误时抛出
            RuntimeError: 流程执行出错时抛出
        """
        try:
            # 验证流程配置
            self._validate_flow_config(flow_config)
            
            # 执行流程步骤
            steps = flow_config.get('steps', [])
            for step in steps:
                self._execute_step(step)
                
        except Exception as e:
            self.logger.error(f"流程执行失败: {str(e)}")
            raise RuntimeError(f"流程执行失败: {str(e)}")
            
    def _validate_flow_config(self, config: Dict[str, Any]) -> None:
        """验证流程配置格式
        
        Args:
            config (Dict[str, Any]): 流程配置字典
            
        Raises:
            ValueError: 配置格式错误时抛出
        """
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