#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import logging
import yaml
import os
from pathlib import Path
from rpa.core.base_bot import BaseBot
from rpa.utils.logger import setup_logger

def parse_args():
    parser = argparse.ArgumentParser(description='RPA Framework 运行器')
    parser.add_argument('--config', '-c', required=True, help='流程配置文件路径')
    parser.add_argument('--debug', '-d', action='store_true', help='启用调试模式')
    parser.add_argument('--dev', action='store_true', help='开发环境模式')
    parser.add_argument('--log', '-l', default='run.log', help='日志文件路径')
    return parser.parse_args()

def setup_dev_env():
    """配置开发环境"""
    # 设置项目根目录
    project_root = Path(__file__).parent
    os.environ['RPA_PROJECT_ROOT'] = str(project_root)
    
    # 设置资源目录
    os.environ['RPA_ASSETS_DIR'] = str(project_root / 'rpa' / 'assets')
    
    # 设置日志级别为DEBUG
    os.environ['RPA_LOG_LEVEL'] = 'DEBUG'
    
    # 打印环境信息
    logger = logging.getLogger(__name__)
    logger.info("开发环境配置:")
    logger.info(f"项目根目录: {os.environ['RPA_PROJECT_ROOT']}")
    logger.info(f"资源目录: {os.environ['RPA_ASSETS_DIR']}")
    logger.info(f"日志级别: {os.environ['RPA_LOG_LEVEL']}")

def main():
    args = parse_args()
    
    # 设置日志
    log_level = logging.DEBUG if args.debug or args.dev else logging.INFO
    setup_logger(args.log, log_level)
    logger = logging.getLogger(__name__)
    
    # 开发环境配置
    if args.dev:
        setup_dev_env()
        logger.info("运行在开发环境模式")
    
    try:
        # 读取配置文件
        config_path = Path(args.config)
        if not config_path.is_absolute():
            config_path = Path(os.environ.get('RPA_PROJECT_ROOT', '')) / config_path
            
        logger.info(f"加载流程配置文件: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            flow_config = yaml.safe_load(f)
            
        # 打印流程信息
        logger.info(f"流程名称: {flow_config.get('name')}")
        logger.info(f"流程版本: {flow_config.get('version')}")
        logger.info(f"流程描述: {flow_config.get('description')}")
        
        # 初始化机器人
        bot = BaseBot()
        
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