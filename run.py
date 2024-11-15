#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import logging
import yaml
import os
from pathlib import Path
from rpa.core.base_bot import BaseBot
from rpa.utils.logger import setup_logger, get_logger

def parse_args():
    parser = argparse.ArgumentParser(description='RPA Framework 运行器')
    parser.add_argument('--flow', '-f', required=True, help='流程配置文件路径')
    parser.add_argument('--config', default='config.yaml', help='全局配置文件路径')
    parser.add_argument('--debug', '-d', action='store_true', help='启用调试模式')
    parser.add_argument('--dev', action='store_true', help='开发环境模式')
    parser.add_argument('--log', '-l', default='run.log', help='日志文件路径')
    return parser.parse_args()

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
    dirs_to_clean = ['logs', 'debug', 'temp']
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

def main():
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
        
        # 初始化机器人，传入配置文件路径
        bot = BaseBot(config_path=args.config, debug=args.debug)
        
        # 执行流程
        logger.info(f"开始执行流程: {flow_config.get('name', '未命名流程')}")
        bot.run_flow(flow_config)
        logger.info("流程执行完成")
        
    except Exception as e:
        logger.error(f"执行出错: {str(e)}")
        if args.dev:
            # 开发模式下打印完整堆栈
            import traceback
            logger.error(traceback.format_exc())
        raise

if __name__ == '__main__':
    main() 