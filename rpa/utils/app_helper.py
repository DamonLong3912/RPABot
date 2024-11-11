import subprocess
import re
from typing import List
from loguru import logger

class AppHelper:
    def __init__(self, device_id: str):
        """初始化应用管理助手
        
        Args:
            device_id: 设备ID
        """
        self.device_id = device_id
        self.logger = logger
        
    def check_and_install_app(self, package: str, min_version: str = None, 
                             apk_path: str = None, force_install: bool = False) -> bool:
        """检查并安装应用
        
        Args:
            package: 应用包名
            min_version: 最低版本要求
            apk_path: APK文件路径
            force_install: 是否强制重新安装
            
        Returns:
            bool: 安装是否成功
        """
        try:
            # 检查应用是否已安装
            installed_version = self._get_app_version(package)
            
            if not installed_version:
                if not apk_path:
                    raise ValueError(f"应用 {package} 未安装且未提供APK路径")
                    
                self.logger.info(f"正在安装应用: {package}")
                self._install_apk(apk_path)
                return True
                
            # 检查版本
            if min_version and not force_install:
                if self._compare_versions(installed_version, min_version) < 0:
                    if not apk_path:
                        raise ValueError(f"应用版本过低 ({installed_version} < {min_version}) 且未提供APK路径")
                        
                    self.logger.info(f"正在更新应用: {package}")
                    self._install_apk(apk_path)
                    return True
                    
            elif force_install and apk_path:
                self.logger.info(f"强制重新安装应用: {package}")
                self._install_apk(apk_path)
                return True
                
            return True
            
        except Exception as e:
            self.logger.error(f"应用安装检查失败: {str(e)}")
            raise
            
    def _get_app_version(self, package: str) -> str:
        """获取应用版本号"""
        try:
            result = subprocess.run(
                ['adb', '-s', self.device_id, 'shell', 'dumpsys', 'package', package],
                capture_output=True,
                text=True,
                check=True
            )
            
            # 解析版本号
            match = re.search(r'versionName=([0-9.]+)', result.stdout)
            return match.group(1) if match else None
            
        except subprocess.CalledProcessError:
            return None
            
    def _install_apk(self, apk_path: str) -> None:
        """安装APK文件"""
        try:
            subprocess.run(
                ['adb', '-s', self.device_id, 'install', '-r', apk_path],
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"APK安装失败: {str(e)}")
            
    def _compare_versions(self, version1: str, version2: str) -> int:
        """比较版本号"""
        v1_parts = [int(x) for x in version1.split('.')]
        v2_parts = [int(x) for x in version2.split('.')]
        
        for i in range(max(len(v1_parts), len(v2_parts))):
            v1 = v1_parts[i] if i < len(v1_parts) else 0
            v2 = v2_parts[i] if i < len(v2_parts) else 0
            
            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
                
        return 0 