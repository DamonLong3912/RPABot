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
  params = {}

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



  def get_coupon_url(self, goods_name = '椰子丝绒燕麦拿铁', type = 'luckin', **kwargs):
    log.info("use coupon")
    # self.app_start()
    # # self.back_until(lambda: self.exists('消息'))
    # if self.d(description='消息').wait(timeout=5):
    #   self.d(description='消息').click()
    #   if self.d(text='뉭').wait(timeout=5):
    #     time.sleep(5)
    #     if self.d(description='大白饭票').wait(timeout=5):
    #       self.d(description='大白饭票').click()
    if self.d(text='客服').wait(timeout=5):
      self.d(text='客服').click()



    # 等待输入框出现 证明进入客服界面
    if self.d(resourceId='com.taobao.taobao:id/mp_chat_input_id').wait(timeout=5):
      # 第一次先下滑一下，避免底部卡片挡住按钮
      screen_size = self.d.window_size()
      self.d.swipe(
          screen_size[0] * 0.5,  # 起点x：屏幕中间
          screen_size[1] * 0.6,  # 起点y：屏幕中间偏下
          screen_size[0] * 0.5,  # 终点x：与起点相同
          screen_size[1] * 0.4,  # 终点y：屏幕中间偏上
          duration=0.1  # 快速滑动
      )
      time.sleep(0.5)  # 等待滑动完成

      # 循环3次尝试查找元素
      for i in range(3):
          eles = self.d(descriptionMatches="去领取|去查看")
          if len(eles) > 0:
              # 找到元素则点击最后一个并退出循环
              last_ele = eles[-1]
              last_ele.click()
              break
          else:
              # 找不到则往上滑动一点
              self.d.swipe(
                  screen_size[0] * 0.5,  # 起点x：屏幕中间
                  screen_size[1] * 0.4,  # 起点y：屏幕中间偏上
                  screen_size[0] * 0.5,  # 终点x：与起点相同
                  screen_size[1] * 0.6,  # 终点y：屏幕中间偏下
                  duration=0.1  # 快速滑动
              )
              time.sleep(0.5)  # 等待滑动完成
      
    if self.exists('提取错误'):
      log.info("提取错误")
      return

    #是否有授权
    if self.d(resourceId='com.taobao.taobao.triver_taobao:id/open_auth_btn_grant',text='确认授权').wait(timeout=5):
      self.d(resourceId='com.taobao.taobao.triver_taobao:id/open_auth_btn_grant',text='确认授权').click()



    self.click('确认')
    self.click('我知道了')
    self.click('查看文本')



    if self.d(text='全部复制').wait(timeout=7):
      self.d(text='全部复制').click()
      if self.exists('剪贴板信息'):
        self.click('同意')
    url = self.d.clipboard
    # log.info(f"url: {url}")

    # 格式化url
    url = url.split("https://")[1]
    url = "https://" + url
    log.info(f"formatted url: {url}")

    if url:
      return url
    else:
      return None

    """
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
    """



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
    log.info(f"url: {url}")
    # https://db.mdlvip.cn/?secret=2490165949719441258
    if "db.mdlvip.cn" in url:
      log.info("open luckin store in browser")
      self.click('允许') # 获取定位权限
      self.sleep(1, '等待允许')
      # 继续编写购买流程
      self.d.click(113,816) # 重新选择城市
      self.sleep(3, '等待重新选择城市')
      self.click('请输入城市')
      self.sleep(1, '等待输入城市')
      breakpoint()
      self.d.send_keys(self.params.get('city'))
      self.sleep(3, '等待结果')
      self.d.click(564,626) # 点击第一个结果
      self.sleep(3, '等待选择门店')
      self.click('请输入内容')
      self.sleep(1, '等待输入内容')
      self.d.send_keys(self.params.get('shop_name'))
      self.sleep(3, '等待搜索结果')
      self.d.click(626,1143) # 点击第一个结果
      self.click('下单')
      self.sleep(1, '等待下单')
      self.click('选择')
      # ...
      self.click('确认下单')
      return False

    if "lk.cafe.paytribe.cn" in url:
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
    # else:
    log.info("不支持的url")
    raise ValueError(f"不支持店铺url: {url}")

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

    location_name = self.params.get('store_name')

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
    goods_name = kwargs.get('goods_name')
    if not goods_name:
      raise ValueError(f"找不到商品名称: {goods_name}")
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
    # if self.d( text='加入购物车').wait(timeout=5):
    #   self.d( text='加入购物车').click()
    # log.info(f"specs: {specs}")
    # time.sleep(1)

    if not self.click('可选'):
        if not self.click('已选'):
          if not self.click('请选择:'):
            raise ValueError("找不到进入购买列表的按钮")


    #大力向下滑动，屏幕向上滚动，避免前面商品已经划到底部
    # 获取屏幕尺寸
    screen_size = self.d.window_size()
    screen_width = screen_size[0]
    screen_height = screen_size[1]
  # 执行2次大力向下滑动
    for _ in range(2):
      self.d.swipe(
          screen_width * 0.5,   # 起点x：屏幕中间
          screen_height * 0.5,  # 起点y：屏幕中间
          screen_width * 0.5,   # 终点x：与起点相同
          screen_height * 0.8,  # 终点y：屏幕底部偏上位置
          duration=0.1  # 快速滑动
      )
    time.sleep(1)  # 等待页面滚动完成


    # info = self.d.app_info('com.taobao.taobao')
    # if not info:
    #     raise Exception("淘宝未安装")
    
    # app_version=info['versionName']


    
    for spec in specs:
      # text = spec
      # textMatches = None
      # # 如果 spec 是 ^ 开头，则认为是正则表达式
      # if spec.startswith('^'):
      #   textMatches = spec
      #   text = None
      # if self.scroll_up_until(
      #   lambda: self.exists(text=text, textMatches=textMatches),
      #   max_times=3,
      #   scale=0.5
      # ):
      #   if not self.click(text=text, textMatches=textMatches):
      #     raise ValueError(f"找不到商品规格: {spec}")
      #   if not self.exists('免密支付'):
      #     log.info("可能之前选中了，现在反而是不选中了, 重新选回来")
      #     if not self.click(text=text, textMatches=textMatches):
      #       raise ValueError(f"找不到商品规格: {spec}")
      # if not self.click('免密支付'):
      #   raise ValueError("找不到免密支付")

      #用元素的方法
      # 尝试3次查找和点击元素
      for i in range(5):
          if self.d(description='可选 '+spec).wait(timeout=3):
              self.d(description='可选 '+spec).click()
              break
          elif self.d(description='已选中 '+spec).wait(timeout=3):
              # 已选中则无需操作
              break
          else:
              # 向下滑动一点
              screen_size = self.d.window_size()
              self.d.swipe(
                  screen_size[0] * 0.5,  # 起点x：屏幕中间
                  screen_size[1] * 0.6,  # 起点y：屏幕中间偏下
                  screen_size[0] * 0.5,  # 终点x：与起点相同 
                  screen_size[1] * 0.4,  # 终点y：屏幕中间偏上
                  duration=0.1  # 快速滑动
              )
              time.sleep(0.5)  # 等待滑动完成

    # #选完后回返回主页，然后点击
    # self.back_until()
    # #判断是否有description中包含"已选"元素的，如果有则点击
    # if not self.click('已选:'):
    #   return False
    if self.d( text='立即购买').wait(timeout=5):
      self.d( text='立即购买').click()
    else:
      return False
    
    if self.d( description='提交订单').wait(timeout=5):
      self.d( description='提交订单').click()
    else:
      return False
      



    
    for i in range(6):
      self.sleep(2, '等待免密支付')
      if self.exists('支付成功'):
        return True
    return False


  def buy_goods(self, params: Dict[str, Any]):



    specs = params.get('specs')
    # specs的格式为："中杯::原味蒸汽奶,大杯:原味蒸汽奶" 循环用::分割
    specs = specs.split(',')


    # address = params.get('address')
    # position = params.get('position')
    # phone = params.get('phone')
    # name = params.get('name')

    type = params.get('type') # luckin, mcdonals, starbucks

    log.info(f"specs: {specs}")
    result = []
    for spec in specs:

      self.back_until()

      one_specs = spec.split('::')

      # 获取最后一个元素作为数字
      count = int(one_specs[-1])
      # 保留前count个元素
      one_specs = one_specs[:count]

      if not self.buy_one_goods(one_specs):
        log.info("购买失败")
        raise ValueError("购买失败")
      
      self.back_until()
      coupon_url = self.get_coupon_url(type=type)
      if not coupon_url:
        raise ValueError("获取点餐链接失败")
      result.append('商品:' + spec + '\n点餐链接:' + coupon_url+'\n')
      
    # log.info(f"result: {result}")
    return result
      # if not self.delivery_goods(address, position, phone, name):
      #   raise ValueError("配送失败")

  def back_until(self, interval=1, max_times=10):
      """商品主页"""
      d = self.d
      current = 1
      while True:
          if not self.d(text='立即购买') or not self.d(text='客服'):
              d.press("back")
              time.sleep(interval)
              current += 1
              if current > max_times:
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
