#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import yaml
import os
from pathlib import Path
from rpa.core.base_bot import BaseBot
from rpa.utils.logger import setup_logger, get_logger
import subprocess
import uiautomator2 as u2
import time

def parse_args():
    parser = argparse.ArgumentParser(description='RPA Framework 运行器')
    parser.add_argument('--flow', '-f', required=True, help='流程配置文件路径')
    parser.add_argument('--config', default='config.yaml', help='全局配置文件路径')
    parser.add_argument('--debug', '-d', action='store_true', help='启用调试模式')
    parser.add_argument('--dev', action='store_true', help='开发环境模式')
    parser.add_argument('--log', '-l', default='run.log', help='日志文件路径')
    parser.add_argument('--init-device', action='store_true', help='初始化设备UIAutomator2环境')
    return parser.parse_args()

def setup_uiautomator2(device_id: str = None) -> bool:
    """安装和初始化UIAutomator2
    
    Args:
        device_id: 设备ID，如果为None则直接失败
        
    Returns:
        bool: 初始化是否成功
    """
    logger = get_logger(__name__)
    try:
        # 设置 adb 路径
        platform_tools_path = Path(__file__).parent / 'tools' / 'platform-tools'
        adb_path = platform_tools_path / 'adb.exe'
        
        if not adb_path.exists():
            logger.error(f"ADB工具不存在: {adb_path}")
            return False
            
        # 将 platform-tools 添加到环境变量
        os.environ['PATH'] = f"{platform_tools_path};{os.environ['PATH']}"
        
        # 检查设备连接
        if device_id:
            devices = [device_id]
        else:
            # 获取所有已连接设备
            result = subprocess.run(['adb', 'devices'], 
                                 capture_output=True, 
                                 text=True,
                                 check=True)
            devices = []
            for line in result.stdout.split('\n')[1:]:
                if line.strip() and '\tdevice' in line:
                    devices.append(line.split('\t')[0])

        if not devices:
            logger.error("未找到已连接的设备")
            return False

        for device in devices:
            logger.info(f"正在初始化设备 {device}")
            
            # 使用 u2.connect()
            d = u2.connect(device)
            try:
                if not d.service("uiautomator").running():
                    # 安装UIAutomator2
                    logger.info("正在安装UIAutomator2服务...")
                    d.service("uiautomator").start()
                    # 等待服务启动
                    time.sleep(2)
                    
                # 安装ATX应用
                logger.info("正在安装ATX代理应用...")
                d.app_install("https://github.com/openatx/android-uiautomator-server/releases/latest/download/app-uiautomator.apk")
                
                # 启动UIAutomator2服务
                logger.info("正在启动UIAutomator2服务...")
                d.service("uiautomator").start()
                
                # 等待服务就绪
                for _ in range(10):
                    if d.service("uiautomator").running():
                        logger.info(f"设备 {device} UIAutomator2服务已就绪")
                        break
                    time.sleep(1)
                else:
                    raise RuntimeError("UIAutomator2服务启动超时")
                
            except Exception as e:
                logger.error(f"初始化设备 {device} 失败: {str(e)}")
                return False

        return True
        
    except Exception as e:
        logger.error(f"设置UIAutomator2失败: {str(e)}")
        return False

def setup_dev_env():
    """配置开发环境"""
    # 设置项目根目录
    project_root = Path(__file__).parent.absolute()
    os.environ['RPA_PROJECT_ROOT'] = str(project_root)
    
    # 设置资源目录
    os.environ['RPA_ASSETS_DIR'] = str(project_root / 'rpa' / 'assets')
    
    # 设置日志目录
    os.environ['RPA_LOG_DIR'] = str(project_root / 'logs')
    
    # 设置日志级别为DEBUG
    os.environ['RPA_LOG_LEVEL'] = 'DEBUG'
    
    # 打印环境信息
    logger = get_logger(__name__)
    logger.info("开发环境配置:")
    logger.info(f"项目根目录: {os.environ['RPA_PROJECT_ROOT']}")
    logger.info(f"资源目录: {os.environ['RPA_ASSETS_DIR']}")
    logger.info(f"日志目录: {os.environ['RPA_LOG_DIR']}")
    logger.info(f"日志级别: {os.environ['RPA_LOG_LEVEL']}")

def clean_temp_directories():
    """清理临时目录"""
    dirs_to_clean = ['logs', 'temp']
    project_root = Path(__file__).parent.absolute()
    
    logger = get_logger(__name__)
    for dir_name in dirs_to_clean:
        dir_path = project_root / dir_name
        if dir_path.exists():
            try:
                for item in dir_path.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        import shutil
                        shutil.rmtree(item)
                logger.info(f"已清理目录: {dir_name}")
            except Exception as e:
                logger.warning(f"清理目录 {dir_name} 时出错: {str(e)}")

def main(flow_config_path: str):
    # 加载流程配置
    with open(flow_config_path, 'r', encoding='utf-8') as f:
        flow_config = yaml.safe_load(f)
    
    # 创建机器人实例，传入流程配置
    bot = BaseBot(flow_config)
    
        
    # 执行流程
    bot.run_flow(flow_config)

def run():
    args = parse_args()
    
    # 清理临时目录
    clean_temp_directories()
    
    # 确保日志文件名有效
    if not args.log:
        args.log = 'run.log'
    
    # 设置日志
    log_level = "DEBUG" if args.debug or args.dev else "INFO"
    setup_logger(args.log, log_level)
    logger = get_logger(__name__)
    
    # 开发环境配置
    if args.dev:
        setup_dev_env()
        logger.info("运行在开发环境模式")
    
    try:
        # 读取流程配置文件
        flow_path = Path(args.flow)
        if not flow_path.is_absolute():
            flow_path = Path(os.environ.get('RPA_PROJECT_ROOT', '')) / flow_path
            
        logger.info(f"加载流程配置文件: {flow_path}")
        with open(flow_path, 'r', encoding='utf-8') as f:
            flow_config = yaml.safe_load(f)
            
        # 打印流程信息
        logger.info(f"流程名称: {flow_config.get('name')}")
        logger.info(f"流程版本: {flow_config.get('version')}")
        logger.info(f"流程描述: {flow_config.get('description')}")
        

        logger.info("开始初始化设备UIAutomator2环境...")
        # 从flow配置中获取设备信息
        device_config = flow_config.get('device', {})
        device_id = device_config.get('ip') or device_config.get('serial')
        
        if not device_id:
            logger.error("未指定设备IP或序列号")
            return
        
        if not setup_uiautomator2(device_id):
            logger.error("设备初始化失败")
            return
        logger.info("设备初始化完成")
        if not args.flow:
            return
        
        # 执行流程
        logger.info(f"开始执行流程: {flow_config.get('name', '未命名流程')}")
        main(flow_path)
        logger.info("流程执行完成")
        
    except Exception as e:
        logger.error(f"执行出错: {str(e)}")
        if args.dev:
            import traceback
            logger.error(traceback.format_exc())
        raise

if __name__ == '__main__':
    run() 