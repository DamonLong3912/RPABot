from .base import Base
import time
import re
import pandas as pd
import sys
import pdb
from .uiautomator_base import Base
import pdb
import random
import argparse
import logging
import os
import argparse
import retry
from lib.cli import cli
from typing import Dict, Any, List

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

class Taobao(Base):

  package_name = "com.taobao.taobao"
  app_name = "淘宝"
  app_version = "10.10.0"

  def deliver_goods(self, phone, name, address, position):
    """
    代下单,直接配送到指定地址
    """
    # 调用下单api
    log.info(f"deliver_goods: {phone}, {name}, {address}, {position}")
    url = "http://h5.cx/api/?skey=132456&function=order&mode=call&dyOrderNo=123&orderNo=321&callMethod=1"



  def use_coupon(self, goods_name = '椰子丝绒燕麦拿铁', type = 'luckin'):
    log.info("use coupon")
    self.app_start()
    # self.back_until(lambda: self.exists('消息'))
    self.click('消息')
    self.click('大白饭票')
    self.sleep(3, '等待大白饭票加载')
    eles = self.d(descriptionMatches="去领取|去查看")
    # 获取最后一个
    last_ele = eles[-1]
    last_ele.click()
    self.sleep(3, '等待领取')
    if self.exists('提取错误'):
      log.info("提取错误")
      return
    self.click('确认')
    self.click('我知道了')
    self.click('查看文本')
    self.sleep(1, '等待查看文本')
    self.click('全部复制')
    self.sleep(1, '等待复制')
    if self.exists('剪贴板信息'):
      self.click('同意')
    url = self.d.clipboard
    log.info(f"url: {url}")

    # 格式化url
    parts = url.split(",")
    if len(parts) == 2:
      url = parts[1]
    else:
      url = parts[0]

    log.info(f"formatted url: {url}")

    if url:
      self.d.open_url(url)
      self.sleep(10, '等待打开')


      # 检查是否打开浏览器
      if self.d.info.get('currentPackageName') == 'com.android.browser':
        log.info("打开浏览器成功")
      else:
        raise ValueError("打开浏览器失败")

      if not self.open_store_in_browser(type):
        raise ValueError("打开门店失败")
      self.buy_goods_in_browser(goods_name, type)
    else:
      log.info("no url")



  def open_store_in_browser(self,type):
    if type == 'starbucks':
      return self.open_starbucks_store_in_browser()
    elif type == 'luckin':
      return self.open_luckin_store_in_browser()
    elif type == 'mcdonalds':
      return self.open_mcdonalds_store_in_browser()
    elif type == 'kfc':
      return self.open_kfc_store_in_browser()
    else:
      raise ValueError("不支持的类型")


  def open_luckin_store_in_browser(self):
    """
    在浏览器中打开瑞幸门店
    """
    log.info("open luckin store in browser")
    self.click('允许') # 获取定位权限
    self.click('查找城市')
    self.d.send_keys('苏州')
    self.click('输入门店名称')
    self.d.send_keys('吴江万象汇店')


  def open_mcdonalds_store_in_browser(self):
    """
    在浏览器中打开麦当劳门店
    """
    log.info("open mcdonalds store in browser")
    self.click('允许') # 获取定位权限
    self.click('查找城市')
    self.d.send_keys('苏州')
    self.click('输入门店名称')
    self.d.send_keys('苏州万象汇店')


  def open_kfc_store_in_browser(self):
    """
    在浏览器中打开肯德基门店
    """
    log.info("open kfc store in browser")
    self.click('允许') # 获取定位权限
    self.click('查找城市')
    self.d.send_keys('苏州')
    self.click('输入门店名称')
    self.d.send_keys('苏州万象汇店')


  def open_starbucks_store_in_browser(self):
    """
    在浏览器中选择商品
    """

    location_name = '吴江万象汇'

    self.click('确定')
    self.sleep(1, '等待打开')
    self.click('请输入门店地址')
    self.d.send_keys(location_name)
    self.sleep(3, '等待输入')
    self.d.click(0.133, 0.287) # 第一个条目
    self.sleep(5, '等待选择')
    self.d.click(0.477, 0.312) #  继续选择第一个
    self.sleep(5, '等待选择')
    # 检查是否正确进入门店
    if self.exists('请仔细核对门店信息'):
      self.click('确定')
      return True
    else:
      log.info("进入门店失败")
      return False

  def buy_goods_in_browser(self, type):
    if type == 'luckin':
      self.buy_luckin_in_browser()
    elif type == 'starbucks':
      self.buy_starbucks_in_browser()
    elif type == 'mcdonalds':
      self.buy_mcdonalds_in_browser()
    elif type == 'kfc':
      self.buy_kfc_in_browser()
    else:
      raise ValueError("不支持的类型")

  def buy_starbucks_in_browser(self, good_name = '椰子丝绒燕麦拿铁'):
    """
    获取商品列表
    """
    log.info(f"goods_name: {goods_name}")
    ele = self.d(text=goods_name)
    if ele.exists():
      ele.sibling(text='选规格').click()
      self.sleep(10, '等待打开选规格')
      if self.wait_until(lambda: self.exists('添加至购物车'), timeout=20):
        # 可能需要选规格，暂时先不做
        self.click('添加至购物车')
        self.click('去结算')
        self.input_name()
      else:
        log.info("找不到添加至购物车")
    else:
      log.info("找不到商品")


  def input_name(self, name: str = '张三'):
    """
    输入商品名称
    """
    self.click('请输入取单人姓名')
    self.sleep(2, '等待输入')
    self.d.send_keys(name)
    self.sleep(3, '等待输入')


  def buy_one_goods(self, specs: List[str]):
    """
    购买一个商品
    """
    self.click('立即购买')
    log.info(f"specs: {specs}")
    for spec in specs:
      text = spec
      textMatches = None
      # 如果 spec 是 ^ 开头，则认为是正则表达式
      if spec.startswith('^'):
        textMatches = spec
        text = None
      if self.scroll_up_until(
        lambda: self.exists(text=text, textMatches=textMatches),
        max_times=3,
        scale=0.5
      ):
        if not self.click(text=text, textMatches=textMatches):
          raise ValueError(f"找不到商品规格: {spec}")
        if not self.exists('免密支付'):
          log.info("可能之前选中了，现在反而是不选中了, 重新选回来")
          if not self.click(text=text, textMatches=textMatches):
            raise ValueError(f"找不到商品规格: {spec}")
      if not self.click('免密支付'):
        raise ValueError("找不到免密支付")
      time.sleep(10)

  def buy_goods(self, params: Dict[str, Any]):
    pay_status = params.get('pay_status')
    pay_list = params.get('pay_list')
    # pay_list的格式为："中杯:原味蒸汽奶,大杯:原味蒸汽奶" 循环用:分割
    pay_list = pay_list.split(',')


    address = params.get('address')
    position = params.get('position')
    phone = params.get('phone')
    name = params.get('name')

    type = params.get('type') # luckin, mcdonals, starbucks



    log.info(f"pay_list: {pay_list}")
    for item in pay_list:
      specs = item.split(':')
      log.info(f"specs: {specs}")
      if not self.buy_one_goods(specs):
        log.info("购买失败")
        raise ValueError("购买失败")
      if not self.use_coupon(type=type):
        raise ValueError("使用优惠券失败")
      if not self.delivery_goods(address, position, phone, name):
        raise ValueError("配送失败")

  def back_until(self, interval=1, max_times=10):
      """商品主页"""
      d = self.d
      current = 1
      while True:
          if not self.exists('立即购买'):
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
      if self.d.app_current()['activity'] == "com.alibaba.wireless.security.open.middletier.fc.ui.ContainerActivity":
          return True
      else:
          return False


  def buy_luckin_in_browser(self):
    """
    在浏览器中购买瑞幸
    """
    self.click('允许') # 获取定位权限
    self.click('查找城市')
    self.d.send_keys('苏州')

    self.click('输入门店名称或地址搜索')
    self.d.send_keys('吴江万象汇店')

  def buy_kfc_in_browser(self):
    """
    在浏览器中购买肯德基
    """
    self.click('允许') # 获取定位权限
    self.click('查找城市')
    self.d.send_keys('苏州')

  def buy_mcdonalds_in_browser(self):
    """
    在浏览器中购买麦当劳
    """
    self.click('允许') # 获取定位权限
    self.click('查找城市')
    self.d.send_keys('苏州')

if __name__ == "__main__":
  bot = Taobao()
  cli(bot)
