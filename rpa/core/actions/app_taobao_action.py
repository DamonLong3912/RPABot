from typing import Dict, Any
from loguru import logger
import subprocess
import time
import select
from .base_action import BaseAction
from .ocr_actions import WaitAndClickOCRTextAction
from bots.taobao import Taobao
import requests


class TaobaoIntentAction(BaseAction):
    """打开淘宝并进入指定商品"""

    def execute(self, params: Dict[str, Any]) -> None:
        intent_url = params.get('intent_url')
        d = self.ui_animator
        ip = self.bot.device_ip
        d.app_stop('com.taobao.taobao') # 强制退出
        cmd = f"am start -a android.intent.action.VIEW -d '{intent_url}'"
        logger.info(f"执行命令: {cmd}")
        d.shell(cmd)
        # 等待淘宝启动
        if not  d( text='立即购买').wait(timeout=10):
            raise Exception("进入淘宝商店失败")


class TaobaoSearchAction(BaseAction):
    """打开淘宝搜索框并搜索进入商品"""

    def execute(self, params: Dict[str, Any]) -> None:
        pass



class TaobaoPayListAction(BaseAction):
    """淘宝选购商品支付操作动作"""
    def execute(self, params: Dict[str, Any]) -> None:
        taobao = Taobao(adb_address=self.bot.device_ip)
        taobao.params = params
        urls = taobao.buy_goods(params)
        
        if not urls:
            error_msg = "购买商品失败：未获取到优惠卷链接"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        try:
            # 订单号
            order_id = params.get('order_id')
                
            # 将urls列表转换为字符串,每个map后面加换行
            urls_str = '\n'.join(map(str, urls))
            
            # 准备上报数据
            data = {
                "orderId": order_id,
                "manualOrderText": urls_str,
                "orderStatus": 11
            }
            
            url = 'https://robot.mbmzone.com/guangqi-ai/api/rpa/putOrder'
            # url = 'http://localhost:8088/guangqi-ai/api/rpa/putOrder'
            
            # 发送POST请求上报数据
            response = requests.post(url, json=data)
            
            if response.status_code != 200:
                raise f"上报数据失败，状态码：{response.status_code}，响应：{response.text}"
            
        except Exception as e:
            error_msg = f"上报支付链接失败：{str(e)}"
            logger.error(error_msg)
            raise error_msg
