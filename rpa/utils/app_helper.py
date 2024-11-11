import subprocess
import re
from typing import List
from loguru import logger
import time
import select

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
        """检查应用版本，如果需要则启动安装过程
        
        Returns:
            bool: 是否需要安装/更新
        """
        try:
            installed_version = self._get_app_version(package)
            
            need_install = False
            if not installed_version:
                need_install = True
            elif min_version and not force_install:
                if self._compare_versions(installed_version, min_version) < 0:
                    need_install = True
            elif force_install:
                need_install = True
                
            if need_install:
                if not apk_path:
                    raise ValueError(f"需要安装应用但未提供APK路径")
                # 只启动安装过程，不等待完成
                self._start_install(apk_path)
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"应用安装检查失败: {str(e)}")
            raise

    def _start_install(self, apk_path: str) -> None:
        """启动APK安装过程，不等待完成"""
        try:
            # 使用 Popen 而不是 run，这样不会等待命令完成
            process = subprocess.Popen(
                ['adb', '-s', self.device_id, 'install', '-r', '-g', apk_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # 行缓冲
            )
            
            # 使用非阻塞方式读取第一行输出
            # 等待最多3秒
            ready = select.select([process.stdout], [], [], 3)[0]
            if ready:
                stdout_line = process.stdout.readline()
                if "Performing Streamed Install" not in stdout_line:
                    raise RuntimeError(f"安装启动失败: {stdout_line}")
            
            self.logger.info("APK安装已启动")
            
        except Exception as e:
            raise RuntimeError(f"启动APK安装失败: {str(e)}")

    def verify_app_installed(self, package: str, timeout: int = 60) -> bool:
        """验证应用是否已成功安装
        
        Args:
            package: 包名
            timeout: 超时时间(秒)
            
        Returns:
            bool: 是否安装成功
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                result = subprocess.run(
                    ['adb', '-s', self.device_id, 'shell', 'pm', 'list', 'packages', package],
                    capture_output=True,
                    text=True,
                    check=True
                )
                if package in result.stdout:
                    return True
            except subprocess.CalledProcessError:
                pass
                
            time.sleep(1)
            
        return False

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