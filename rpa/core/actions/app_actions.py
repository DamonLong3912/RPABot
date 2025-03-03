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
            
            self.bot.ui_animator.app_start(package)
            

                    
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

class TaobaoSearchAction(BaseAction):
    """淘宝搜索框操作动作"""
    
    def execute(self, params: Dict[str, Any]) -> None:
        time.sleep(2)
        search_text = params.get('search_text')
        
        if not search_text:
            raise ValueError("必须提供search_text参数")

        
        self.back_until()
        
        try:
            logger.info(f"等待搜索框出现...")
            if self.ui_animator(className="android.view.View", description="搜索栏").wait(timeout=10):
                self.ui_animator(className="android.view.View", description="搜索栏").click()
                
                # 输入搜索内容
                if self.ui_animator(className="android.widget.EditText", resourceId="com.taobao.taobao:id/searchEdit").wait(timeout=5):
                    self.ui_animator(className="android.widget.EditText", resourceId="com.taobao.taobao:id/searchEdit").click()
                    self.ui_animator(className="android.widget.EditText", resourceId="com.taobao.taobao:id/searchEdit").send_keys(search_text)
                # 点击搜索按钮
                if self.ui_animator(text="搜索").wait(timeout=5):
                    self.ui_animator(text="搜索").click()
                else:
                    raise ValueError("搜索按钮未在规定时间内出现")
                

                if self.ui_animator(text="立即购买").wait(timeout=5):
                    pass
                else:
                    raise ValueError("立即购买未在规定时间内出现")
    

            else:
                logger.error("搜索框未在规定时间内出现")
                raise ValueError("搜索框未在规定时间内出现")
        
        except subprocess.CalledProcessError as e:
            logger.error(f"搜索操作失败: {str(e)}")
        except Exception as e:
            logger.error(f"搜索操作失败: {str(e)}")
            raise
        
    def back_until(self, interval=1, max_times=10):
        """返回首页"""
        d = self.ui_animator
        current = 1
        while True:
            if not self.ui_animator(className="android.view.View", description='搜索栏'):
                if self.ui_animator(className="android.view.View", resourceId="com.taobao.taobao:id/poplayer_native_state_id"):
                    self.ui_animator(className="android.view.View", resourceId="com.taobao.taobao:id/poplayer_native_state_id").click()
                # logger.info("press back")
                d.press("back")
                time.sleep(interval)
                current += 1
                if current > max_times:
                    logger.info("reach max times")
                    break
            else:
                break


class TaobaoPayListAction(BaseAction):
    """淘宝选购商品支付操作动作"""
    
    def execute(self, params: Dict[str, Any]) -> None:
        pay_status = params.get('pay_status')
        pay_list = params.get('pay_list')
        #pay_list的格式为："中杯:原味蒸汽奶,大杯:原味蒸汽奶" 循环用:分割
        pay_list = pay_list.split(',')
        for item in pay_list:
            self.back_until()
            self.ui_animator(className="android.widget.TextView", text='立即购买').click()
            pay_list2 = item.split(':')
            if '星巴克' in pay_status:
                self.ui_animator(text=pay_list2[0]).click()
                self.ui_animator(text=pay_list2[1]).click()
                self.ui_animator(className="android.widget.LinearLayout", description="确认").click()
                if self.ui_animator(className="android.view.View", description="提交订单").wait(timeout=5):
                    self.ui_animator(className="android.view.View", description="提交订单").click()
                    if not self.ui_animator(resourceId="com.taobao.taobao:id/render_container").wait(timeout=10):
                        raise ValueError("疑似未支付成功")

                else:
                   raise ValueError("确认订单页面未能成功点击提交订单按钮")
                
    def back_until(self, interval=1, max_times=10):
        """商品主页"""
        d = self.ui_animator
        current = 1
        while True:
            if not self.ui_animator(className="android.widget.TextView", text='立即购买'):
                d.press("back")
                time.sleep(interval)
                current += 1
                if current > max_times:
                    logger.info("reach max times")
                    break
            else:
                break










class ReturnToHomeAction(BaseAction):
    """返回应用首页动作"""
    
    def execute(self, params: Dict[str, Any]) -> None:
        home_indicator = params.get('home_indicator')  # 用于判断是否在首页的标识
        
        if not home_indicator:
            raise ValueError("必须提供home_indicator参数")
        
        self.back_until(lambda: self.ui_animator(className="android.view.View", description=home_indicator))

    def back_until(self, func, interval=1, max_times=10):
        d = self.ui_animator
        current = 1
        while True:
            if not func():
                logger.info("press back")
                d.press("back")
                time.sleep(interval)
                current += 1
                if current > max_times:
                    logger.info("reach max times")
                    break
            else:
                break