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

  def use_coupons(self, count=1):
    eles_count = eles.count
    idx = 0
    log.info(f"idx: {idx}, eles_count: {eles_count}, count: {count}")
    for ele in eles:
      if eles_count - idx <= count:
        ele.click()
        self.sleep(1, '等待领取')
        self.use_coupon()
      else:
        log.info(f"skip idx: {idx}")
      idx += 1

  def use_coupon(self):
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
    self.click('全部复制')
    if self.exists('剪贴板信息'):
      self.click('同意')
    url = self.d.clipboard
    log.info(f"url: {url}")
    if url:
      self.d.open_url(url)
      self.sleep(10, '等待打开')
      if not self.open_store_in_browser():
        raise ValueError("打开门店失败")
      self.buy_goods_in_browser()
    else:
      log.info("no url")

  def open_store_in_browser(self):
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


  def buy_goods_in_browser(self):
    """
    获取商品列表
    """
    goods_name = '椰子丝绒燕麦拿铁'
    log.info(f"goods_name: {goods_name}")
    ele = self.d(text=goods_name)
    if ele.exists():
      ele.sibling(text='选规格').click()
      self.sleep(10, '等待打开选规格')
      # 检查是否打开
      if self.exists('添加至购物车'):
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
    self.d.send_keys(name)
    self.sleep(3, '等待输入')


  def buy_one_goods(self, specs: List[str]):
    """
    购买一个商品
    """
    self.click('立即购买')
    for spec in specs:
      if not self.exists(text=spec):
        if not self.scroll_up_until(
          lambda: self.exists(text=spec),
          max_times=3
        ):
            raise ValueError(f"找不到商品规格: {spec2}")
      if not self.click(text=spec):
        raise ValueError(f"找不到商品规格: {spec}")

      if not self.click('免密支付'):
        raise ValueError("找不到免密支付")
      time.sleep(10)

  def buy_goods(self, params: Dict[str, Any]):
    pay_status = params.get('pay_status')
    pay_list = params.get('pay_list')
    # pay_list的格式为："中杯:原味蒸汽奶,大杯:原味蒸汽奶" 循环用:分割
    pay_list = pay_list.split(',')
    for item in pay_list:
      specs = item.split(':')
      self.buy_one_goods(item)

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




if __name__ == "__main__":
  bot = Taobao()
  cli(bot)
