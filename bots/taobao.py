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
