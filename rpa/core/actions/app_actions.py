from typing import Dict, Any
from loguru import logger
import subprocess
import time
import select
from .base_action import BaseAction

class CheckAndInstallAppAction(BaseAction):
    """检查并安装应用动作"""
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        package = params.get('package')
        apk_path = params.get('apk_path')
        
        if not package:
            raise ValueError("必须提供package参数")
            
        try:
            # 检查应用是否已安装
            result = subprocess.run(
                ['adb', '-s', self.device_id, 'shell', 'pm', 'list', 'packages', package],
                capture_output=True,
                text=True,
                check=True
            )
            
            is_installed = package in result.stdout
            
            check_result = {
                'installed': is_installed,
                'need_install': not is_installed
            }
            
            logger.info(f"应用 {package} 检查结果:")
            logger.info(f"  - 已安装: {is_installed}")
            
            if check_result['need_install'] and not apk_path:
                raise ValueError(f"需要安装应用但未提供APK路径")
                
            if check_result['need_install']:
                self._start_install(apk_path)
                
            return check_result
            
        except Exception as e:
            logger.error(f"应用安装检查失败: {str(e)}")
            raise

    def _start_install(self, apk_path: str) -> None:
        try:
            process = subprocess.Popen(
                ['adb', '-s', self.device_id, 'install', '-r', '-g', apk_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            ready = select.select([process.stdout], [], [], 3)[0]
            if ready:
                stdout_line = process.stdout.readline()
                if "Performing Streamed Install" not in stdout_line:
                    raise RuntimeError(f"安装启动失败: {stdout_line}")
            
            logger.info("APK安装已启动")
            
        except Exception as e:
            raise RuntimeError(f"启动APK安装失败: {str(e)}")

class VerifyAppInstalledAction(BaseAction):
    """验证应用是否已安装动作"""
    
    def execute(self, params: Dict[str, Any]) -> bool:
        package = params.get('package')
        timeout = params.get('timeout', 60)
        
        if not package:
            raise ValueError("必须提供package参数")
            
        start_time = time.time()
        logger.info(f"开始验证应用 {package} 是否安装...")
        
        while time.time() - start_time < timeout:
            try:
                result = subprocess.run(
                    ['adb', '-s', self.device_id, 'shell', 'pm', 'list', 'packages', package],
                    capture_output=True,
                    text=True,
                    check=True
                )
                if package in result.stdout:
                    logger.info(f"应用 {package} 已成功安装")
                    return True
            except subprocess.CalledProcessError as e:
                logger.warning(f"检查安装状态时出错: {str(e)}")
                
            logger.debug(f"应用 {package} 尚未安装完成，等待1秒后重试...")
            time.sleep(1)
            
        logger.error(f"验证应用安装超时({timeout}秒)")
        return False

class StartAppAction(BaseAction):
    """启动应用动作"""
    
    def execute(self, params: Dict[str, Any]) -> bool:
        package = params.get('package')
        max_retries = params.get('max_retries', 5)
        retry_interval = params.get('retry_interval', 2)
        
        if not package:
            raise ValueError("必须提供package参数")
            
        try:
            logger.info(f"尝试启动应用 {package}")
            
            # 先检查应用是否已安装
            check_result = subprocess.run(
                ['adb', '-s', self.device_id, 'shell', 'pm', 'list', 'packages', package],
                capture_output=True,
                text=True,
                check=True
            )
            
            if package not in check_result.stdout:
                logger.error(f"应用 {package} 未安装，无法启动")
                return False
            
            for attempt in range(max_retries):
                logger.info(f"第 {attempt + 1}/{max_retries} 次尝试启动应用")
                
                start_cmd = [
                    'adb', '-s', self.device_id, 'shell',
                    'am', 'start',
                    '-W',  # 等待启动完成
                    '-n', f"{package}/.page.launch.LocalLauncherActivity"
                ]
                
                logger.debug(f"执行启动命令: {' '.join(start_cmd)}")
                result = subprocess.run(
                    start_cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                if "Status: ok" in result.stdout and "LaunchState: COLD" in result.stdout:
                    logger.info(f"应用 {package} 启动成功")
                    time.sleep(2)
                    return True
                    
                if attempt < max_retries - 1:
                    logger.warning(f"启动未成功，{retry_interval}秒后重试...")
                    try:
                        subprocess.run(
                            ['adb', '-s', self.device_id, 'shell', 'am', 'force-stop', package],
                            check=True,
                            capture_output=True
                        )
                        logger.debug("已强制停止应用")
                    except subprocess.CalledProcessError as e:
                        logger.warning(f"强制停止应用失败: {str(e)}")
                    
                    time.sleep(retry_interval)
                else:
                    logger.error("达到最大重试次数，启动失败")
                    return False
                    
        except subprocess.CalledProcessError as e:
            logger.error(f"启动应用失败: {str(e)}")
            logger.error(f"错误输出: {e.stderr}")
            return self._try_monkey_start(package)

    def _try_monkey_start(self, package: str) -> bool:
        """使用 monkey 命令尝试启动应用"""
        try:
            logger.info("尝试使用 monkey 命令启动应用...")
            monkey_cmd = [
                'adb', '-s', self.device_id, 'shell',
                'monkey',
                '-p', package,
                '-c', 'android.intent.category.LAUNCHER',
                '1'
            ]
            logger.debug(f"执行 monkey 命令: {' '.join(monkey_cmd)}")
            
            result = subprocess.run(
                monkey_cmd,
                capture_output=True,
                text=True,
                check=True
            )
            logger.debug(f"Monkey 命令输出: {result.stdout}")
            
            time.sleep(3)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"使用 monkey 命令启动也失败: {str(e)}")
            logger.error(f"Monkey 错误输出: {e.stderr}")
            return False 

class WaitForAppInstalledAction(BaseAction):
    """等待应用安装完成动作"""
    
    def execute(self, params: Dict[str, Any]) -> bool:
        package = params.get('package')
        timeout = params.get('timeout', 60)
        check_interval = params.get('check_interval', 1)
        
        if not package:
            raise ValueError("必须提供package参数")
            
        start_time = time.time()
        logger.info(f"等待应用 {package} 安装完成...")
        
        while time.time() - start_time < timeout:
            try:
                result = subprocess.run(
                    ['adb', '-s', self.device_id, 'shell', 'pm', 'list', 'packages', package],
                    capture_output=True,
                    text=True,
                    check=True
                )
                if package in result.stdout:
                    logger.info(f"应用 {package} 已安装完成")
                    return True
            except subprocess.CalledProcessError as e:
                logger.warning(f"检查安装状态时出错: {str(e)}")
                
            logger.debug(f"应用 {package} 尚未安装完成，{check_interval}秒后重试...")
            time.sleep(check_interval)
            
        logger.error(f"等待应用安装超时({timeout}秒)")
        return False 