from typing import Dict, Any
from loguru import logger
import subprocess
import time
import select
from .base_action import BaseAction


class TaobaoSearchAction(BaseAction):
    """打开淘宝搜索框并搜索进入商品"""
    
    def execute(self, params: Dict[str, Any]) -> None:
        search_text = params.get('search_text')
        
        if not search_text:
            raise ValueError("必须提供search_text参数")

        
        self.back_until()
        
        try:
            logger.info(f"等待搜索框出现...")
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


class TaobaoPayListAction(BaseAction):
    """淘宝选购商品支付操作动作"""
    
    def execute(self, params: Dict[str, Any]) -> None:
        pay_status = params.get('pay_status')
        pay_list = params.get('pay_list')
        #pay_list的格式为："中杯:原味蒸汽奶,大杯:原味蒸汽奶" 循环用:分割
        pay_list = pay_list.split(',')
        for item in pay_list:
            self.back_until()
            self.ui_animator(className="android.widget.TextView", text='立即购买').click()
            pay_list2 = item.split(':')
            if '星巴克' in pay_status:
                self.ui_animator(text=pay_list2[0]).click()
                self.ui_animator(text=pay_list2[1]).click()
                self.ui_animator(className="android.widget.LinearLayout", description="确认").click()
                if self.ui_animator(className="android.view.View", description="提交订单").wait(timeout=5):
                    self.ui_animator(className="android.view.View", description="提交订单").click()
                    if not self.ui_animator(resourceId="com.taobao.taobao:id/render_container").wait(timeout=20):
                        raise ValueError("疑似未支付成功")
                else:
                   raise ValueError("确认订单页面未能成功点击提交订单按钮")
                
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


class TaobaoCustomerServiceUrlPayAction(BaseAction):
    """淘宝打开客服窗口并根据链接选择商品"""
    
    def execute(self, params: Dict[str, Any]) -> None:
        self.back_until()

        if  self.ui_animator(text='客服').wait(timeout=5):
            self.ui_animator(text='客服').click()
        else:
            raise ValueError("打开客服对话框失败")
        #未测试
        if self.ui_animator( resourceId="com.taobao.taobao:id/tv_chatcontent").wait(timeout=5):
            # 获取所有匹配的元素
            elements = self.ui_animator(resourceId="com.taobao.taobao:id/tv_chatcontent").all()
            # 获取最后一个元素下的"去领取"按钮
            if elements:
                last_element = elements[-1]
                go_get_btn = last_element.child(description="去领取")
                if go_get_btn:
                    go_get_btn.click()
                else:
                    raise ValueError("未找到'去领取'按钮")
        else:
            raise ValueError("打开商品选择链接失败")
                
    def back_until(self, interval=1, max_times=10):
        """商品主页"""
        d = self.ui_animator
        current = 1
        while True:
            if not self.ui_animator(resourceId="com.taobao.taobao:id/ll_bottom_bar_content"):
                d.press("back")
                time.sleep(interval)
                current += 1
                if current > max_times:
                    logger.info("reach max times")
                    break
            else:
                break