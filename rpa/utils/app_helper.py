import re
from typing import List
import subprocess
from loguru import logger

class AppHelper:
    def __init__(self, device):
        self.device = device
        self.logger = logger
        
    def check_and_install_app(self, package: str, min_version: str = None, apk_path: str = None) -> bool:
        """
        检查并安装应用
        
        Args:
            package: 应用包名
            min_version: 最低版本要求
            apk_path: APK文件路径
            
        Returns:
            bool: 安装是否成功
        """
        try:
            # 检查应用是否已安装
            app_info = self.device.app_info(package)
            
            if not app_info:
                if not apk_path:
                    raise ValueError(f"应用 {package} 未安装且未提供APK路径")
                    
                self.logger.info(f"正在安装应用: {package}")
                self.device.app_install(apk_path)
                return True
                
            # 检查版本
            if min_version:
                current_version = app_info['versionName']
                if self._compare_versions(current_version, min_version) < 0:
                    if not apk_path:
                        raise ValueError(f"应用版本过低 ({current_version} < {min_version}) 且未提供APK路径")
                        
                    self.logger.info(f"正在更新应用: {package}")
                    self.device.app_install(apk_path)
                    return True
                    
            return True
            
        except Exception as e:
            self.logger.error(f"应用安装检查失败: {str(e)}")
            raise
            
    def check_android_version(self, min_version: str) -> bool:
        """检查Android版本"""
        try:
            device_version = self.device.info['version']
            if self._compare_versions(device_version, min_version) < 0:
                raise ValueError(f"Android版本过低 ({device_version} < {min_version})")
            return True
        except Exception as e:
            self.logger.error(f"Android版本检查失败: {str(e)}")
            raise
            
    def check_and_grant_permissions(self, package: str, permissions: List[str]) -> bool:
        """检查并授予权限"""
        try:
            for permission in permissions:
                # 构建完整权限名
                full_permission = f"android.permission.{permission}"
                
                # 检查权限
                cmd = ['adb', 'shell', 'pm', 'list', 'permissions', '-g', '-f']
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if full_permission not in result.stdout:
                    self.logger.warning(f"权限 {permission} 不存在")
                    continue
                    
                # 授予权限
                self.device.shell(f'pm grant {package} {full_permission}')
                
            return True
            
        except Exception as e:
            self.logger.error(f"权限检查和授予失败: {str(e)}")
            raise
            
    def _compare_versions(self, version1: str, version2: str) -> int:
        """比较版本号"""
        v1_parts = [int(x) for x in re.split(r'[.-]', version1)]
        v2_parts = [int(x) for x in re.split(r'[.-]', version2)]
        
        for i in range(max(len(v1_parts), len(v2_parts))):
            v1 = v1_parts[i] if i < len(v1_parts) else 0
            v2 = v2_parts[i] if i < len(v2_parts) else 0
            
            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
                
        return 0 