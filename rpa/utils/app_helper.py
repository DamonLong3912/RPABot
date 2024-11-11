import subprocess
import re
from typing import List, Dict, Any
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
        
    def check_and_install_app(self, package: str, apk_path: str = None) -> Dict[str, Any]:
        """检查应用是否已安装，如果未安装则启动安装过程
        
        Returns:
            Dict[str, Any]: {
                'installed': bool,  # 是否已安装
                'need_install': bool,  # 是否需要安装
            }
        """
        try:
            # 检查应用是否已安装
            result = subprocess.run(
                ['adb', '-s', self.device_id, 'shell', 'pm', 'list', 'packages', package],
                capture_output=True,
                text=True,
                check=True
            )
            
            is_installed = package in result.stdout
            
            result = {
                'installed': is_installed,
                'need_install': not is_installed
            }
            
            # 打印检查结果
            self.logger.info(f"应用 {package} 检查结果:")
            self.logger.info(f"  - 已安装: {is_installed}")
            
            # 如果需要安装但没有提供APK路径
            if result['need_install'] and not apk_path:
                raise ValueError(f"需要安装应用但未提供APK路径")
                
            # 如果需要安装则启动安装过程
            if result['need_install']:
                self._start_install(apk_path)
                
            return result
            
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
        self.logger.info(f"开始验证应用 {package} 是否安装...")
        
        while time.time() - start_time < timeout:
            try:
                result = subprocess.run(
                    ['adb', '-s', self.device_id, 'shell', 'pm', 'list', 'packages', package],
                    capture_output=True,
                    text=True,
                    check=True
                )
                if package in result.stdout:
                    self.logger.info(f"应用 {package} 已成功安装")
                    return True
            except subprocess.CalledProcessError as e:
                self.logger.warning(f"检查安装状态时出错: {str(e)}")
                
            self.logger.debug(f"应用 {package} 尚未安装完成，等待1秒后重试...")
            time.sleep(1)
            
        self.logger.error(f"验证应用安装超时({timeout}秒)")
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

    def start_app(self, package: str, max_retries: int = 5, retry_interval: int = 2) -> bool:
        """启动应用
        
        Args:
            package: 包名
            max_retries: 最大重试次数
            retry_interval: 重试间隔(秒)
            
        Returns:
            bool: 是否成功启动
        """
        try:
            self.logger.info(f"尝试启动应用 {package}")
            
            # 先检查应用是否已安装
            check_result = subprocess.run(
                ['adb', '-s', self.device_id, 'shell', 'pm', 'list', 'packages', package],
                capture_output=True,
                text=True,
                check=True
            )
            
            if package not in check_result.stdout:
                self.logger.error(f"应用 {package} 未安装，无法启动")
                return False
            
            for attempt in range(max_retries):
                self.logger.info(f"第 {attempt + 1}/{max_retries} 次尝试启动应用")
                
                start_cmd = [
                    'adb', '-s', self.device_id, 'shell',
                    'am', 'start',
                    '-W',  # 等待启动完成
                    '-n', f"{package}/.page.launch.LocalLauncherActivity"
                ]
                
                self.logger.debug(f"执行启动命令: {' '.join(start_cmd)}")
                result = subprocess.run(
                    start_cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # 检查启动结果
                self.logger.debug(f"启动输出: {result.stdout}")
                
                if "Status: ok" in result.stdout and "LaunchState: COLD" in result.stdout:
                    self.logger.info(f"应用 {package} 启动成功")
                    time.sleep(2)  # 等待应用完全启动
                    return True
                else:
                    if attempt < max_retries - 1:
                        self.logger.warning(f"启动未成功，{retry_interval}秒后重试...")
                        # 在重试前先尝试关闭应用
                        try:
                            subprocess.run(
                                ['adb', '-s', self.device_id, 'shell', 'am', 'force-stop', package],
                                check=True,
                                capture_output=True
                            )
                            self.logger.debug("已强制停止应用")
                        except subprocess.CalledProcessError as e:
                            self.logger.warning(f"强制停止应用失败: {str(e)}")
                        
                        time.sleep(retry_interval)
                    else:
                        self.logger.error("达到最大重试次数，启动失败")
                        return False
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"启动应用失败: {str(e)}")
            self.logger.error(f"错误输出: {e.stderr}")
            
            # 尝试使用 monkey 命令作为备选方案
            try:
                self.logger.info("尝试使用 monkey 命令启动应用...")
                monkey_cmd = [
                    'adb', '-s', self.device_id, 'shell',
                    'monkey',
                    '-p', package,
                    '-c', 'android.intent.category.LAUNCHER',
                    '1'
                ]
                self.logger.debug(f"执行 monkey 命令: {' '.join(monkey_cmd)}")
                
                result = subprocess.run(
                    monkey_cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                self.logger.debug(f"Monkey 命令输出: {result.stdout}")
                
                time.sleep(3)  # 等待启动
                return True
            except subprocess.CalledProcessError as e2:
                self.logger.error(f"使用 monkey 命令启动也失败: {str(e2)}")
                self.logger.error(f"Monkey 错误输出: {e2.stderr}")
                return False