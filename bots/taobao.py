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
import requests

# 设置日志文件
log_file = "logs/taobao.log"
logging.basicConfig(level=logging.INFO, filename=log_file)

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

class Taobao(Base):

  package_name = "com.taobao.taobao"
  app_name = "淘宝"
  app_version = "10.10.0"

  def deliver_goods(
      self,
      phone,
      name,
      address,
      to_address_detail,
      ad_code,
      order_no,
      to_latitude,
      to_longitude,
      function = "order",
      mode = "calc",
      weight = 1,
      goods = [{"amount":1000,"name":"商品","qty":1}],
      goods_count = 1,
      shop_id = "2143343302_738862466",
      skey = "132456",
      callback_url = "",
      order_remark = "到门打电话",
      from_latitude = 113,
      from_longitude = 22.53,
    ):
    """
    代下单,直接配送到指定地址
    """
    # 调用下单api
    log.info(f"deliver_goods: {phone}, {name}, {address}, {to_address_detail}, {ad_code}, {shop_id}, {skey}, {callback_url}, {order_remark}, {goods_count}, {weight}, {goods}, {from_latitude}, {from_longitude}, {to_latitude}, {to_longitude}")
    base_url = "http://h5.cx/api/"
    # ?skey=132456&function=order&mode=calc&orderNo=321&callbackUrl=&shopId=2143343302_738862466&toName=测试&toPhone=17180421212&toAddress=广东深圳市白石洲&toAddressDetail=601&fromLatitude=113&fromLongitude=22.53&toLatitude=113.96788572&toLongitude=22.53978696&orderRemark=到门打电话&goodsCount=1&weight=1&goods=[{"amount":1000,"name":"商品","qty":1}]&adCode=深圳
    params = {
      "skey": skey,
      "function": function,
      "mode": mode,
      "orderNo": order_no,
      "callbackUrl": callback_url,
      "shopId": shop_id,
      "toName": name,
      "toPhone": phone,
      "toAddress": address,
      "toAddressDetail": to_address_detail,
      "fromLatitude": from_latitude,
      "fromLongitude": from_longitude,
      "toLatitude": to_latitude,
      "toLongitude": to_longitude,
      "orderRemark": order_remark,
      "goodsCount": goods_count,
      "weight": weight,
      "goods": goods,
      "adCode": ad_code
    }
    url = base_url + "?" + "&".join([f"{k}={v}" for k, v in params.items()])
    log.info(f"url: {url}")
    response = requests.get(url)
    log.info(f"response: {response.json()}")
    return response.json()



  def use_coupon(self, goods_name = '椰子丝绒燕麦拿铁', type = 'luckin', **kwargs):
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
    url = url.split("https://")[1]
    url = "https://" + url
    log.info(f"formatted url: {url}")

    if url:
      self.d.open_url(url)
      self.sleep(10, '等待打开')


      # 检查是否打开浏览器
      if self.d.info.get('currentPackageName') == 'com.android.browser':
        log.info("打开浏览器成功")
      else:
        raise ValueError("打开浏览器失败")

      if not self.open_store_in_browser(type, url=url):
        raise ValueError("打开门店失败")
      self.buy_goods_in_browser(goods_name, type, url=url)
    else:
      log.info("no url")



  def open_store_in_browser(self,type, **kwargs):
    if type == 'starbucks':
      return self.open_starbucks_store_in_browser(**kwargs)
    elif type == 'luckin':
      return self.open_luckin_store_in_browser(**kwargs)
    elif type == 'mcdonalds':
      return self.open_mcdonalds_store_in_browser(**kwargs)
    elif type == 'kfc':
      return self.open_kfc_store_in_browser(**kwargs)
    else:
      raise ValueError("不支持的类型")


  def open_luckin_store_in_browser(self, **kwargs):
    """
    在浏览器中打开瑞幸门店
    """
    url = kwargs.get('url', None)
    log.info("open luckin store in browser")
    self.click('允许') # 获取定位权限

    if self.exists('重新定位'):
      log.info("有重新定位，是在门店选择页面")
      self.d.click(109,347) # 重新选择城市
      self.sleep(3, '等待重新选择城市')

    self.click('查找城市')
    self.sleep(3, '等待查找城市')
    self.d.send_keys('苏州')
    self.sleep(3, '等待输入')
    xpath = "//android.widget.TextView[@text='苏州']"
    selector = self.d.xpath(xpath)
    selector.all()[0].click()

    self.click('输入门店名称')
    self.d.send_keys('吴江万象汇店')

    self.d.click(579,641) # 点击第一个结果
    self.sleep(3, '等待选择门店')

    # 检查是否进入成功
    if self.exists('经典饮品'):
      log.info("进入成功")
      return True
    else:
      log.info("进入失败")
      return False

  def open_mcdonalds_store_in_browser(self, **kwargs):
    """
    在浏览器中打开麦当劳门店
    """
    log.info("open mcdonalds store in browser")
    self.click('允许') # 获取定位权限
    self.click('查找城市')
    self.d.send_keys('苏州')
    self.click('输入门店名称')
    self.d.send_keys('苏州万象汇店')


  def open_kfc_store_in_browser(self, **kwargs):
    """
    在浏览器中打开肯德基门店
    """
    log.info("open kfc store in browser")
    self.click('允许') # 获取定位权限
    self.click('查找城市')
    self.d.send_keys('苏州')
    self.click('输入门店名称')
    self.d.send_keys('苏州万象汇店')


  def open_starbucks_store_in_browser(self, **kwargs):
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

  def buy_goods_in_browser(self, type, **kwargs):
    if type == 'luckin':
      self.buy_luckin_in_browser(**kwargs)
    elif type == 'starbucks':
      self.buy_starbucks_in_browser(**kwargs)
    elif type == 'mcdonalds':
      self.buy_mcdonalds_in_browser(**kwargs)
    elif type == 'kfc':
      self.buy_kfc_in_browser(**kwargs)
    else:
      raise ValueError("不支持的类型")

  def buy_starbucks_in_browser(self, **kwargs):
    """
    获取商品列表
    """
    goods_name = kwargs.get('goods_name', '椰子丝绒燕麦拿铁')
    url = kwargs.get('url', None)
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
    if not self.click('立即购买'):
      if self.click('去购买'):
        self.sleep(3, '等待去购买')
      else:
        raise ValueError("找不到立即购买或去购买")
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
    self.sleep(3, '等待免密支付')
    if self.exists('支付成功'):
      return True
    else:
      return False

  def buy_goods(self, params: Dict[str, Any]):
    log.info(f"params: {params}")
    specs = params.get('specs')
    # specs的格式为："中杯:原味蒸汽奶,大杯:原味蒸汽奶" 循环用:分割
    specs = specs.split(',')


    address = params.get('address')
    position = params.get('position')
    phone = params.get('phone')
    name = params.get('name')

    type = params.get('type') # luckin, mcdonals, starbucks

    log.info(f"specs: {specs}")
    for spec in specs:
      one_specs = spec.split(':')
      if not self.buy_one_goods(one_specs):
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


  def buy_luckin_in_browser(self, **kwargs):
    """
    在浏览器中购买瑞幸
    """
    name = kwargs.get('name', '小黄油美式')
    if self.scroll_up_until(lambda: self.exists(text=name), max_times=10, scale=0.5):
      self.click(text=name)
      self.sleep(3, '等待打开')
      if not self.click('立刻购买'):
        log.info("找不到立刻购买")
        raise ValueError("找不到立刻购买")
      if self.exists('查询失败'):
        log.info("查询失败")
        raise ValueError("查询失败")
      else:
        self.input_name()
    else:
      log.info("找不到商品")
      raise ValueError("找不到商品")

  def buy_kfc_in_browser(self, **kwargs):
    """
    在浏览器中购买肯德基
    """
    self.click('允许') # 获取定位权限
    self.click('查找城市')
    self.d.send_keys('苏州')

  def buy_mcdonalds_in_browser(self, **kwargs):
    """
    在浏览器中购买麦当劳
    """
    self.click('允许') # 获取定位权限
    self.sleep(3, '等待允许') # 重新选择城市
    self.d.click(128,845)
    self.sleep(1, '等待重新选择城市')
    self.click('请输入关键字')
    self.sleep(2, '等待输入关键字')
    self.d.send_keys('苏州')

    selector = self.d.xpath("//android.widget.TextView[@text='苏州']")
    selector.all()[0].click()
    self.sleep(1, '等待选择餐厅')


    self.click('请输入地址寻找门店')
    self.sleep(2, '等待输入地址')
    self.d.send_keys('吴江吾悦')
    self.sleep(3, '等待搜索结果')
    self.d.click(546,1078) # 点击第一个结果

    self.click('已核实门店')
    self.click('确认下单')
    # 这里应该就结束了
    return True

if __name__ == "__main__":
  bot = Taobao()
  cli(bot)
