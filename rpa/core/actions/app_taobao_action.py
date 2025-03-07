from typing import Dict, Any
from loguru import logger
import subprocess
import time
import select
from .base_action import BaseAction
from .ocr_actions import WaitAndClickOCRTextAction
from bots.taobao import Taobao


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
        time.sleep(10)


class TaobaoSearchAction(BaseAction):
    """打开淘宝搜索框并搜索进入商品"""

    def execute(self, params: Dict[str, Any]) -> None:
        pass



class TaobaoPayListAction(BaseAction):
    """淘宝选购商品支付操作动作"""
    def execute(self, params: Dict[str, Any]) -> None:
        taobao = Taobao(adb_address=self.bot.device_ip)
        taobao.params = params
        taobao.buy_goods(params)
