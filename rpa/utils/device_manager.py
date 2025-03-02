import threading
from typing import Dict, Optional, Tuple, List
import json
from pathlib import Path
import os
from rpa.utils.logger import get_logger
import uiautomator2 as u2
import time
import glob  # 新增导入
import yaml  # 新增导入
from queue import Queue
from collections import defaultdict
from threading import Event
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Manager

# 定义设备状态
class DeviceStatus:
    UNAVAILABLE = 0  # 不可用
    AVAILABLE = 1    # 可用
    BUSY = 2         # 非空闲
    ALLOCATING = 3  # 新增：正在分配中

class DeviceManager:
    _instance = None
    _lock = threading.Lock()  # 单例锁
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DeviceManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.logger = get_logger(__name__)
        
        # 使用Manager创建线程安全的字典
        manager = Manager()
        self._devices = manager.dict()  # 线程安全的设备状态字典
        self._error_task_devices = manager.dict()  # 线程安全的异常设备字典
        
        self._initialized = True
        
        # 启动监控线程
        self._heartbeat_thread = threading.Thread(target=self._check_devices_health, daemon=True)
        self._heartbeat_thread.start()
        
        self._cleanup_thread = threading.Thread(target=self._cleanup_devices, daemon=True)
        self._cleanup_thread.start()
        
        self._error_task_cleanup_thread = threading.Thread(target=self._cleanup_error_tasks, daemon=True)
        self._error_task_cleanup_thread.start()
        
    def _check_device_connection(self, device_ip: str) -> bool:
        """检查设备连接状态
        
        Args:
            device_ip: 设备IP
            
        Returns:
            bool: 设备是否在线
        """
        try:
            d = u2.connect(device_ip)
            # 尝试获取设备信息来验证连接
            d.info
            return True
        except Exception as e:
            # self.logger.warning(f"设备 {device_ip} 连接检查失败: {str(e)}")
            return False
            
    def _check_devices_health(self):
        """设备健康检查循环"""
        while True:
            time.sleep(10)  # 每10秒检查一次，减少频率
            current_time = time.time()
            for device_ip, (status, last_heartbeat) in list(self._devices.items()):
                # 跳过正在分配中的设备
                if status == DeviceStatus.ALLOCATING:
                    continue
                # 只检查空闲和不可用的设备
                if status == DeviceStatus.AVAILABLE or status == DeviceStatus.UNAVAILABLE:
                    if not self._check_device_connection(device_ip):
                        self._devices[device_ip] = (DeviceStatus.UNAVAILABLE, current_time)
                    else:
                        self._devices[device_ip] = (DeviceStatus.AVAILABLE, current_time)
    
    def _cleanup_devices(self):
        """定期调整 YAML 文件和device中的设备"""
        while True:
            time.sleep(600)  # 每600秒检查一次
            current_devices = self._devices.keys()
            valid_devices = []  # 确保使用集合来存储设备 IP

            # 检查 flows 和 tests 目录下的 YAML 文件
            for path in glob.glob('flows/*.yaml') + glob.glob('tests/flows/*.yaml'):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        flow_config = yaml.safe_load(f)
                        device_config = flow_config.get('device', {})
                        device_ids = device_config.get('ip', [])
                        device_ids = [ip.strip() for ip in device_ids.split(',') if ip.strip()]
                        for device_ip in device_ids:
                            valid_devices.append(device_ip)  # 使用 append 方法添加设备 IP
                except Exception as e:
                    self.logger.error(f"加载流程配置失败: {str(e)}")

            # 移除不在有效设备列表中的设备
            for device_ip in current_devices:
                if device_ip not in valid_devices:
                    del self._devices[device_ip]
                    self.logger.info(f"设备 {device_ip} 已从设备池中移除，因不在有效的 YAML 文件中")

            # 添加 YAML 文件中存在但不在设备管理器中的设备
            for device_ip in valid_devices:
                if device_ip not in current_devices:
                    self._devices[device_ip] = (DeviceStatus.UNAVAILABLE, time.time())  # 状态为不可用
                    self.logger.info(f"设备 {device_ip} 已添加到设备池，状态为不可用")
    
    def register_devices(self, device_ips: str):
        """注册设备到设备池"""
        devices = [ip.strip() for ip in device_ips.split(',') if ip.strip()]
        current_time = time.time()
        for device in devices:
            if device not in self._devices:
                self._devices[device] = (DeviceStatus.UNAVAILABLE, current_time)
                self.logger.info(f"设备 {device} 已添加到设备池")
    
    def get_available_device(self, device_ips: str):
        """获取指定设备列表中的一个空闲设备
        
        Args:
            device_ids: 设备ID列表
            
        Returns:
            Optional[str]: 可用设备的IP地址，如果没有可用设备则返回None
        """
        device_ids = [ip.strip() for ip in device_ips.split(',') if ip.strip()]
        current_time = time.time()
        
        for device_ip in device_ids:
            if device_ip in self._devices:
                status, last_heartbeat = self._devices[device_ip]
                if status == DeviceStatus.AVAILABLE:
                    # 先标记为分配中
                    self._devices[device_ip] = (DeviceStatus.ALLOCATING, current_time)
                    # 再次检查连接状态
                    if self._check_device_connection(device_ip):
                        self._devices[device_ip] = (DeviceStatus.BUSY, current_time)
                        self.logger.info(f"设备 {device_ip} 已分配")
                        return device_ip
                    else:
                        # 如果连接失败，恢复为不可用状态
                        self._devices[device_ip] = (DeviceStatus.UNAVAILABLE, current_time)

        # 如果没有可用设备，尝试连接设备
        for device_ip in device_ids:
            if device_ip not in self._devices:
                self._devices[device_ip] = (DeviceStatus.UNAVAILABLE, current_time)
            
            status = self._devices[device_ip][0]
            if status != DeviceStatus.BUSY and status != DeviceStatus.ALLOCATING:
                # 先标记为分配中
                self._devices[device_ip] = (DeviceStatus.ALLOCATING, current_time)
                if self._check_device_connection(device_ip):
                    self._devices[device_ip] = (DeviceStatus.BUSY, current_time)
                    self.logger.info(f"设备 {device_ip} 连接成功，状态已更新为可用")
                    return device_ip
                else:
                    self._devices[device_ip] = (DeviceStatus.UNAVAILABLE, current_time)
        return None
    
    def release_device(self, device_ip: str):
        """释放设备"""
        if device_ip in self._devices:
            if self._check_device_connection(device_ip):
                self._devices[device_ip] = (DeviceStatus.AVAILABLE, time.time())
            self.logger.info(f"设备 {device_ip} 已释放")
    
    def get_all_devices(self) -> Dict[str, Dict[str, any]]:
        """获取所有设备状态"""
        current_time = time.time()
        return {
            ip: {
                "status": "unavailable" if status == DeviceStatus.UNAVAILABLE else "available" if status == DeviceStatus.AVAILABLE else "busy",
                "connected": self._check_device_connection(ip),
                "last_heartbeat": int(current_time - last_heartbeat)
            }
            for ip, (status, last_heartbeat) in self._devices.items()
        }            
            
    def add_error_task_device(self, device_ip: str):
        """添加异常任务的设备"""
        self._error_task_devices[device_ip] = time.time()
        self.logger.info(f"设备 {device_ip} 因任务异常被加入监控")

    def _cleanup_error_tasks(self):
        """定期检查并清理异常任务的设备"""
        while True:
            time.sleep(60)  # 每分钟检查一次
            current_time = time.time()
            
            for device_ip in list(self._error_task_devices.keys()):
                last_error_time = self._error_task_devices.get(device_ip, 0)
                if current_time - last_error_time > 600:  # 10分钟 = 600秒
                    if device_ip in self._error_task_devices:
                        del self._error_task_devices[device_ip]
                    with self._devices:
                        self.release_device(device_ip)
                    self.logger.info(f"设备 {device_ip} 因异常状态超过10分钟未处理而被释放")
            