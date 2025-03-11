from flask import Flask, request, jsonify
from pathlib import Path
import threading
from typing import Dict, Any
from rpa.utils.logger import get_logger
from rpa.utils.device_manager import DeviceManager
import traceback
import yaml
import os
import glob
from rpa.utils.db import DatabaseManager 
from run import load_config
import requests
import time
import json

app = Flask(__name__)
logger = get_logger(__name__)

# 存储正在运行的任务，包括设备IP
running_tasks: Dict[str, Dict[str, Any]] = {}

# 在文件顶部定义全局的 device_manager
device_manager = DeviceManager()

def get_config():
    """从config.yaml获取配置"""
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"读取配置文件失败: {str(e)}")
        return {}

def run_flow(flow_config: Dict[str, Any], task_id: str, device_ip: str, start_step_index: int = 0):
    """在独立线程中运行流程
    
    Args:
        flow_config: 流程配置
        task_id: 任务ID
        device_ip: 设备IP
        start_step_index: 开始执行的步骤索引
    """
    global running_tasks  # 声明使用全局的 running_tasks
    from run import setup_uiautomator2, main
    
    try:
        # # 记录变量信息到日志
        # if 'variables' in flow_config:
        #     logger.info(f"流程变量: {flow_config['variables']}")
        
        # 检查是否有已存储的任务标识
        if task_id in running_tasks:
            # 使用存储的variables参数
            flow_config['variables'] = running_tasks[task_id].get('variables', {})
            start_step_index += 1
            # 历史任务应该加一执行
            logger.info(f"恢复任务 {task_id} 的执行，从步骤 {start_step_index} 开始")
            main(flow_config, device_ip, start_step_index, task_id)
            return
        else:
            # 存储任务和variables参数
            running_tasks[task_id] = {
                'device_ip': device_ip,
                'variables': flow_config.get('variables', {})
            }
        
        # 初始化设备
        logger.info("开始初始化设备UIAutomator2环境...")
        if not setup_uiautomator2(device_ip):
            logger.error("设备初始化失败")
            device_manager.release_device(device_ip)
            return
        logger.info("设备初始化完成")
        
        
        # 执行流程
        logger.info(f"开始执行流程: {flow_config.get('name', '未命名流程')}")
        main(flow_config, device_ip, start_step_index, task_id)
        logger.info("流程执行完成")

                # 清理任务记录
        if task_id in running_tasks:
            del running_tasks[task_id]
        
    except Exception as e:
        logger.error(f"执行出错: {str(e)}")
        logger.error(traceback.format_exc())
        raise


@app.route('/api/flow/start', methods=['POST'])
def start_flow():
    """启动流程
    
    请求体:
    {
        "flow_path": "flows/test.yaml",
        "task_id": "unique_task_id",  // 可选
        "start_step_index": 0,         // 可选，默认从0开始
        "variables": {                 // 可选，流程变量
            "var1": "新手机",
            "var2": "平板电脑",
            "var3": "自定义值"
        }
    }
    """
    global running_tasks  # 声明使用全局的 running_tasks
    try:
        data = request.get_json()
        flow_path = data.get('flow_path')
        task_id = data.get('task_id', str(threading.get_ident()))
        start_step_index = data.get('start_step_index', 0)
        variables = data.get('variables', {})
        
        if not flow_path:
            return jsonify({
                "success": False,
                "message": "缺少flow_path参数"
            }), 400
            
        # 检查文件是否存在
        flow_file = Path(flow_path)
        if not flow_file.is_absolute():
            flow_file = Path(os.environ.get('RPA_PROJECT_ROOT', '')) / flow_file
            
        if not flow_file.exists():
            return jsonify({
                "success": False,
                "message": f"流程文件不存在: {flow_path}"
            }), 404
            
        # 获取设备 IP
        if task_id in running_tasks:
            device_ip = running_tasks[task_id]['device_ip']
            # 如果是恢复任务且没有传入新的variables,使用存储的variables
            if not variables:
                variables = running_tasks[task_id].get('variables', {})
        else:
            # 获取可用设备
            device_config = yaml.safe_load(open(flow_file, 'r', encoding='utf-8'))
            device_ids = device_config.get('device', {}).get('ip', [])
            if not device_ids:
                return jsonify({
                    "success": False,
                    "message": "未配置设备"
                }), 500
            
            # 获取可用设备
            device_ip = device_manager.get_available_device(device_ids)  # 传入设备ID列表
            if not device_ip:
                return jsonify({
                    "success": False,
                    "message": "没有可用的空闲设备"
                }), 500
            
        # 加载流程配置
        with open(flow_file, 'r', encoding='utf-8') as f:
            flow_config = yaml.safe_load(f)
            
        # 合并API传入的变量到流程配置中
        if variables:
            # 如果YAML中没有variables部分，先创建
            if 'variables' not in flow_config:
                flow_config['variables'] = {}
            # 合并变量，API传入的变量优先级更高
            flow_config['variables'].update(variables)
            logger.info(f"已合并API传入的变量: {variables}")
        
        # 创建新线程运行流程
        thread = threading.Thread(
            target=run_flow,
            args=(flow_config, task_id, device_ip, start_step_index),  # 传递开始步骤索引
            daemon=True
        )
        thread.start()
        
        return jsonify({
            "success": True,
            "message": "流程已启动",
            "task_id": task_id
        })
        
    except Exception as e:
        logger.error(f"启动流程失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"启动流程失败: {str(e)}"
        }), 500

@app.route('/api/flow/status/<task_id>', methods=['GET'])
def get_flow_status(task_id):
    """获取流程状态"""
    global running_tasks  # 声明使用全局的 running_tasks
    if task_id in running_tasks:
        thread = running_tasks[task_id]['thread']
        return jsonify({
            "success": True,
            "status": "running" if thread.is_alive() else "completed"
        })
    else:
        return jsonify({
            "success": True,
            "status": "not_found"
        })

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """获取设备状态"""
    global device_manager  # 声明使用全局的 device_manager
    devices = device_manager.get_all_devices()
    return jsonify({
        "success": True,
        "devices": devices  # 现在包含更多设备信息
    })

@app.route('/api/flows/upload', methods=['POST'])
def upload_flow():
    """上传新的流程配置文件"""
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "没有文件上传"}), 400

    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"success": False, "message": "未选择文件"}), 400

    if file and file.filename.endswith('.yaml'):
        # 保存文件到指定目录
        file_path = os.path.join('flows', file.filename)
        file.save(file_path)

        # 重新加载流程配置
        try:
            flow_config = yaml.safe_load(file)
            device_config = flow_config.get('device', {})
            device_ids = device_config.get('ip', [])
            device_ids = [ip.strip() for ip in device_ids.split(',') if ip.strip()]
            
            if device_ids:
                device_manager.register_devices(device_ids)  # 注册新设备
            
            return jsonify({"success": True, "message": "流程配置已上传并加载"}), 200
        except Exception as e:
            return jsonify({"success": False, "message": f"加载流程配置失败: {str(e)}"}), 500

    return jsonify({"success": False, "message": "文件格式不正确，必须为 YAML 文件"}), 400

def poll_external_api():
    """轮询外部接口获取待处理订单"""
    config = get_config()
    poller_settings = config.get('poller', {})
    
    # 定义服务提供商对应的店铺链接
    provider_url_map = {
        '星巴克': 'taobao://item.taobao.com/item.htm?id=693715128230',
        '瑞幸': 'taobao://item.taobao.com/item.htm?id=600254519991',
        '麦当劳': 'taobao://item.taobao.com/item.htm?id=727352428927'
    }

    def start_flow_with_retry(flow_data, max_retries=float('inf'), retry_interval=5):
        """启动流程并在遇到500错误时重试
        
        Args:
            flow_data: 流程数据
            max_retries: 最大重试次数，默认无限重试
            retry_interval: 重试间隔时间（秒）
        """
        retry_count = 0
        while True:
            try:
                response = requests.post(config.get('base_url','') + '/api/flow/start', json=flow_data)
                
                if response.status_code == 500:
                    retry_count += 1
                    logger.warning(f"启动流程返回500错误，这是第{retry_count}次重试")
                    time.sleep(retry_interval)
                    continue
                    
                if response.status_code == 200:
                    logger.info(f"成功启动{flow_data['variables']['service_provider']}订单处理流程: {flow_data['task_id']}")
                    return True
                else:
                    logger.error(f"启动流程失败: {response.text}")
                    return False
                    
            except Exception as e:
                logger.error(f"调用流程API时出错: {str(e)}")
                return False
    
    while poller_settings.get('auto_start', False):
        try:
            url = config.get('remote_api','') + poller_settings.get('api_url')
            if not url:
                logger.error("未配置轮询接口URL")
                return
                
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 200:
                    orders = data.get('data', [])
                    if not orders:
                        logger.info("当前没有待处理的订单")
                    else:
                        logger.info(f"获取到待处理订单")
                        
                        # 只处理第一条数据
                        order = orders[0]
                        logger.info(f"获取到待处理订单: {order.get('id')}")
                        
                        try:
                            # 获取服务提供商
                            service_provider = order.get('serviceProvider', '')
                            
                            # 获取店铺链接
                            intent_url = provider_url_map.get(service_provider)
                            
                            if not intent_url:
                                logger.error(f"未找到服务提供商 {service_provider} ")
                                continue
                                
                            flow_data = {
                                "flow_path": 'flows/taobao_pay.yaml',
                                "task_id": order.get('id'),
                                "variables": {
                                    "intent_url": intent_url,
                                    "order_id": order.get('id'),
                                    "specs": order.get('productList'),
                                    "service_provider": service_provider
                                }
                            }
                            
                            # 使用重试机制启动流程
                            start_flow_with_retry(flow_data)
                            
                        except Exception as e:
                            logger.error(f"处理订单 {order.get('orderNum')} 时出错: {str(e)}")
            else:
                logger.error(f"请求外部接口失败: {response.status_code}")
                
        except Exception as e:
            logger.error(f"轮询外部接口时出错: {str(e)}")
            logger.error(traceback.format_exc())
        
        # 重新获取配置，以便支持动态修改配置
        config = get_config()
        poller_settings = config.get('poller', {})
        # 等待下一次轮询
        time.sleep(poller_settings.get('polling_interval', 5))

def start_server(host='0.0.0.0', port=5000):
    """启动API服务器"""

    logger.info("启动轮询任务...")
    # 在单独的线程中启动轮询，不阻塞服务器启动
    polling_thread = threading.Thread(target=poll_external_api, daemon=True)
    polling_thread.start()
    logger.info("轮询任务已启动")

    # 自动获取flows和tests/flows下的yaml文件中的IP并注册设备
    flow_paths = glob.glob('flows/*.yaml') + glob.glob('tests/flows/*.yaml')
    for flow_path in flow_paths:
        try:
            with open(flow_path, 'r', encoding='utf-8') as f:
                flow_config = yaml.safe_load(f)
                device_config = flow_config.get('device', {})
                device_ids = device_config.get('ip')
                
                if device_ids:
                    device_manager.register_devices(device_ids)
        except Exception as e:
            logger.error(f"加载设备配置失败: {str(e)}")
    
    app.run(host=host, port=port)
        