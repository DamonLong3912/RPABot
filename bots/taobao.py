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
from typing import Dict, Any

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

class Taobao(Base):

  package_name = "com.taobao.taobao"
  app_name = "淘宝"
  app_version = "10.10.0"

  def use_coupons(self, count=1):
    self.app_start()
    # self.back_until(lambda: self.exists('消息'))
    self.click('消息')
    self.click('大白饭票')
    self.sleep(3, '等待大白饭票加载')

    eles = self.d(descriptionMatches="去领取|去查看")
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
    else:
      log.info("no url")

  def choose_goods_in_browser(self):
    """
    在浏览器中选择商品
    """
    self.click('确定')
    self.sleep(1, '等待打开')
    self.click('请输入门店地址')
    self.d.send_keys('北京市朝阳区望京SOHO塔3')
    self.sleep(3, '等待输入')
    self.d.click(0.133, 0.287) # 第一个条目
    self.sleep(3, '等待选择')

  def buy_goods(self, params: Dict[str, Any]):
    pay_status = params.get('pay_status')
    pay_list = params.get('pay_list')
    # pay_list的格式为："中杯:原味蒸汽奶,大杯:原味蒸汽奶" 循环用:分割
    pay_list = pay_list.split(',')
    for item in pay_list:
        self.back_until(lambda: self.exists('立即购买'))
        self.click('立即购买')
        pay_list2 = item.split(':')
        if '星巴克' in pay_status:
            spec1, spec2 = pay_list2
            if not self.click(text=spec1):
              raise ValueError(f"找不到商品规格: {spec1}")

            if not self.exists(text=spec2):
              if not self.scroll_up_until(
                lambda: self.exists(text=spec2),
                max_times=3
              ):
                raise ValueError(f"找不到商品规格: {spec2}")
            if not self.click(text=spec2):
              raise ValueError(f"找不到商品规格: {spec2}")

            if not self.click('免密支付'):
              raise ValueError("找不到免密支付")
            time.sleep(10)
            # 检查结果
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
