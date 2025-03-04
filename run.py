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
from rpa.utils.device_manager import DeviceManager
from typing import Dict, Any
import threading
from rpa.utils.db import DatabaseManager

def parse_args():
    parser = argparse.ArgumentParser(description='RPA Framework 运行器')
    parser.add_argument('--flow', '-f', help='流程配置文件路径')
    parser.add_argument('--config', default='config.yaml', help='全局配置文件路径')
    parser.add_argument('--debug', '-d', action='store_true', help='启用调试模式')
    parser.add_argument('--dev', action='store_true', help='开发环境模式')
    parser.add_argument('--log', '-l', default='run.log', help='日志文件路径')
    parser.add_argument('--api', action='store_true', help='启动API服务')
    parser.add_argument('--host', default='0.0.0.0', help='API服务监听地址')
    parser.add_argument('--port', type=int, default=5000, help='API服务端口')
    parser.add_argument('--init-device', action='store_true', help='初始化设备UIAutomator2环境')
    parser.add_argument('--start-step-index', type=int, help='开始步骤索引')
    return parser.parse_args()

def setup_uiautomator2(device_ip: str) -> bool:
    """安装和初始化UIAutomator2

    Args:
        device_ip: 设备IP

    Returns:
        bool: 初始化是否成功
    """
    logger = get_logger(__name__)
    try:
        # 设置 adb 路径
        platform_tools_path = Path(__file__).parent / 'tools' / 'platform-tools'
        adb_path = platform_tools_path / 'adb'

        if not adb_path.exists():
            logger.error(f"ADB工具不存在: {adb_path}")
            return False

        # 将 platform-tools 添加到环境变量
        os.environ['PATH'] = f"{platform_tools_path};{os.environ['PATH']}"

        logger.info(f"正在初始化设备 {device_ip}")

        # 使用 u2.connect()
        d = u2.connect(device_ip)
        try:
            # 检查ATX应用是否已安装
            atx_package = "com.github.uiautomator"
            app_info = d.app_info(atx_package)

            if not app_info:
                # 安装ATX应用
                logger.info("正在安装ATX代理应用...")
                d.app_install("https://github.com/openatx/android-uiautomator-server/releases/latest/download/app-uiautomator.apk")
            else:
                logger.info("ATX代理应用已安装，版本：" + str(app_info.get('versionName', 'unknown')))

            return True

        except Exception as e:
            logger.error(f"初始化设备 {device_ip} 失败: {str(e)}")
            return False

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

def load_config(config_path: str) -> Dict[str, Any]:
    """加载配置文件"""
    logger = get_logger(__name__)
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"加载配置文件失败: {str(e)}")
        return {}

def main(flow_config: Dict[str, Any], device_ip: str, start_step_index: int = 0,task_id=None):
    logger = get_logger(__name__)

    try:

        # 直接使用传入的设备IP创建机器人实例
        bot = BaseBot(flow_config, device_ip,task_id)

        # 执行流程
        bot.run_flow(flow_config, start_step_index)

        # 释放设备
        DeviceManager().release_device(device_ip)

    except Exception as e:
        # 将异常任务的设备加入监控
        DeviceManager().add_error_task_device(device_ip)
        raise

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

    # 初始化数据库连接
    DatabaseManager.init_from_config(args.config or 'config.yaml')

    # 如果是API模式，启动服务器
    if args.api:
        from rpa.api.server import start_server
        logger.info(f"启动API服务 {args.host}:{args.port}")
        start_server(args.host, args.port)
        return

    # 否则执行单个流程
    if not args.flow:
        logger.error("未指定流程配置文件")
        return



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



        # 加载全局配置
        global_config = load_config(args.config or 'config.yaml')
        # 合并全局配置和流程配置
        flow_config.update(global_config)


        # 从flow配置中获取设备信息
        device_config = flow_config.get('device', {})
        device_ids = device_config.get('ip')

        if not device_ids:
            logger.error("未指定设备IP")
            return

        try:
            device_ids = [ip.strip() for ip in device_ids.split(',') if ip.strip()]
            # 只初始化要使用的设备
            logger.info("开始初始化设备UIAutomator2环境...")
            if not setup_uiautomator2(device_ids[0]):
                logger.error("设备初始化失败")
                return
            logger.info("设备初始化完成")

            if not args.flow:
                return

            # 执行流程，传入配置对象
            logger.info(f"开始执行流程: {flow_config.get('name', '未命名流程')}")
            start_step_index = args.start_step_index if args.start_step_index is not None else 0
            main(flow_config, device_ids[0], start_step_index)
            logger.info("流程执行完成")

        except Exception as e:
            raise

    except Exception as e:
        logger.error(f"执行出错: {str(e)}")
        if args.dev:
            import traceback
            logger.error(traceback.format_exc())
        raise

if __name__ == '__main__':
    run()
