#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import logging
import yaml
from rpa.core.base_bot import BaseBot
from rpa.utils.logger import setup_logger

def parse_args():
    parser = argparse.ArgumentParser(description='RPA Framework 运行器')
    parser.add_argument('--config', '-c', required=True, help='流程配置文件路径')
    parser.add_argument('--debug', '-d', action='store_true', help='启用调试模式')
    parser.add_argument('--log', '-l', default='run.log', help='日志文件路径')
    return parser.parse_args()

def main():
    args = parse_args()
    
    # 设置日志
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logger(args.log, log_level)
    logger = logging.getLogger(__name__)
    
    try:
        # 读取配置文件
        with open(args.config, 'r', encoding='utf-8') as f:
            flow_config = yaml.safe_load(f)
            
        # 初始化机器人
        bot = BaseBot()
        
        # 执行流程
        logger.info(f"开始执行流程: {flow_config.get('name', '未命名流程')}")
        bot.run_flow(flow_config)
        logger.info("流程执行完成")
        
    except Exception as e:
        logger.error(f"执行出错: {str(e)}")
        raise

if __name__ == '__main__':
    main() 