from typing import Dict, Any
from loguru import logger
import subprocess
import time
import select
from .base_action import BaseAction
from .ocr_actions import WaitAndClickOCRTextAction


class TaobaoIntentAction(BaseAction):
    """打开淘宝并进入指定商品"""

    def execute(self, params: Dict[str, Any]) -> None:
        intent_url = params.get('intent_url')
        d = self.ui_animator
        ip = self.bot.device_ip
        cmd = f"am start -a android.intent.action.VIEW -d '{intent_url}'"
        logger.info(f"执行命令: {cmd}")
        d.shell(cmd)
        # 等待淘宝启动
        time.sleep(10)


class TaobaoSearchAction(BaseAction):
    """打开淘宝搜索框并搜索进入商品"""

    def execute(self, params: Dict[str, Any]) -> None:
        if not search_text:
            raise ValueError("必须提供search_text参数")


        self.back_until()

        try:
            logger.info(f"等待搜索框出现...")
            # com.taobao.taobao:id/home_searchedit
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
            if self.is_verification_page():
                raise RuntimeError("出现验证页面")
                break
            # if not self.ui_animator(className="android.view.View", resourceId="com.taobao.taobao:id/home_searchedit"):
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


    def is_verification_page(self):
        """判断是否是验证页面"""
        if self.ui_animator.app_current()['activity'] == "com.alibaba.wireless.security.open.middletier.fc.ui.ContainerActivity":
            return True
        else:
            return False


class TaobaoPayListAction(BaseAction):
    """淘宝选购商品支付操作动作"""

    def execute(self, params: Dict[str, Any]) -> None:
        pay_status = params.get('pay_status')
        pay_list = params.get('pay_list')
        #pay_list的格式为："中杯:原味蒸汽奶,大杯:原味蒸汽奶" 循环用:分割
        pay_list = pay_list.split(',')
        # breakpoint()
        for item in pay_list:
            self.back_until()
            self.ui_animator(className="android.widget.TextView", text='立即购买').click()
            pay_list2 = item.split(':')
            if '星巴克' in pay_status:
                WaitAndClickOCRTextAction(self.bot).execute({
                    "text": pay_list2[0],
                })
                WaitAndClickOCRTextAction(self.bot).execute({
                    "text": pay_list2[1],
                })
                breakpoint()
                # WaitAndClickOCRTextAction(self.bot).execute({
                #   "textContains": "免密支付",
                # })
                time.sleep(10)
                # 检查结果
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


class TaobaoUseCouponAction(BaseAction):
    """
    淘宝使用优惠券
    """

    def execute(self, params: Dict[str, Any]) -> None:
        # 强制关闭淘宝
        d = self.ui_animator
        d.stop_app("com.taobao.taobao")
        # 等待淘宝关闭
        d.start_app("com.taobao.taobao")
        # 这样应该进入首页
        logger.info("等待首页加载")
        time.sleep(10) # 等待首页加载
        d(text="消息").click(timeout=1)
        logger.info("点击消息")
        time.sleep(1)
        d("大白饭铺").click(timeout=1)
        # 点击优惠券
        d(text="优惠券").click(timeout=1)
        # 点击立即使用
        d(text="立即使用").click(timeout=1)
        # 点击确定
        d(text="确定").click(timeout=1)
